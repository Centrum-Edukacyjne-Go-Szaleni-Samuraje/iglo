from unittest import mock
from django.core.files.base import ContentFile
from django.test import TestCase

from league.models import Season, SeasonState, WinType
from league.services.season_report import SeasonReportService
from league.tests.factories import (
    SeasonFactory,
    GroupFactory,
    MemberFactory,
    PlayerFactory,
    GameFactory,
    RoundFactory,
)


class SeasonReportServiceTestCase(TestCase):
    def test_get_player_identifier_with_egd_pin(self):
        player = PlayerFactory.build(nick="goplayer", egd_pin="19500001")
        self.assertEqual(SeasonReportService.get_player_identifier(player), "19500001")

    def test_get_player_identifier_without_egd_pin(self):
        player = PlayerFactory.build(nick="goplayer", egd_pin=None)
        self.assertEqual(SeasonReportService.get_player_identifier(player), "goplayer")

        player_empty = PlayerFactory.build(nick="goplayer2", egd_pin="")
        self.assertEqual(SeasonReportService.get_player_identifier(player_empty), "goplayer2")

    def test_transform_sgf_replaces_pb_and_pw(self):
        raw_sgf = "(;GM[1]FF[4]CA[UTF-8]PB[OldBlack]PW[OldWhite]KM[6.5]SZ[19];B[pd];W[dp])"
        transformed = SeasonReportService.transform_sgf(raw_sgf, black_id="12345", white_id="67890")
        self.assertIn("PB[12345]", transformed)
        self.assertIn("PW[67890]", transformed)
        self.assertNotIn("PB[OldBlack]", transformed)
        self.assertNotIn("PW[OldWhite]", transformed)
        self.assertIn(";B[pd];W[dp]", transformed)

    def test_transform_sgf_handles_escaped_brackets(self):
        raw_sgf = r"(;GM[1]PB[Player\[1\]]PW[Player\[2\]];B[pd])"
        transformed = SeasonReportService.transform_sgf(raw_sgf, black_id="B_PIN", white_id="W_PIN")
        self.assertIn("PB[B_PIN]", transformed)
        self.assertIn("PW[W_PIN]", transformed)

    def test_transform_sgf_injects_missing_pb_and_pw(self):
        raw_sgf = "(;GM[1]SZ[19];B[pd])"
        transformed = SeasonReportService.transform_sgf(raw_sgf, black_id="1111", white_id="2222")
        self.assertIn("PB[1111]", transformed)
        self.assertIn("PW[2222]", transformed)
        self.assertTrue(transformed.startswith("(;"))

    def test_transform_sgf_preserves_moves_matching_nicknames(self):
        # A nickname could be 'ko' or 'dd', which shouldn't be touched in moves
        raw_sgf = "(;GM[1]PB[ko]PW[dd];B[dd];W[ko])"
        transformed = SeasonReportService.transform_sgf(raw_sgf, black_id="19500001", white_id="19500002")
        self.assertIn("PB[19500001]", transformed)
        self.assertIn("PW[19500002]", transformed)
        self.assertIn(";B[dd];W[ko]", transformed)

    def test_generate_report_for_season(self):
        season = SeasonFactory(state=SeasonState.IN_PROGRESS, number=10)
        group = GroupFactory(season=season, name="A")
        round1 = RoundFactory(group=group, number=1)

        player_b = PlayerFactory(first_name="Jan", last_name="Kowalski", nick="jank", egd_pin="11112222")
        player_w = PlayerFactory(first_name="Adam", last_name="Nowak", nick="adamn", egd_pin=None)
        player_c = PlayerFactory(first_name="Anna", last_name="Wisniewska", nick="annaw", egd_pin="33334444")

        member_b = MemberFactory(group=group, player=player_b)
        member_w = MemberFactory(group=group, player=player_w)
        member_c = MemberFactory(group=group, player=player_c)

        # 1. Played game with SGF
        sgf_content = "(;GM[1]FF[4]PB[jank]PW[adamn]SZ[19];B[pd];W[dp])"
        game_played = GameFactory(
            group=group,
            round=round1,
            black=member_b,
            white=member_w,
            winner=member_b,
            win_type=WinType.RESIGN,
            sgf=ContentFile(sgf_content, name="game1.sgf"),
        )

        # 2. Unplayed game
        GameFactory(
            group=group,
            round=round1,
            black=member_b,
            white=member_c,
            winner=None,
            win_type=WinType.NOT_PLAYED,
            sgf=None,
        )

        # 3. BYE game
        GameFactory(
            group=group,
            round=round1,
            black=member_c,
            white=None,
            winner=member_c,
            win_type=WinType.BYE,
            sgf=None,
        )

        # 4. Played game in a different season
        other_season = SeasonFactory(state=SeasonState.FINISHED, number=9)
        other_group = GroupFactory(season=other_season, name="A")
        other_round = RoundFactory(group=other_group, number=1)
        other_member_b = MemberFactory(group=other_group, player=player_b)
        other_member_w = MemberFactory(group=other_group, player=player_w)
        GameFactory(
            group=other_group,
            round=other_round,
            black=other_member_b,
            white=other_member_w,
            winner=other_member_w,
            win_type=WinType.POINTS,
            sgf=ContentFile("(;GM[1]SZ[19];B[pp])", name="other.sgf"),
        )

        report = SeasonReportService.generate_report(season)

        self.assertIn("players", report)
        self.assertIn("sgfs", report)
        self.assertEqual(report["total_players"], 2)
        self.assertEqual(report["total_games"], 1)

        # Only players from game1 in season 10 should be in players dict
        self.assertEqual(len(report["players"]), 2)
        self.assertIn("11112222", report["players"])
        self.assertEqual(report["players"]["11112222"], "Jan Kowalski")
        # player_w has no EGD pin, falls back to nick "adamn"
        self.assertIn("adamn", report["players"])
        self.assertEqual(report["players"]["adamn"], "Adam Nowak")
        self.assertNotIn("33334444", report["players"])

        # Only game1 should be in sgfs
        self.assertEqual(len(report["sgfs"]), 1)
        self.assertIn("PB[11112222]", report["sgfs"][0])
        self.assertIn("PW[adamn]", report["sgfs"][0])
