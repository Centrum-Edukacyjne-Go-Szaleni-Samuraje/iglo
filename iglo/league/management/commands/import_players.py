import csv
from itertools import islice
from pathlib import Path

from django.contrib.auth.hashers import make_password
from django.core.management import BaseCommand, CommandParser, CommandError

from accounts.models import User
from league.models import Player, Member, Season


class Command(BaseCommand):
    help = "Fills DB with users and rankings"

    def add_arguments(self, parser: CommandParser):
        parser.add_argument("csv_file", type=Path, help="Path to csv file")

    def handle(self, *args, **options):
        file_path = options["csv_file"]

        if not file_path.is_file():
            raise CommandError(f"File {file_path} not found")

        with file_path.open(encoding="utf8") as csv_file:
            reader = csv.DictReader(
                csv_file, fieldnames=("full_name", "email", "nick", "rank", "group")
            )

            for player_info in islice(reader, 1, None):
                print(player_info)
                try:
                    first_name, last_name = player_info["full_name"].split(maxsplit=1)
                except ValueError:
                    first_name, last_name = player_info["full_name"], ""

                user, _ = User.objects.get_or_create(
                    email__iexact=player_info["email"],
                    defaults={
                        "email": player_info["email"],
                        "password": make_password(None),
                    },
                )
                rank = player_info["rank"] or 100
                last_season = Season.objects.latest("number")
                player, _ = Player.objects.update_or_create(
                    nick__iexact=player_info["nick"],
                    defaults={
                        "nick": player_info["nick"],
                        "first_name": first_name,
                        "last_name": last_name,
                        "user": user,
                        "rank": rank,
                        "auto_join": Member.objects.filter(
                            group__season=last_season,
                            player__nick__iexact=player_info["nick"],
                        ).exists(),
                    },
                )
                Member.objects.filter(player=player).update(rank=rank)
