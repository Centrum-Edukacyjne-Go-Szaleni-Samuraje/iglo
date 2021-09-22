import json
import datetime

from django.core.management.base import BaseCommand, CommandError

from league.models import Season, Group, Player, Game


class Command(BaseCommand):
    help = 'Load historical seasons'

    def add_arguments(self, parser):
        parser.add_argument('seasons_file', type=str)

    def handle(self, *args, **options):
        with open(options['seasons_file'], 'r') as f:
            data = json.load(f)
            for season_data in reversed(data):
                start_date = datetime.datetime.fromtimestamp(season_data["startDate"] / 1000).date()
                end_date = datetime.datetime.fromtimestamp(season_data["endDate"] / 1000).date()
                season = Season.objects.create(
                    start_date=start_date,
                    end_date=end_date,
                )
                for group_data in season_data["tables"]:
                    group_name = group_data["name"][-1]
                    group = Group.objects.create(
                        name=group_name,
                        season=season,
                    )
                    players = []
                    for player_name in group_data["players"]:
                        players.append(Player.objects.create(
                            name=player_name,
                            group=group,
                        ))
                    for player_index, result_row in enumerate(group_data["results"]):
                        for other_player_index, result in enumerate(result_row):
                            if player_index <= other_player_index:
                                continue
                            Game.objects.create(
                                group=group,
                                black=players[player_index],
                                white=players[other_player_index],
                                winner=players[player_index] if result == 1 else players[other_player_index]
                            )

        self.stdout.write(self.style.SUCCESS(f'Successfully loaded {len(data)} seasons'))
