from django.core.management import BaseCommand

from league.tasks import update_gor_task


class Command(BaseCommand):
    help = "update gor"

    def handle(self, *args, **options):
        update_gor_task()
