import datetime
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.http import Http404

from league.models import Game, WinType, SeasonState, Member
from league.views import GroupEGDExportView
from league.tests.factories import (
    MemberFactory,
    GroupFactory,
    GameFactory,
    SeasonFactory,
    PlayerFactory,
    RoundFactory,
)
from accounts.factories import UserFactory
from accounts.models import UserRole


class EGDEligibilityTestCase(TestCase):
    """Tests for the EGD eligibility of games."""

    def setUp(self):
        self.season = SeasonFactory(state=SeasonState.IN_PROGRESS)
        self.group = GroupFactory(season=self.season)
        self.round = RoundFactory(group=self.group)
        
        # Create four players with different EGD approval settings
        self.player1 = PlayerFactory(egd_approval=True)  # Approves EGD
        self.player2 = PlayerFactory(egd_approval=True)  # Approves EGD
        self.player3 = PlayerFactory(egd_approval=False)  # Does not approve EGD
        self.player4 = PlayerFactory(egd_approval=False)  # Does not approve EGD
        
        # Create members for the group
        self.member1 = MemberFactory(group=self.group, player=self.player1)
        self.member2 = MemberFactory(group=self.group, player=self.player2)
        self.member3 = MemberFactory(group=self.group, player=self.player3)
        self.member4 = MemberFactory(group=self.group, player=self.player4)

    def test_game_is_egd_eligible(self):
        """Test that a game is EGD eligible if both players have approved EGD reporting."""
        # Game with both players approving EGD
        game1 = GameFactory(
            group=self.group,
            round=self.round,
            black=self.member1,
            white=self.member2,
            winner=self.member1,
            win_type=WinType.RESIGN
        )
        self.assertTrue(game1.is_egd_eligible)
        
        # Game with one player not approving EGD
        game2 = GameFactory(
            group=self.group,
            round=self.round,
            black=self.member1,
            white=self.member3,
            winner=self.member1,
            win_type=WinType.RESIGN
        )
        self.assertFalse(game2.is_egd_eligible)
        
        # Game with both players not approving EGD
        game3 = GameFactory(
            group=self.group,
            round=self.round,
            black=self.member3,
            white=self.member4,
            winner=self.member3,
            win_type=WinType.RESIGN
        )
        self.assertFalse(game3.is_egd_eligible)

    def test_bye_game_is_not_egd_eligible(self):
        """Test that a BYE game is not EGD eligible."""
        game = GameFactory(
            group=self.group,
            round=self.round,
            winner=self.member1,
            win_type=WinType.BYE
        )
        self.assertFalse(game.is_egd_eligible)

    def test_not_played_game_is_not_eligible_for_export(self):
        """Test that a not played game is not eligible for EGD export even if both players approve EGD."""
        # Create a game that hasn't been played yet between two EGD-approved players
        unplayed_game = GameFactory(
            group=self.group,
            round=self.round,
            black=self.member1,
            white=self.member2,
            win_type=None  # Not played yet
        )
        
        # The game should be marked as EGD eligible (for UI purposes)
        self.assertTrue(unplayed_game.is_egd_eligible)
        
        # But for export, a game needs to be both EGD eligible AND played
        # Create a view object to manually check export eligibility logic
        would_be_exported = unplayed_game.is_egd_eligible and unplayed_game.is_played and unplayed_game.win_type != WinType.NOT_PLAYED
        self.assertFalse(would_be_exported)


class EligibilitySelectionLogicTestCase(TestCase):
    """Tests for the logic of selecting EGD eligible games for export."""

    def setUp(self):
        self.season = SeasonFactory(state=SeasonState.IN_PROGRESS)
        self.group = GroupFactory(season=self.season)
        self.round = RoundFactory(group=self.group)
        
        # Create players with different EGD approval settings
        self.player1 = PlayerFactory(egd_approval=True, first_name="John", last_name="Doe", country="PL")
        self.player2 = PlayerFactory(egd_approval=True, first_name="Jane", last_name="Smith", country="UK")
        self.player3 = PlayerFactory(egd_approval=False, first_name="Bob", last_name="Brown", country="US")
        
        # Create members for the group
        self.member1 = MemberFactory(group=self.group, player=self.player1, rank=2100)  # Around 1d
        self.member2 = MemberFactory(group=self.group, player=self.player2, rank=1900)  # Around 1k
        self.member3 = MemberFactory(group=self.group, player=self.player3, rank=1500)  # Around 5k

    def test_export_only_includes_eligible_games(self):
        """Test that only games eligible for EGD are included in export."""
        # Game with both players approving EGD
        eligible_game = GameFactory(
            group=self.group,
            round=self.round,
            black=self.member1,
            white=self.member2,
            winner=self.member1,
            win_type=WinType.RESIGN
        )
        
        # Game with one player not approving EGD
        ineligible_game = GameFactory(
            group=self.group,
            round=self.round,
            black=self.member1,
            white=self.member3,
            winner=self.member1,
            win_type=WinType.RESIGN
        )
        
        # Apply the same filtering logic that GroupEGDExportView uses
        eligible_for_export = []
        for game in Game.objects.filter(group=self.group):
            if game.is_egd_eligible and game.is_played and game.win_type != WinType.NOT_PLAYED:
                eligible_for_export.append(game)
        
        # Check that only eligible game is included
        self.assertEqual(len(eligible_for_export), 1)
        self.assertEqual(eligible_for_export[0], eligible_game)
        
    def test_export_skips_not_played_games(self):
        """Test that unplayed games aren't included in export even if players approve EGD."""
        # Played game with EGD approval
        played_game = GameFactory(
            group=self.group,
            round=self.round,
            black=self.member1,
            white=self.member2,
            winner=self.member1,
            win_type=WinType.RESIGN
        )
        
        # Unplayed game with EGD approval
        unplayed_game = GameFactory(
            group=self.group,
            round=self.round,
            black=self.member1,
            white=self.member2,
            win_type=None  # Not played
        )
        
        # Apply the export filtering logic
        eligible_for_export = []
        for game in Game.objects.filter(group=self.group):
            if game.is_egd_eligible and game.is_played and game.win_type != WinType.NOT_PLAYED:
                eligible_for_export.append(game)
        
        # Check that only played game is included
        self.assertEqual(len(eligible_for_export), 1)
        self.assertEqual(eligible_for_export[0], played_game)