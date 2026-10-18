from django.core.files.base import ContentFile
from django.test import TestCase
from rest_framework.test import APIClient

from league.models import Season, SeasonState, WinType
from league.tests.factories import (
    SeasonFactory,
    GroupFactory,
    MemberFactory,
    PlayerFactory,
    GameFactory,
    RoundFactory,
)


class SeasonReportAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create seasons
        self.season1 = SeasonFactory(state=SeasonState.FINISHED, number=1)
        self.season2 = SeasonFactory(state=SeasonState.IN_PROGRESS, number=2)
        self.season3_draft = SeasonFactory(state=SeasonState.DRAFT, number=3)

        # Set up a game in season2
        group = GroupFactory(season=self.season2, name="A")
        round1 = RoundFactory(group=group, number=1)

        self.player_b = PlayerFactory(first_name="Jan", last_name="Kowalski", nick="jank", egd_pin="11112222")
        self.player_w = PlayerFactory(first_name="Adam", last_name="Nowak", nick="adamn", egd_pin=None)

        self.member_b = MemberFactory(group=group, player=self.player_b)
        self.member_w = MemberFactory(group=group, player=self.player_w)

        sgf_content = "(;GM[1]FF[4]PB[jank]PW[adamn]SZ[19];B[pd];W[dp])"
        self.game = GameFactory(
            group=group,
            round=round1,
            black=self.member_b,
            white=self.member_w,
            winner=self.member_b,
            win_type=WinType.RESIGN,
            sgf=ContentFile(sgf_content, name="game.sgf"),
        )

    def test_get_season_report_by_number(self):
        response = self.client.get(f"/api/seasons/{self.season2.number}/report/")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("players", data)
        self.assertIn("sgfs", data)
        self.assertEqual(data["total_players"], 2)
        self.assertEqual(data["total_games"], 1)
        self.assertEqual(data["players"]["11112222"], "Jan Kowalski")
        self.assertEqual(data["players"]["adamn"], "Adam Nowak")
        self.assertEqual(len(data["sgfs"]), 1)
        self.assertIn("PB[11112222]", data["sgfs"][0])
        self.assertIn("PW[adamn]", data["sgfs"][0])

    def test_get_season_report_by_pk(self):
        response = self.client.get(f"/api/seasons/{self.season2.pk}/report/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("players", data)
        self.assertIn("sgfs", data)

    def test_get_season_latest_report_resolves_to_in_progress_not_draft(self):
        # Season 3 is in DRAFT, season 2 is in IN_PROGRESS.
        # Latest report should return season 2 data.
        response = self.client.get("/api/seasons/latest/report/")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data["sgfs"]), 1)
        self.assertIn("PB[11112222]", data["sgfs"][0])


    def test_season_report_404_on_nonexistent_season(self):
        response = self.client.get("/api/seasons/99999/report/")
        self.assertEqual(response.status_code, 404)
