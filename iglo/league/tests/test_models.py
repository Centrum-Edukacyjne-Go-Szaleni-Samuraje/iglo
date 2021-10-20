from django.test import TestCase

from league.tests.factories import MemberFactory, GroupFactory, GameFactory


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
