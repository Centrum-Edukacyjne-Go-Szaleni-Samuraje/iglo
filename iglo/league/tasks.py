import datetime
import hashlib
import logging
import time
from typing import Optional, Dict, List, Tuple, Any, Callable

from celery import shared_task
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from requests.exceptions import HTTPError

from league import texts
from league.models import Game, GameAIAnalyseUpload, GameAIAnalyseUploadStatus, Player
from league.utils.aisensei import upload_sgf, AISenseiConfig, AISenseiException
from league.utils.egd import get_gor_by_pin, EGDException
from league.utils.ogs import fetch_sgf, OGSException, get_player_data
from utils.emails import send_email
from league import igor

logger = logging.getLogger("league")

# Common retry logic for API rate limits
def retry_on_rate_limit(func: Callable, *args, **kwargs) -> Tuple[bool, Any, str]:
    """
    Execute a function with exponential backoff retry on rate limit (HTTP 429).
    
    Args:
        func: The function to execute
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        Tuple of (success: bool, result: Any, error_message: str)
    """
    retry_delays = [5, 10, 20, 40]  # Seconds to wait between retries
    last_error = None
    
    for attempt, delay in enumerate(retry_delays + [0]):  # +[0] for one more attempt after last delay
        try:
            result = func(*args, **kwargs)
            return True, result, ""
        except (HTTPError, OGSException, EGDException) as err:
            last_error = err
            error_str = str(err)
            
            # Check if it's a rate limit error (HTTP 429)
            if "429" in error_str or "Too Many Requests" in error_str:
                if attempt < len(retry_delays):  # If we have retries left
                    logger.info(f"Rate limited. Retrying in {delay} seconds...")
                    time.sleep(delay)
                    continue
            
            # If it's not a rate limit error or we're out of retries, stop trying
            return False, None, str(err)
    
    # This should never happen, but just in case
    return False, None, str(last_error) if last_error else "Unknown error"

# Common function to generate error report
def format_error_report(failed_updates: List[Dict]) -> str:
    """
    Format a list of failed updates into a readable report.
    
    Args:
        failed_updates: List of dictionaries with 'name', 'id', and 'error' keys
        
    Returns:
        Formatted error report as string
    """
    if not failed_updates:
        return "All players were updated successfully."
    
    report = "The following players could not be updated:\n\n"
    
    # Group errors by type
    errors_by_type = {}
    for item in failed_updates:
        error = item['error']
        if error not in errors_by_type:
            errors_by_type[error] = []
        errors_by_type[error].append(f"{item['name']} [{item['id']}]")
    
    # Format the report
    for error, players in errors_by_type.items():
        report += f"Error: {error}\n"
        for player in players:
            report += f"- {player}\n"
        report += "\n"
    
    return report


@shared_task(time_limit=20)
def game_ai_analyse_upload_task(game_id: int) -> None:
    if not settings.ENABLE_AI_ANALYSE_UPLOAD:
        logger.info("AI analyse upload skipped for game %d - this feature is disabled", game_id)
        return
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
        game=game,
        sgf_hash=hashlib.md5(sgf_data.encode()).hexdigest(),
        defaults={
            "status": GameAIAnalyseUploadStatus.IN_PROGRESS,
        },
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
            tags=[f"IGLO - Grupa {game.group.name}"],
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


@shared_task(time_limit=1200)  # Increased time limit to allow for retries
def update_gor(triggering_user_email: Optional[str] = None):
    logger.info("Updating players ranks from EGD")
    players = Player.objects.filter(egd_pin__isnull=False).all()
    total_players = len(players)
    logger.info(f"Found {total_players} players to update")
    
    # Track successes and failures for reporting
    updated_count = 0
    failed_updates = []
    
    # Update player ranks from EGD
    for idx, player in enumerate(players, start=1):
        # Wrap the EGD API call with retry logic
        def fetch_gor():
            return get_gor_by_pin(player.egd_pin)
        
        success, result, error_message = retry_on_rate_limit(fetch_gor)
        
        if success:
            # Update was successful
            player.rank = result
            player.save()
            updated_count += 1
            logger.info(f"{idx}/{total_players} Updated {player.nick} [{player.egd_pin}] EGD rank: {result}")
        else:
            # Update failed
            failed_updates.append({
                'name': player.nick,
                'id': player.egd_pin,
                'error': error_message
            })
            logger.info(f"{idx}/{total_players} Failed to update {player.nick} [{player.egd_pin}] EGD rank - {error_message}")
    
    # Generate report
    success_message = f"{updated_count} out of {total_players} players successfully updated."
    error_report = format_error_report(failed_updates)
    full_report = f"{success_message}\n\n{error_report}"
    
    logger.info(f"EGD update completed. {success_message}")
    
    # Send notification email if requested
    if triggering_user_email and triggering_user_email.strip():
        send_mail(
            subject=texts.UPDATE_GOR_MAIL_SUBJECT,
            message=f"{texts.UPDATE_GOR_MAIL_CONTENT}\n\n{full_report}",
            from_email=None,
            recipient_list=[triggering_user_email],
        )


@shared_task(time_limit=1200)
def update_ogs_data(triggering_user_email: Optional[str] = None):
    """Update OGS ratings and IDs for all players."""
    # Update OGS ratings and IDs for all players
    logger.info("Updating players data from OGS")
    ogs_players = Player.objects.filter(ogs_username__isnull=False).exclude(ogs_username='').all()
    total_players = len(ogs_players)
    logger.info(f"Found {total_players} players with OGS usernames to update")
    
    # Track successes and failures for reporting
    updated_count = 0
    failed_updates = []
    
    for idx, player in enumerate(ogs_players, start=1):
        # Wrap the OGS API call with retry logic
        def fetch_ogs_data():
            return get_player_data(player.ogs_username)
        
        success, player_data, error_message = retry_on_rate_limit(fetch_ogs_data)
        
        if success:
            # Update was successful
            player.ogs_id = player_data['id']
            player.ogs_rating = player_data['rating']
            player.ogs_deviation = player_data['deviation']
            player.save()
            updated_count += 1
            logger.info(f"{idx}/{total_players} Updated {player.nick} [{player.ogs_username}] OGS data: ID={player.ogs_id}, rating={player.ogs_rating}±{player.ogs_deviation}")
        else:
            # Update failed
            failed_updates.append({
                'name': player.nick,
                'id': player.ogs_username,
                'error': error_message
            })
            logger.info(f"{idx}/{total_players} Failed to update {player.nick} [{player.ogs_username}] OGS data - {error_message}")
    
    # Generate report
    success_message = f"{updated_count} out of {total_players} players successfully updated."
    error_report = format_error_report(failed_updates)
    full_report = f"{success_message}\n\n{error_report}"
    
    logger.info(f"OGS update completed. {success_message}")
    
    # Send notification email if requested
    if triggering_user_email and triggering_user_email.strip():
        send_mail(
            subject=texts.UPDATE_OGS_MAIL_SUBJECT,
            message=f"{texts.UPDATE_OGS_MAIL_CONTENT}\n\n{full_report}",
            from_email=None,
            recipient_list=[triggering_user_email],
        )

@shared_task(time_limit=1200)
def recalculate_igor():
    logger.info("Recalculating IGoR")
    igor.recalculate_igor()
    logger.info("Recalculating IGoR: success")

def emails(game):
    return [player.user.email for player in [game.white.player, game.black.player] if player.user]

def send_game_email(path, to, game):
    send_email(
        subject_template=path+"/subject.txt",
        body_template=path+"/body.html",
        to=to,
        context={"game": game},
        reply_to=[settings.REPLY_TO_EMAIL]
    )

@shared_task()
def send_upcoming_games_reminder():
    if not settings.ENABLE_UPCOMING_GAMES_REMINDER:
        logger.info("Send upcoming games reminder skipped - this feature is disabled")
        return
    games = Game.objects.get_immediate_games()
    logger.info("Sending %d upcoming games reminders", games.count())
    for game in games:
        game.upcoming_reminder_sent = datetime.datetime.now()
        game.save()
        send_game_email("league/emails/upcoming_game_reminder", emails(game), game)

@shared_task()
def send_delayed_games_reminder():
    if not settings.ENABLE_DELAYED_GAMES_REMINDER:
        logger.info("Send delayed games reminder skipped - this feature is disabled")
        return
    games = Game.objects.get_delayed_games()
    logger.info("Sending %d delayed games reminders", games.count())
    for game in games:
        game.delayed_reminder_sent = datetime.datetime.now()
        game.save()
        send_game_email("league/emails/delayed_game_reminder", emails(game), game)
