from unittest import mock

from django.test import TestCase

from league.models import GameAIAnalyseUploadStatus
from league.tasks import game_ai_analyse_upload_task
from league.tests.factories import GameFactory
from league.utils.aisensei import AISenseiException


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
        game = GameFactory(sgf__data="data")

        with mock.patch("league.tasks.upload_sgf") as upload_sgf_mock:
            upload_sgf_mock.side_effect = AISenseiException("error message")
            game_ai_analyse_upload_task(game_id=game.id)

        upload_sgf_mock.assert_called_once_with(config=mock.ANY, sgf_data="data")
        game.refresh_from_db()
        self.assertIsNone(game.ai_analyse_link)
        upload = game.ai_analyse_uploads.get()
        self.assertEqual(upload.status, GameAIAnalyseUploadStatus.FAILED)
        self.assertIsNone(upload.result)
        self.assertEqual(upload.error, "error message")
