import datetime
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware

from accounts.models import User, UserRole
from league.models import Season, SeasonState, Game, WinType
from league.views import SeasonDetailView
from league.tests.factories import SeasonFactory, GroupFactory, MemberFactory


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