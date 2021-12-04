from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.template.defaultfilters import register


class UserManager(BaseUserManager):
    def create_user(self, email, password=None):
        if not email:
            raise ValueError('Users must have an email address')
        user = self.model(email=self.normalize_email(email))
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None):
        user = self.create_user(email, password=password)
        user.is_admin = True
        user.save(using=self._db)
        return user


class UserRole(models.TextChoices):
    TEACHER = 'teacher', 'Nauczyciel'
    REFEREE = 'referee', 'Sędzia'

    @staticmethod
    def from_str(role: str):
        return UserRole[role.upper()]


class User(AbstractBaseUser):
    email = models.EmailField(unique=True)
    is_admin = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    roles = ArrayField(models.CharField(max_length=32, choices=UserRole.choices), default=list)

    objects = UserManager()

    USERNAME_FIELD = 'email'

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin

    def grant_role(self, role: UserRole):
        if role not in self.roles:
            self.roles.append(role)
            self.save()

    def refuse_role(self, role: UserRole):
        if role in self.roles:
            self.roles.remove(role)
            self.save()

    def has_role(self, *roles: UserRole):
        return self.is_staff or any(role in self.roles for role in roles)


@register.filter('has_role')
def has_role(user: User, role: str):
    try:
        role = UserRole.from_str(role)
        return user.is_authenticated and user.has_role(role)
    except KeyError:
        return False
