from django.contrib import admin

from accounts.models import User


class UserModelAdmin(admin.ModelAdmin):
    list_display = ["email", "last_login", "has_password"]
    search_fields = ["email"]

    def has_password(self, object):
        return object.has_usable_password()

    has_password.boolean = True


admin.site.register(User, UserModelAdmin)
