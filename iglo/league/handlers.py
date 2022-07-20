import datetime

from django.dispatch import receiver

from league.models import game_rescheduled, Game
from league.tasks import send_game_rescheduled_notification


@receiver(game_rescheduled, sender=Game)
def game_rescheduled_handler(game: Game, old_date: datetime.datetime, **kwargs) -> None:
    send_game_rescheduled_notification.delay(game_id=game.id, old_date=old_date)

