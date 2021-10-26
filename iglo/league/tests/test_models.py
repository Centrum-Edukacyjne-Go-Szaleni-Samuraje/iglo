import datetime

from django.test import TestCase

from league.models import MemberResult, Season, SeasonState
from league.tests.factories import (
    MemberFactory,
    GroupFactory,
    GameFactory,
    SeasonFactory,
)


class MemberTestCase(TestCase):
    def test_score(self):
        group = GroupFactory()
        member_1 = MemberFactory(group=group)
        member_2 = MemberFactory(group=group)
        member_3 = MemberFactory(group=group)
        member_4 = MemberFactory(group=group)
        GameFactory(group=group, white=member_1, black=member_2, result="W")
        GameFactory(group=group, white=member_3, black=member_1, result="B")
        GameFactory(group=group, white=member_1, black=member_4, result="B")

        self.assertEqual(member_1.score, 2)

    def test_sodos(self):
        group = GroupFactory()
        member_1 = MemberFactory(group=group)
        member_2 = MemberFactory(group=group)
        member_3 = MemberFactory(group=group)
        member_4 = MemberFactory(group=group)
        GameFactory(group=group, white=member_1, black=member_2, result="W")
        GameFactory(group=group, white=member_3, black=member_1, result="B")
        GameFactory(group=group, white=member_1, black=member_4, result="B")
        GameFactory(group=group, white=member_2, black=member_3, result="W")
        GameFactory(group=group, white=member_4, black=member_2, result="B")
        GameFactory(group=group, white=member_3, black=member_4, result="W")

        self.assertEqual(member_1.sodos, 3)

    def test_result_for_promotion(self):
        group = GroupFactory(name="B")
        member_1 = MemberFactory(group=group)
        member_2 = MemberFactory(group=group)
        member_3 = MemberFactory(group=group)
        GameFactory(group=group, white=member_1, black=member_2, result="W")
        GameFactory(group=group, white=member_1, black=member_3, result="W")
        GameFactory(group=group, white=member_2, black=member_3, result="W")

        self.assertEqual(member_1.result, MemberResult.PROMOTION)

    def test_result_for_relegation(self):
        group = GroupFactory()
        member_1 = MemberFactory(group=group)
        member_2 = MemberFactory(group=group)
        member_3 = MemberFactory(group=group)
        GameFactory(group=group, white=member_1, black=member_2, result="W")
        GameFactory(group=group, white=member_1, black=member_3, result="W")
        GameFactory(group=group, white=member_2, black=member_3, result="W")

        self.assertEqual(member_3.result, MemberResult.RELEGATION)

    def test_result_for_stay(self):
        group = GroupFactory()
        member_1 = MemberFactory(group=group)
        member_2 = MemberFactory(group=group)
        member_3 = MemberFactory(group=group)
        GameFactory(group=group, white=member_1, black=member_2, result="W")
        GameFactory(group=group, white=member_1, black=member_3, result="W")
        GameFactory(group=group, white=member_2, black=member_3, result="W")

        self.assertEqual(member_2.result, MemberResult.STAY)


class SeasonTestCase(TestCase):
    def test_prepare_season(self):
        season = SeasonFactory(promotion_count=1, state=SeasonState.STARTED.value, number=1)
        group_a = GroupFactory(season=season, name="A")
        group_a_member_1 = MemberFactory(group=group_a, order=1)
        group_a_member_2 = MemberFactory(group=group_a, order=2)
        group_a_member_3 = MemberFactory(group=group_a, order=3)
        GameFactory(
            group=group_a, white=group_a_member_1, black=group_a_member_2, result="W"
        )
        GameFactory(
            group=group_a, white=group_a_member_1, black=group_a_member_3, result="W"
        )
        GameFactory(
            group=group_a, white=group_a_member_2, black=group_a_member_3, result="W"
        )
        group_b = GroupFactory(season=season, name="B")
        group_b_member_1 = MemberFactory(group=group_b, order=1)
        group_b_member_2 = MemberFactory(group=group_b, order=2)
        group_b_member_3 = MemberFactory(group=group_b, order=3)
        GameFactory(
            group=group_b, white=group_b_member_1, black=group_b_member_2, result="W"
        )
        GameFactory(
            group=group_b, white=group_b_member_1, black=group_b_member_3, result="W"
        )
        GameFactory(
            group=group_b, white=group_b_member_2, black=group_b_member_3, result="W"
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
