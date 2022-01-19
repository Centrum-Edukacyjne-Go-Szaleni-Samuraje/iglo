from django.contrib import admin

from league.models import Season, Group, Player, Game, Round, Member, Teacher


class SeasonModelAdmin(admin.ModelAdmin):
    list_display = ["number", "start_date", "end_date"]


class PlayerModelAdmin(admin.ModelAdmin):
    list_display = ["nick", "first_name", "last_name", "rank", "auto_join", "user"]
    search_fields = ["nick", "first_name", "last_name", "user__email"]
    list_select_related = ["user"]


class GameModelAdmin(admin.ModelAdmin):
    list_display = ["black", "white", "season_number", "group_name", "round_number"]
    raw_id_fields = ["black", "white", "winner", "round", "group"]
    list_select_related = ["black__player", "white__player", "group__season", "round"]

    def season_number(self, obj):
        return obj.group.season.number

    def group_name(self, obj):
        return obj.group.name

    def round_number(self, obj):
        return obj.round.number


class RoundModelAdmin(admin.ModelAdmin):
    list_display = ["number", "season_number", "group_name"]
    raw_id_fields = ["group"]
    list_select_related = ["group__season"]

    def season_number(self, obj):
        return obj.group.season.number

    def group_name(self, obj):
        return obj.group.name


class MemberModelAdmin(admin.ModelAdmin):
    list_display = ["player", "season_number", "group_name"]
    ordering = ["-group__season__number", "-group__name"]

    def season_number(self, obj):
        return obj.group.season.number

    def group_name(self, obj):
        return obj.group.name


class GroupModelAdmin(admin.ModelAdmin):
    list_display = ["name", "season_number", "type"]
    list_select_related = ["season"]

    def season_number(self, obj):
        return obj.season.number


class TeacherModelAdmin(admin.ModelAdmin):
    pass


admin.site.register(Season, SeasonModelAdmin)
admin.site.register(Group, GroupModelAdmin)
admin.site.register(Player, PlayerModelAdmin)
admin.site.register(Game, GameModelAdmin)
admin.site.register(Round, RoundModelAdmin)
admin.site.register(Member, MemberModelAdmin)
admin.site.register(Teacher, TeacherModelAdmin)
