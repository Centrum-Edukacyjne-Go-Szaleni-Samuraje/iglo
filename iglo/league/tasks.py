import hashlib
import logging
from typing import Optional

from celery import shared_task
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.mail import send_mail

from league import texts
from league.models import Game, GameAIAnalyseUpload, GameAIAnalyseUploadStatus, Player
from league.utils.aisensei import upload_sgf, AISenseiConfig, AISenseiException
from league.utils.egd import get_gor_by_pin, EGDException
from league.utils.ogs import fetch_sgf, OGSException

logger = logging.getLogger("league")


@shared_task(time_limit=20)
def game_ai_analyse_upload_task(game_id: int) -> None:
    logger.info("AI analyse upload started for game %d", game_id)
    game = Game.objects.get(id=game_id)
    if not game.sgf:
        logger.info("AI analyse upload skipped for game %d - no SGF data", game_id)
        return
    if game.ai_analyse_link:
        logger.info("AI analyse upload skipped for game %d - AI analyse already defined", game_id)
        return
    with game.sgf.open("r") as file:
        sgf_data = file.read()
    upload, created = GameAIAnalyseUpload.objects.get_or_create(
        game=game, sgf_hash=hashlib.md5(sgf_data.encode()).hexdigest()
    )
    if not created:
        if upload.status == GameAIAnalyseUploadStatus.DONE:
            logger.info("AI analyse already uploaded for game %d", game_id)
            game.ai_analyse_link = upload.result
            game.save()
            return
        elif upload.status == GameAIAnalyseUploadStatus.IN_PROGRESS:
            logger.info("AI analyse already in progress for game %d", game_id)
    try:
        result = upload_sgf(
            config=AISenseiConfig(
                auth_url=settings.AI_SENSEI["AUTH_URL"],
                service_url=settings.AI_SENSEI["SERVICE_URL"],
                email=settings.AI_SENSEI["EMAIL"],
                password=settings.AI_SENSEI["PASSWORD"],
            ),
            sgf_data=sgf_data,
        )
        upload.result = result
        upload.status = GameAIAnalyseUploadStatus.DONE
        upload.save()
        game.ai_analyse_link = result
        game.save()
        logger.info("AI analyse uploaded successfully for game %d", game_id)
    except AISenseiException as err:
        upload.error = str(err)
        upload.status = GameAIAnalyseUploadStatus.FAILED
        upload.save()
        logger.info("AI analyse upload failed for game %d - %s", game_id, str(err))


@shared_task(time_limit=10)
def game_sgf_fetch_task(game_id: int) -> None:
    logger.info("SGF fetch started for game %d", game_id)
    game = Game.objects.get(id=game_id)
    if game.external_sgf_link and not game.sgf:
        try:
            sgf_data = fetch_sgf(sgf_url=game.external_sgf_link)
            game.sgf.save(f"game-{game.id}.sgf", ContentFile(sgf_data))
            logger.info("SGF fetched successfully for game %d", game_id)
        except OGSException as err:
            logger.info("SGF fetch fail for game %d - %s", game_id, str(err))
    else:
        logger.info("SGF fetch skipped for game %d - SGF already exists", game_id)


@shared_task(time_limit=10)
def update_gor(triggering_user_email: Optional[str] = None):
    logger.info("Updating players ranks")
    players = Player.objects.filter(egd_pin__isnull=False).all()
    logger.info(f"Found {len(players)} players to update")
    for idx, player in enumerate(players, start=1):
        try:
            player.rank = get_gor_by_pin(player.egd_pin)
            player.save()
            logger.info(f"{idx}/{len(players)} Updated {player.nick} [{player.egd_pin}] ")
        except EGDException as err:
            logger.info(f"{idx}/{len(players)} Failed to update {player.nick} [{player.egd_pin}] rank - {err}")
    if triggering_user_email:
        send_mail(
            subject=texts.UPDATE_GOR_MAIL_SUBJECT,
            message=texts.UPDATE_GOR_MAIL_CONTENT,
            from_email=None,
            recipient_list=[triggering_user_email]
        )
