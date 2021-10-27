import datetime
import json

from django.core.management.base import BaseCommand

from league.models import Season, Group, Player, Game, GameServer, Member, Account, Round, SeasonState

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
        with open(options["seasons_file"], "r") as f:
            data = json.load(f)
            for season_number, season_data in enumerate(reversed(data), start=1):
                start_date = datetime.datetime.fromtimestamp(
                    season_data["startDate"] / 1000
                ).date()
                end_date = datetime.datetime.fromtimestamp(
                    season_data["endDate"] / 1000
                ).date()
                season = Season.objects.create(
                    number=season_number,
                    start_date=start_date,
                    end_date=end_date,
                    promotion_count=2,
                    players_per_group=len(season_data["tables"][0]["players"]),
                    state=SeasonState.READY.value,
                )
                for group_data in season_data["tables"]:
                    group_name = group_data["name"][-1]
                    group = Group.objects.create(
                        name=group_name,
                        season=season,
                    )
                    rounds = [
                        Round.objects.create(
                            group=group,
                            number=number,
                        ) for number in range(1, len(group_data["players"]))
                    ]
                    players = []
                    for player_order, player_name in enumerate(group_data["players"], start=1):
                        player, _ = Player.objects.update_or_create(nick=player_name)
                        account, _ = Account.objects.update_or_create(
                            player=player, name=player_name, server=GameServer.KGS
                        )
                        member = Member.objects.create(
                            player=player,
                            group=group,
                            order=player_order,
                            rank=None,
                        )
                        players.append(member)
                    paring_system = PARING_SYSTEM_6 if len(group_data["players"]) == 6 else PARING_SYSTEM_8
                    for player_index, result_row in enumerate(group_data["results"]):
                        for other_player_index, result in enumerate(result_row):
                            if player_index <= other_player_index:
                                continue
                            Game.objects.create(
                                group=group,
                                round=rounds[paring_system[frozenset({player_index + 1, other_player_index + 1})] - 1],
                                black=players[player_index],
                                white=players[other_player_index],
                                result="B" if result == 1 else "W",
                                server=GameServer.KGS,
                                date=datetime.datetime.combine(
                                    season.start_date, datetime.datetime.min.time()
                                ),
                                link=None,
                            )

        self.stdout.write(
            self.style.SUCCESS(f"Successfully loaded {len(data)} seasons")
        )
