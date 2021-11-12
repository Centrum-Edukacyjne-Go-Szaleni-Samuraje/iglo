from django.contrib import admin

from league.models import Season, Group, Player, Game, Round


class PlayerModelAdmin(admin.ModelAdmin):
    list_display = ["nick", "first_name", "last_name", "rank", "user"]
    search_fields = ["nick", "first_name", "last_name", "user__email"]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related("user")


admin.site.register(Season)
admin.site.register(Group)
admin.site.register(Player, PlayerModelAdmin)
admin.site.register(Game)
admin.site.register(Round)
