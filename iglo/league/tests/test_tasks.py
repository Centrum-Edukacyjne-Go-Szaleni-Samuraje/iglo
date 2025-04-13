import datetime
from unittest import mock

from django.core import mail
from django.test import TestCase, override_settings

from league.models import GameAIAnalyseUploadStatus, SeasonState
from league.tasks import game_ai_analyse_upload_task, send_delayed_games_reminder, send_upcoming_games_reminder
from league.tests.factories import GameFactory, SeasonFactory
from league.utils.aisensei import AISenseiException


@override_settings(ENABLE_AI_ANALYSE_UPLOAD=True)
class GameAIAnalyseUploadTaskTestCase(TestCase):

    def test_task_succeed(self):
        game = GameFactory(sgf__data="data", group__name="A")

        with mock.patch("league.tasks.upload_sgf") as upload_sgf_mock:
            upload_sgf_mock.return_value = "https://ai.com/123"
            game_ai_analyse_upload_task(game_id=game.id)

        upload_sgf_mock.assert_called_once_with(config=mock.ANY, sgf_data="data", tags=["IGLO - Grupa A"])
        game.refresh_from_db()
        self.assertEqual(game.ai_analyse_link, "https://ai.com/123")
        upload = game.ai_analyse_uploads.get()
        self.assertEqual(upload.status, GameAIAnalyseUploadStatus.DONE)
        self.assertEqual(upload.result, "https://ai.com/123")

    def test_task_failed(self):
        game = GameFactory(sgf__data="data", group__name="A")

        with mock.patch("league.tasks.upload_sgf") as upload_sgf_mock:
            upload_sgf_mock.side_effect = AISenseiException("error message")
            game_ai_analyse_upload_task(game_id=game.id)

        upload_sgf_mock.assert_called_once_with(config=mock.ANY, sgf_data="data", tags=["IGLO - Grupa A"])
        game.refresh_from_db()
        self.assertIsNone(game.ai_analyse_link)
        upload = game.ai_analyse_uploads.get()
        self.assertEqual(upload.status, GameAIAnalyseUploadStatus.FAILED)
        self.assertIsNone(upload.result)
        self.assertEqual(upload.error, "error message")


@override_settings(ENABLE_DELAYED_GAMES_REMINDER=True)
class SendDelayedGamesRemindersTask(TestCase):

    def test_task(self):
        now = datetime.datetime.now()
        season = SeasonFactory(state=SeasonState.IN_PROGRESS)
        game = GameFactory(date=now - datetime.timedelta(days=1), win_type=None, group__season=season)

        send_delayed_games_reminder()

        game.refresh_from_db()
        self.assertIsNotNone(game.delayed_reminder_sent)
        self.assertEqual(len(mail.outbox), 1)
        
@override_settings(ENABLE_UPCOMING_GAMES_REMINDER=True)
class SendUpcomingGamesRemindersTask(TestCase):

    def test_task(self):
        now = datetime.datetime.now()
        season = SeasonFactory(state=SeasonState.IN_PROGRESS)
        game = GameFactory(date=now + datetime.timedelta(days=1), win_type=None, group__season=season)

        send_upcoming_games_reminder()

        game.refresh_from_db()
        self.assertIsNotNone(game.upcoming_reminder_sent)
        self.assertEqual(len(mail.outbox), 1)
        
        
@override_settings(ENABLE_AUTO_MARK_UNPLAYED_GAMES=True)
class MarkOverdueGamesAsUnplayedTask(TestCase):

    def test_task(self):
        now = datetime.datetime.now()
        season = SeasonFactory(state=SeasonState.IN_PROGRESS)
        
        # Create games with different dates
        
        # Game 1: Scheduled 8 days ago (should be marked as unplayed)
        overdue_date = now - datetime.timedelta(days=8)
        overdue_game = GameFactory(
            group__season=season,
            date=overdue_date,
            win_type=None
        )
        
        # Game 2: Scheduled 6 days ago (should NOT be marked as unplayed)
        recent_date = now - datetime.timedelta(days=6)
        recent_game = GameFactory(
            group__season=season,
            date=recent_date,
            win_type=None
        )
        
        # Game 3: Overdue but already has a result (should not be changed)
        played_game = GameFactory(
            group__season=season,
            date=overdue_date,
            win_type="points",
            winner=overdue_game.black
        )
        
        # Run the task
        from league.tasks import mark_overdue_games_as_unplayed
        mark_overdue_games_as_unplayed()
        
        # Refresh the game instances from the database
        overdue_game.refresh_from_db()
        recent_game.refresh_from_db()
        played_game.refresh_from_db()
        
        # Check that only the overdue game was marked as unplayed
        self.assertEqual(overdue_game.win_type, "not_played")
        self.assertIsNone(overdue_game.winner)
        
        # Recent game should still have no result
        self.assertIsNone(recent_game.win_type)
        self.assertIsNone(recent_game.winner)
        
        # Played game should maintain its original result
        self.assertEqual(played_game.win_type, "points")
        self.assertEqual(played_game.winner, overdue_game.black)
