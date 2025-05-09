import datetime
import json

from django.core.management.base import BaseCommand

from league.models import (
    Season,
    Group,
    Player,
    Game,
    GameServer,
    Member,
    Round,
    SeasonState,
    WinType,
    GroupType,
)

PARING_SYSTEM_6 = {
    frozenset({1, 6}): 1,
    frozenset({2, 5}): 1,
    frozenset({3, 4}): 1,
    frozenset({1, 5}): 2,
    frozenset({2, 4}): 2,
    frozenset({3, 6}): 2,
    frozenset({1, 4}): 3,
    frozenset({2, 3}): 3,
    frozenset({5, 6}): 3,
    frozenset({1, 3}): 4,
    frozenset({2, 6}): 4,
    frozenset({4, 5}): 4,
    frozenset({1, 2}): 5,
    frozenset({3, 5}): 5,
    frozenset({4, 6}): 5,
}
PARING_SYSTEM_8 = {
    frozenset({1, 8}): 1,
    frozenset({2, 7}): 1,
    frozenset({3, 6}): 1,
    frozenset({4, 5}): 1,
    frozenset({1, 7}): 2,
    frozenset({2, 8}): 2,
    frozenset({3, 5}): 2,
    frozenset({4, 6}): 2,
    frozenset({1, 6}): 3,
    frozenset({2, 5}): 3,
    frozenset({3, 8}): 3,
    frozenset({4, 7}): 3,
    frozenset({1, 5}): 4,
    frozenset({2, 6}): 4,
    frozenset({3, 7}): 4,
    frozenset({4, 8}): 4,
    frozenset({1, 4}): 5,
    frozenset({2, 3}): 5,
    frozenset({5, 8}): 5,
    frozenset({6, 7}): 5,
    frozenset({1, 3}): 6,
    frozenset({2, 4}): 6,
    frozenset({5, 7}): 6,
    frozenset({6, 8}): 6,
    frozenset({1, 2}): 7,
    frozenset({3, 4}): 7,
    frozenset({5, 6}): 7,
    frozenset({7, 8}): 7,
}


class Command(BaseCommand):
    help = "Load historical seasons"

    def add_arguments(self, parser):
        parser.add_argument("seasons_file", type=str)

    def handle(self, *args, **options):
        loaded_seasons = 0
        with open(options["seasons_file"], "r") as f:
            data = json.load(f)
            for season_number, season_data in enumerate(reversed(data), start=1):
                start_date = datetime.datetime.fromtimestamp(
                    season_data["startDate"] / 1000
                ).date()
                end_date = datetime.datetime.fromtimestamp(
                    season_data["endDate"] / 1000
                ).date()
                if Season.objects.filter(
                    start_date=start_date, end_date=end_date
                ).exists():
                    continue
                loaded_seasons += 1
                is_last_season = season_number == len(data)
                season = Season.objects.create(
                    number=season_number,
                    start_date=start_date,
                    end_date=end_date,
                    promotion_count=2,
                    players_per_group=len(season_data["tables"][0]["players"]),
                    state=SeasonState.FINISHED,
                )
                for group_data in season_data["tables"]:
                    group_type = GroupType.MCMAHON if group_data.get("type") == "MCMAHON" else GroupType.ROUND_ROBIN
                    group_name = group_data["name"][-1]
                    group = Group.objects.create(
                        name=group_name,
                        season=season,
                        type=group_type,
                    )
                    players = []
                    for player_order, player_name in enumerate(
                        group_data["players"], start=1
                    ):
                        if not player_name:
                            players.append(None)
                            continue
                        try:
                            player = Player.objects.get(nick__iexact=player_name)
                            player.auto_join = is_last_season
                            player.save()
                        except Player.DoesNotExist:
                            player = Player.objects.create(
                                nick=player_name,
                                kgs_username=player_name,
                                auto_join=is_last_season,
                            )
                        member = Member.objects.create(
                            player=player,
                            group=group,
                            order=player_order,
                            rank=None,
                            egd_approval=player.egd_approval,  # Copy EGD approval from player
                        )
                        players.append(member)
                    if group_type == GroupType.MCMAHON:
                        for number, round_data in enumerate(group_data["rounds"], start=1):
                            round = Round.objects.create(
                                group=group,
                                number=number,
                            )
                            for game_data in round_data["games"]:
                                Game.objects.create(
                                    round=round,
                                    group=group,
                                    black=group.members.get(player__nick=game_data["black"]),
                                    white=group.members.get(player__nick=game_data["white"]),
                                    winner=group.members.get(player__nick=game_data["winner"]) if game_data["winner"] else None,
                                    win_type=WinType.POINTS if game_data["winner"] else WinType.NOT_PLAYED,
                                )
                    else:
                        paring_system = (
                            PARING_SYSTEM_6
                            if len(group_data["players"]) == 6
                            else PARING_SYSTEM_8
                        )
                        rounds = [
                            Round.objects.create(
                                group=group,
                                number=number,
                            )
                            for number in range(1, len(group_data["players"]))
                        ]
                        for player_index, result_row in enumerate(group_data["results"]):
                            for other_player_index, result in enumerate(result_row):
                                if (
                                    player_index <= other_player_index
                                    or not players[player_index]
                                    or not players[other_player_index]
                                ):
                                    continue
                                Game.objects.create(
                                    group=group,
                                    round=rounds[
                                        paring_system[
                                            frozenset(
                                                {player_index + 1, other_player_index + 1}
                                            )
                                        ]
                                        - 1
                                    ],
                                    black=players[player_index],
                                    white=players[other_player_index],
                                    winner=players[player_index]
                                    if result == 1
                                    else players[other_player_index],
                                    server=GameServer.KGS,
                                    win_type=WinType.POINTS,
                                    date=datetime.datetime.combine(
                                        season.start_date, datetime.datetime.min.time()
                                    ),
                                    link=None,
                                )

        self.stdout.write(
            self.style.SUCCESS(f"Successfully loaded {loaded_seasons} seasons")
        )
