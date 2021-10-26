from django.contrib.auth.mixins import UserPassesTestMixin


class AdminPermissionRequired(UserPassesTestMixin):

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin
