import datetime

from django.db.models import Q
from django.test import TestCase

from league.models import MemberResult, Season, SeasonState, Game, Round, Member
from league.tests.factories import (
    MemberFactory,
    GroupFactory,
    GameFactory,
    SeasonFactory,
    PlayerFactory,
)


class MemberTestCase(TestCase):
    def test_score(self):
        group = GroupFactory()
        member_1 = MemberFactory(group=group)
        member_2 = MemberFactory(group=group)
        member_3 = MemberFactory(group=group)
        member_4 = MemberFactory(group=group)
        GameFactory(group=group, white=member_1, black=member_2, winner=member_1)
        GameFactory(group=group, white=member_3, black=member_1, winner=member_1)
        GameFactory(group=group, white=member_1, black=member_4, winner=member_4)

        self.assertEqual(member_1.score, 2)

    def test_sodos(self):
        group = GroupFactory()
        member_1 = MemberFactory(group=group)
        member_2 = MemberFactory(group=group)
        member_3 = MemberFactory(group=group)
        member_4 = MemberFactory(group=group)
        GameFactory(group=group, white=member_1, black=member_2, winner=member_1)
        GameFactory(group=group, white=member_3, black=member_1, winner=member_1)
        GameFactory(group=group, white=member_1, black=member_4, winner=member_4)
        GameFactory(group=group, white=member_2, black=member_3, winner=member_2)
        GameFactory(group=group, white=member_4, black=member_2, winner=member_2)
        GameFactory(group=group, white=member_3, black=member_4, winner=member_3)

        self.assertEqual(member_1.sodos, 3)

    def test_result_for_promotion(self):
        group = GroupFactory(name="B")
        member_1 = MemberFactory(group=group)
        member_2 = MemberFactory(group=group)
        member_3 = MemberFactory(group=group)
        GameFactory(group=group, white=member_1, black=member_2, winner=member_1)
        GameFactory(group=group, white=member_1, black=member_3, winner=member_1)
        GameFactory(group=group, white=member_2, black=member_3, winner=member_2)

        self.assertEqual(member_1.result, MemberResult.PROMOTION)

    def test_result_for_relegation(self):
        group = GroupFactory()
        member_1 = MemberFactory(group=group)
        member_2 = MemberFactory(group=group)
        member_3 = MemberFactory(group=group)
        GameFactory(group=group, white=member_1, black=member_2, winner=member_1)
        GameFactory(group=group, white=member_1, black=member_3, winner=member_1)
        GameFactory(group=group, white=member_2, black=member_3, winner=member_2)

        self.assertEqual(member_3.result, MemberResult.RELEGATION)

    def test_result_for_stay(self):
        group = GroupFactory()
        member_1 = MemberFactory(group=group)
        member_2 = MemberFactory(group=group)
        member_3 = MemberFactory(group=group)
        GameFactory(group=group, white=member_1, black=member_2, winner=member_1)
        GameFactory(group=group, white=member_1, black=member_3, winner=member_1)
        GameFactory(group=group, white=member_2, black=member_3, winner=member_2)

        self.assertEqual(member_2.result, MemberResult.STAY)


class SeasonTestCase(TestCase):
    def test_prepare_season_from_previous(self):
        season = SeasonFactory(
            promotion_count=1, state=SeasonState.READY.value, number=1
        )
        group_a = GroupFactory(season=season, name="A")
        group_a_member_1 = MemberFactory(group=group_a, order=1)
        group_a_member_2 = MemberFactory(group=group_a, order=2)
        group_a_member_3 = MemberFactory(group=group_a, order=3)
        GameFactory(
            group=group_a, white=group_a_member_1, black=group_a_member_2, winner=group_a_member_1
        )
        GameFactory(
            group=group_a, white=group_a_member_1, black=group_a_member_3, winner=group_a_member_1
        )
        GameFactory(
            group=group_a, white=group_a_member_2, black=group_a_member_3, winner=group_a_member_2
        )
        group_b = GroupFactory(season=season, name="B")
        group_b_member_1 = MemberFactory(group=group_b, order=1)
        group_b_member_2 = MemberFactory(group=group_b, order=2)
        group_b_member_3 = MemberFactory(group=group_b, order=3)
        GameFactory(
            group=group_b, white=group_b_member_1, black=group_b_member_2, winner=group_a_member_1
        )
        GameFactory(
            group=group_b, white=group_b_member_1, black=group_b_member_3, winner=group_a_member_1
        )
        GameFactory(
            group=group_b, white=group_b_member_2, black=group_b_member_3, winner=group_a_member_2
        )

        new_season = Season.objects.prepare_season(
            start_date=datetime.date(2021, 1, 1), players_per_group=3, promotion_count=1
        )

        self.assertEqual(new_season.state, SeasonState.DRAFT.value)
        self.assertEqual(new_season.number, 2)
        self.assertEqual(new_season.start_date, datetime.date(2021, 1, 1))
        self.assertEqual(new_season.end_date, datetime.date(2021, 1, 14))
        self.assertEqual(new_season.players_per_group, 3)
        self.assertEqual(new_season.promotion_count, 1)
        self.assertEqual(new_season.groups.count(), 2)
        new_group_a = new_season.groups.get(name="A")
        self.assertEqual(new_group_a.members.count(), 3)
        self.assertTrue(
            new_group_a.members.filter(player=group_a_member_1.player, order=1).exists()
        )
        self.assertTrue(
            new_group_a.members.filter(player=group_a_member_2.player, order=2).exists()
        )
        self.assertTrue(
            new_group_a.members.filter(player=group_b_member_1.player, order=3).exists()
        )
        new_group_b = new_season.groups.get(name="B")
        self.assertEqual(new_group_b.members.count(), 3)
        self.assertTrue(
            new_group_b.members.filter(player=group_a_member_3.player, order=1).exists()
        )
        self.assertTrue(
            new_group_b.members.filter(player=group_b_member_2.player, order=2).exists()
        )
        self.assertTrue(
            new_group_b.members.filter(player=group_b_member_3.player, order=3).exists()
        )

    def test_prepare_season_when_previous_is_in_draft(self):
        SeasonFactory(state=SeasonState.DRAFT.value)

        with self.assertRaises(ValueError):
            Season.objects.prepare_season(
                start_date=datetime.date(2021, 1, 1),
                players_per_group=3,
                promotion_count=1,
            )

    def test_delete_group(self):
        season = SeasonFactory(state=SeasonState.DRAFT.value)
        group_1 = GroupFactory(season=season, name="A")
        group_2 = GroupFactory(season=season, name="B")

        season.delete_group(group_id=group_1.id)

        group_2.refresh_from_db()
        self.assertEqual(season.groups.count(), 1)
        self.assertEqual(group_2.name, "A")

    def test_add_gorup(self):
        season = SeasonFactory(state=SeasonState.DRAFT.value)

        season.add_group()

        group = season.groups.get()
        self.assertEqual(season.groups.count(), 1)
        self.assertEqual(group.name, "A")

    def test_start(self):
        season = SeasonFactory(state=SeasonState.DRAFT.value, start_date=datetime.date(2021, 1, 1))
        group = GroupFactory(season=season)
        member_1 = MemberFactory(group=group)
        member_2 = MemberFactory(group=group)
        member_3 = MemberFactory(group=group)
        member_4 = MemberFactory(group=group)

        season.start()

        season.refresh_from_db()
        self.assertEqual(season.state, SeasonState.READY.value)
        self.assertEqual(group.rounds.count(), 3)
        round_1 = group.rounds.get(number=1)
        self.assertEqual(round_1.games.count(), 2)
        self.assertEqual(round_1.start_date, datetime.date(2021, 1, 1))
        self.assertEqual(round_1.end_date, datetime.date(2021, 1, 7))
        self.assertTrue(self._game_exists(round_1, member_1, member_4))
        self.assertTrue(self._game_exists(round_1, member_2, member_3))
        round_2 = group.rounds.get(number=2)
        self.assertEqual(round_2.start_date, datetime.date(2021, 1, 8))
        self.assertEqual(round_2.end_date, datetime.date(2021, 1, 14))
        self.assertEqual(round_2.games.count(), 2)
        self.assertTrue(self._game_exists(round_2, member_1, member_3))
        self.assertTrue(self._game_exists(round_2, member_2, member_4))
        round_3 = group.rounds.get(number=3)
        self.assertEqual(round_3.games.count(), 2)
        self.assertEqual(round_3.start_date, datetime.date(2021, 1, 15))
        self.assertEqual(round_3.end_date, datetime.date(2021, 1, 21))
        self.assertTrue(self._game_exists(round_3, member_1, member_2))
        self.assertTrue(self._game_exists(round_3, member_3, member_4))

    def _game_exists(self, round: Round, member_1: Member, member_2: Member) -> bool:
        return (
            Game.objects.filter(group=round.group, round=round)
                .filter(
                Q(black=member_1, white=member_2) | Q(black=member_2, white=member_1)
            )
                .exists()
        )


class GroupTestCase(TestCase):
    def test_delete_member(self):
        group = GroupFactory(season__state=SeasonState.DRAFT.value)
        member_1 = MemberFactory(group=group, order=1)
        member_2 = MemberFactory(group=group, order=2)
        member_3 = MemberFactory(group=group, order=2)

        group.delete_member(member_id=member_2.id)

        member_1.refresh_from_db()
        member_3.refresh_from_db()
        self.assertEqual(group.members.count(), 2)
        self.assertEqual(member_1.order, 1)
        self.assertEqual(member_3.order, 2)

    def test_move_member_up(self):
        group = GroupFactory(season__state=SeasonState.DRAFT.value)
        member_1 = MemberFactory(group=group, order=1)
        member_2 = MemberFactory(group=group, order=2)

        group.move_member_up(member_id=member_2.id)

        member_1.refresh_from_db()
        member_2.refresh_from_db()
        self.assertEqual(member_2.order, 1)
        self.assertEqual(member_1.order, 2)

    def test_move_member_down(self):
        group = GroupFactory(season__state=SeasonState.DRAFT.value)
        member_1 = MemberFactory(group=group, order=1)
        member_2 = MemberFactory(group=group, order=2)

        group.move_member_down(member_id=member_1.id)

        member_1.refresh_from_db()
        member_2.refresh_from_db()
        self.assertEqual(member_1.order, 2)
        self.assertEqual(member_2.order, 1)

    def test_add_member(self):
        season = SeasonFactory(state=SeasonState.DRAFT.value)
        group_1 = GroupFactory(season=season)
        MemberFactory(group=group_1, order=1)
        group_2 = GroupFactory(season=season)
        player = PlayerFactory()
        MemberFactory(group=group_2, player=player)

        group_1.add_member(player_nick=player.nick)

        new_member = group_1.members.get(player=player)
        self.assertEqual(group_1.members.count(), 2)
        self.assertEqual(new_member.group, group_1)
        self.assertEqual(new_member.order, 2)
        self.assertEqual(group_2.members.count(), 0)
