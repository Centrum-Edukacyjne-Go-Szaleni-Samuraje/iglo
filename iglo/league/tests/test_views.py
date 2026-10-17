import datetime
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware

from accounts.models import User, UserRole
from league.models import Season, SeasonState, Game, WinType, GroupType
from league.views import SeasonDetailView
from league.tests.factories import SeasonFactory, GroupFactory, MemberFactory, RoundFactory, GameFactory


class SeasonViewsTestCase(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        # Create users
        self.regular_user = User.objects.create_user(
            email='regular@test.com', 
            password='password123'
        )
        self.admin_user = User.objects.create_superuser(
            email='admin@test.com', 
            password='password123'
        )
        # Add referee role to both users so they can access the view
        self.regular_user.roles = [UserRole.REFEREE]
        self.regular_user.save()
        self.admin_user.roles = [UserRole.REFEREE]
        self.admin_user.save()
        # Create a season
        self.season = SeasonFactory(state=SeasonState.IN_PROGRESS, number=42)

    def _add_session_to_request(self, request):
        """Helper to add session to request for message storage"""
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
        
        # Add message storage
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        return request

    def test_revert_to_draft_admin_only(self):
        """Test that only admins can revert seasons to draft state"""
        url = reverse('season-detail', kwargs={'number': self.season.number})
        
        # Test with regular user
        request = self.factory.post(url, {'action-revert-to-draft': True})
        request.user = self.regular_user
        request = self._add_session_to_request(request)
        
        view = SeasonDetailView.as_view()
        response = view(request, number=self.season.number)
        
        # Check that season state did not change
        self.season.refresh_from_db()
        self.assertEqual(self.season.state, SeasonState.IN_PROGRESS)
        
        # Test with admin user
        request = self.factory.post(url, {'action-revert-to-draft': True})
        request.user = self.admin_user
        request = self._add_session_to_request(request)
        
        view = SeasonDetailView.as_view()
        response = view(request, number=self.season.number)
        
        # Check that season state changed to draft
        self.season.refresh_from_db()
        self.assertEqual(self.season.state, SeasonState.DRAFT)


class GroupDetailViewTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='referee@test.com',
            password='password123'
        )
        self.user.roles = [UserRole.REFEREE]
        self.user.save()

        self.season = SeasonFactory(state=SeasonState.IN_PROGRESS, number=45)
        self.group = GroupFactory(season=self.season, name="A", type=GroupType.ROUND_ROBIN)
        self.members = [
            MemberFactory(group=self.group, order=i)
            for i in range(1, 5)
        ]
        self.round_1 = RoundFactory(group=self.group, number=1)
        self.round_2 = RoundFactory(group=self.group, number=2)

        # R1: m0 beats m1, m2 beats m3
        GameFactory(
            group=self.group, round=self.round_1,
            black=self.members[0], white=self.members[1],
            winner=self.members[0], win_type=WinType.POINTS
        )
        GameFactory(
            group=self.group, round=self.round_1,
            black=self.members[2], white=self.members[3],
            winner=self.members[2], win_type=WinType.POINTS
        )
        # R2: m0 beats m2, m1 beats m3 by walkover (m3 didn't show up)
        GameFactory(
            group=self.group, round=self.round_2,
            black=self.members[0], white=self.members[2],
            winner=self.members[0], win_type=WinType.POINTS
        )
        GameFactory(
            group=self.group, round=self.round_2,
            black=self.members[1], white=self.members[3],
            winner=self.members[1], win_type=WinType.NOT_PLAYED
        )

    def test_results_table_calculation(self):
        table = self.group.results_table
        self.assertEqual(len(table), 4)

        # First place should be members[0] with 2 points
        first_pos, first_member, first_results = table[0]
        self.assertEqual(first_pos, 1)
        self.assertEqual(first_member.id, self.members[0].id)
        self.assertEqual(first_member.points, 2)
        self.assertEqual(first_member.total_walkovers, 0)

        # members[3] lost a walkover game
        m3_entry = [entry for entry in table if entry[1].id == self.members[3].id][0]
        self.assertEqual(m3_entry[1].lost_unplayed_games, 1)
        self.assertEqual(m3_entry[1].total_walkovers, 1)

    def test_group_detail_view_query_count(self):
        self.client.force_login(self.user)
        url = reverse('group-detail', kwargs={
            'season_number': self.season.number,
            'group_name': self.group.name
        })

        # The view should render efficiently in at most 7 queries (group, season/teacher, members, players, games, session, user)
        with self.assertNumQueries(7):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)