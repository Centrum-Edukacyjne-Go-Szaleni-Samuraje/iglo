import datetime as dt
from dataclasses import dataclass

from django.views.generic import TemplateView

from timetable.models import Event, EventType


@dataclass
class DisplayEvent:
    title: str
    date: dt.date
    time: dt.time
    language: list[str]
    type: EventType
    beginningOrEnding: str = None


class EventListView(TemplateView):
    template_name = 'timetable/timetable.html'

    # DisplayEvents should be cached?
    def get_context_data(self, **kwargs):
        month_ago = dt.date.today() - dt.timedelta(days=365)
        events = Event.objects.filter(start_date__gte=month_ago).all()
        events_to_display = []
        for event in events:
            if event.is_expanded:
                events_to_display.append(
                    DisplayEvent(event.title, event.start_date, event.start_time, event.language, event.type, 'beginning'))
                events_to_display.append(
                    DisplayEvent(event.title, event.end_date, event.end_time, event.language, event.type, 'ending'))
            else:
                events_to_display.append(
                    DisplayEvent(event.title, event.start_date, event.start_time, event.language, event.type))
        events_to_display.sort(key=lambda e: dt.datetime.combine(e.date, e.time or dt.time()))
        return super().get_context_data(**kwargs) | {
            "events": events_to_display
        }
