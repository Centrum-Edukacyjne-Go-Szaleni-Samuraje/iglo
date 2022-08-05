import datetime

from celery import chain
from django.dispatch import receiver

from league.models import game_rescheduled, Game, game_result_reported, game_review_submitted
from league.tasks import (
    send_game_rescheduled_notification_task,
    game_ai_analyse_upload_task,
    game_sgf_fetch_task,
    send_game_review_submitted_task,
    send_game_result_reported_task,
)


@receiver(signal=game_rescheduled, sender=Game)
def game_rescheduled_handler(game: Game, old_date: datetime.datetime, **kwargs) -> None:
    send_game_rescheduled_notification_task.delay(game_id=game.id, old_date=old_date)


@receiver(signal=game_result_reported, sender=Game)
def game_result_reported_handler(game: Game, **kwargs):
    chain(
        game_sgf_fetch_task.si(game_id=game.id),
        game_ai_analyse_upload_task.si(game_id=game.id),
        send_game_result_reported_task.si(game_id=game.id),
    )


@receiver(signal=game_review_submitted, sender=Game)
def game_review_submitted_handler(game: Game, **kwargs):
    send_game_review_submitted_task.delay(game_id=game.id)
