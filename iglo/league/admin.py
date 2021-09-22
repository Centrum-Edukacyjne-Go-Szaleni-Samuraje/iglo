from django.contrib import admin

from league.models import Season, Group, Player, Game

admin.site.register(Season)
admin.site.register(Group)
admin.site.register(Player)
admin.site.register(Game)
