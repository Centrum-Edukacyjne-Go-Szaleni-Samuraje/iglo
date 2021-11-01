import datetime
import pickle
import re
from dataclasses import dataclass
from typing import Optional

import requests
from bs4 import BeautifulSoup
from django.core.files.base import ContentFile
from django.core.management import BaseCommand

from league.models import Game, GameServer

KGS_ARCHIVE_URL = "https://www.gokgs.com/gameArchives.jsp"
CACHE_DB = "kgs_cache.db"


@dataclass(frozen=True)
class KGSPlayer:
    name: str
    rank: Optional[str]


@dataclass()
class KGSGame:
    link: Optional[str]
    sgf: Optional[str]
    white: KGSPlayer
    black: KGSPlayer
    config: str
    date: datetime.datetime
    type: str
    result: str

    @property
    def winner(self) -> KGSPlayer:
        return self.white if self.result[0] == "W" else self.black

    @property
    def is_league(self) -> bool:
        return "iglo" in self.sgf.lower() if self.sgf else False


def get_months(start_date: datetime.date, end_date: datetime.date) -> list[(int, int)]:
    to_month = lambda date: (date.year, date.month)
    months = []
    current_month = to_month(start_date)
    while current_month <= to_month(end_date):
        months.append(current_month)
        current_month = (
            current_month[0] + int(current_month[1] / 12),
            ((current_month[1] % 12) + 1),
        )
    return months


class Command(BaseCommand):
    help = "Fill details for KGS games"

    def handle(self, *args, **options):
        games_query = Game.objects.filter(server=GameServer.KGS, link=None)
        games_count = games_query.count()
        print(f"Games to update: {games_count}")
        games_updated = 0
        for game in games_query:
            first_player_name = game.black.player.nick
            kgs_games = []
            for year, month in get_months(
                game.group.season.start_date, game.group.season.end_date
            ):
                kgs_games.extend(
                    self._get_games(user=first_player_name, year=year, month=month)
                )
            print(
                f"- B: {game.black.player.nick} vs W: {game.white.player.nick} - {game.date} - {game.result}"
            )
            for kgs_game in kgs_games:
                if (
                    kgs_game.is_league
                    and game.group.season.start_date
                    <= kgs_game.date.date()
                    <= game.group.season.end_date
                    and kgs_game.winner.name.lower() == game.winner.player.nick.lower()
                    and {kgs_game.black.name.lower(), kgs_game.white.name.lower()}
                    == {game.black.player.nick.lower(), game.white.player.nick.lower()}
                ):
                    name_to_player = {
                        game.white.player.nick.lower(): game.white,
                        game.black.player.nick.lower(): game.black,
                    }
                    game.black = name_to_player[kgs_game.black.name.lower()]
                    game.white = name_to_player[kgs_game.white.name.lower()]
                    game.black.save()
                    game.white.save()
                    game.link = kgs_game.link
                    game.date = kgs_game.date
                    # TODO: parse result
                    # game.result = kgs_game.result
                    game.sgf.save(f"game-{game.id}.sgf", ContentFile(kgs_game.sgf))
                    game.save()
                    print("  > updated")
                    games_updated += 1
                    break
            else:
                print("  > not found")
        print(f"Updated games: {games_updated}/{games_count}")

    def _get_games(self, user: str, year: int, month: int) -> list[KGSGame]:
        try:
            with open(CACHE_DB, "rb") as f:
                cache = pickle.load(f)
        except FileNotFoundError:
            cache = {}
        cache_key = (user, year, month)
        try:
            return cache[cache_key]
        except KeyError:
            response = requests.get(
                url=KGS_ARCHIVE_URL,
                params={
                    "user": user,
                    "year": year,
                    "month": month,
                },
            )
            bs = BeautifulSoup(response.content, "html.parser")
            results = []
            for tr in bs.table.find_all("tr")[1:]:
                if len(tr.find_all("td")) != 7:
                    continue
                link, white, black, config, date, type, result = tr.find_all("td")
                player_pattern = "(\w+) \[([\w\-\?]+)\]"
                white_name, white_rank = re.match(player_pattern, white.text).groups()
                black_name, black_rank = re.match(player_pattern, black.text).groups()
                link = link.a["href"] if link.text == "Yes" else None
                if link:
                    sgf_response = requests.get(url=link)
                    sgf_content = sgf_response.content.decode()
                else:
                    sgf_content = None
                results.append(
                    KGSGame(
                        link=link,
                        white=KGSPlayer(
                            name=white_name,
                            rank=white_rank if white_rank not in ["-", "?"] else None,
                        ),
                        black=KGSPlayer(
                            name=black_name,
                            rank=black_rank if black_rank not in ["-", "?"] else None,
                        ),
                        config=config.text,
                        date=datetime.datetime.strptime(date.text, "%m/%d/%y %I:%M %p"),
                        type=type.text,
                        result=result.text,
                        sgf=sgf_content,
                    )
                )
            cache[cache_key] = results
            with open(CACHE_DB, "wb") as f:
                pickle.dump(cache, f)
            return results
