from django.contrib import admin

from timetable.models import Event


class EventModelAdmin(admin.ModelAdmin):
    list_display = ["title", "type", "start_date", "start_time", "end_date", "end_time", "description", "link",
                    "language"]
    search_fields = ["title", "type"]


admin.site.register(Event, EventModelAdmin)
