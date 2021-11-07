import csv
from pathlib import Path

from django.contrib.auth.hashers import make_password
from django.core.management import BaseCommand, CommandParser, CommandError

from accounts.models import User
from league.models import Player


class Command(BaseCommand):
    help = 'Fills DB with users and rankings'

    def add_arguments(self, parser: CommandParser):
        parser.add_argument('csv_file', type=Path, help='Path to csv file')

    def handle(self, *args, **options):
        file_path = options['csv_file']

        if not file_path.is_file():
            raise CommandError(f'File {file_path} not found')

        players = self.load_csv(file_path)
        self.fill_db(players)

    @staticmethod
    def load_csv(file_path):
        with file_path.open(encoding='utf8') as csv_file:
            reader = csv.DictReader(csv_file, fieldnames=('full_name', 'email', 'nick', 'rank', 'group'))
            content = list(reader)
            return content[1:]  # omit header

    @staticmethod
    def fill_db(players):
        for player_info in players:
            print(player_info)
            user, _ = User.objects.get_or_create(
                email__iexact=player_info['email'],
                defaults={
                    'email': player_info['email'],
                    'password': make_password(None)
                })
            Player.objects.update_or_create(
                nick__iexact=player_info['nick'],
                defaults={
                    'nick': player_info['nick'],
                    'user': user,
                    'rank': player_info['rank'] or 1200
                }
            )
