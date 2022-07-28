from django.urls import path

from timetable.views import EventListView

urlpatterns = [
    path("timetable", EventListView.as_view(), name="timetable"),
]
