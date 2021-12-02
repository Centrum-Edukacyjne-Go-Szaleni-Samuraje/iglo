from django.contrib.auth.mixins import UserPassesTestMixin


class AdminPermissionRequired(UserPassesTestMixin):

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin


class AdminPermissionForModifyRequired(AdminPermissionRequired):

    def test_func(self):
        if self.request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            return super().test_func()
        return True


class UserRoleRequired(UserPassesTestMixin):
    required_roles = []

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.has_role(*self.required_roles)


class UserRoleRequiredForModify(UserRoleRequired):

    def test_func(self):
        if self.request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            return super().test_func()
        return True
