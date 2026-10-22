from unittest import mock
import requests
from django.test import SimpleTestCase

from league.utils.kifubara import (
    KifubaraConfig,
    KifubaraException,
    upload_game_to_kifubara,
)


class KifubaraUtilsTestCase(SimpleTestCase):

    def setUp(self):
        self.config = KifubaraConfig(
            service_url="https://kifubara.app/api/integrations/analyze",
            key="secret-token-123",
        )

    @mock.patch("requests.post")
    def test_upload_game_success_with_rich_metadata(self, post_mock):
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "game_id": "8fe45241-1111",
            "share_url": "https://kifubara.app/share/p580zq7I",
            "state_url": "https://kifubara.app/api/integrations/games/8fe45241-1111/state",
            "match_id": "s46-gA-black-white-1",
            "deduped": False,
        }
        post_mock.return_value = mock_response

        share_url = upload_game_to_kifubara(
            config=self.config,
            sgf_data="(;GM[1])",
            match_id="s46-gA-black-white-1",
            season="46",
            group="A",
            round="2",
            black="Jan Kowalski",
            white="Anna Nowak",
            board="1",
            external_url="https://iglo.go.art.pl/game/1",
        )

        self.assertEqual(share_url, "https://kifubara.app/share/p580zq7I")
        post_mock.assert_called_once_with(
            url="https://kifubara.app/api/integrations/analyze",
            headers={
                "Authorization": "Bearer secret-token-123",
                "Content-Type": "application/json",
            },
            json={
                "sgf": "(;GM[1])",
                "match_id": "s46-gA-black-white-1",
                "season": "46",
                "group": "A",
                "round": "2",
                "black": "Jan Kowalski",
                "white": "Anna Nowak",
                "board": "1",
                "external_url": "https://iglo.go.art.pl/game/1",
            },
            timeout=30,
        )

    @mock.patch("requests.post")
    def test_upload_game_http_error(self, post_mock):
        mock_response = mock.Mock()
        mock_response.status_code = 400
        mock_response.text = '{"error": "invalid_sgf"}'
        post_mock.return_value = mock_response

        with self.assertRaises(KifubaraException) as ctx:
            upload_game_to_kifubara(
                config=self.config,
                sgf_data="bad sgf",
                match_id="test-match",
            )
        self.assertIn("HTTP 400", str(ctx.exception))

    @mock.patch("requests.post")
    def test_upload_game_json_error(self, post_mock):
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"error": "parse_failed"}
        post_mock.return_value = mock_response

        with self.assertRaises(KifubaraException) as ctx:
            upload_game_to_kifubara(
                config=self.config,
                sgf_data="bad",
                match_id="test-match",
            )
        self.assertIn("parse_failed", str(ctx.exception))
