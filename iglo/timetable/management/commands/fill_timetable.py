import datetime

from django.core.management import BaseCommand
import lorem

from timetable.models import Event, EventType


class Command(BaseCommand):
    help = "Fill timetable"

    def handle(self, *args, **options):
        event = Event(
            title="IGLO sezon 15",
            start_date=datetime.date(2022, 2, 21),
            end_date=datetime.date(2022, 3, 27),
            type=EventType.SEASON,
            link="https://iglo.szalenisamuraje.org/",
            description=lorem.sentence()
        )
        event.save()
        event = Event(
            title="IGLO sezon 16",
            start_date=datetime.date(2022, 4, 11),
            end_date=datetime.date(2022, 5, 15),
            type=EventType.SEASON,
            link="https://iglo.szalenisamuraje.org/",
            description=lorem.sentence()
        )
        event.save()
        event = Event(
            title="IGLO sezon 17",
            start_date=datetime.date(2022, 5, 30),
            end_date=datetime.date(2022, 7, 3),
            type=EventType.SEASON,
            link="https://iglo.szalenisamuraje.org/",
            description=lorem.sentence()
        )
        event.save()
        event = Event(
            title="IGLO sezon 18",
            start_date=datetime.date(2022, 9, 19),
            end_date=datetime.date(2022, 10, 23),
            type=EventType.SEASON,
            link="https://iglo.szalenisamuraje.org/",
            description=lorem.sentence()
        )
        event.save()
        event = Event(
            title="IGLO sezon 19",
            start_date=datetime.date(2022, 11, 7),
            end_date=datetime.date(2022, 12, 11),
            type=EventType.SEASON,
            link="https://iglo.szalenisamuraje.org/",
            description=lorem.sentence()
        )
        event.save()
        event = Event(
            title="Wykład AAA",
            start_date=datetime.date(2022, 2, 23),
            start_time=datetime.time(20, 00),
            type=EventType.LECTURE,
            language=['pl'],
            link="https://discord.gg/gBHsmMX796",
            description=lorem.sentence()
        )
        event.save()
        event = Event(
            title="Wykład BBB",
            start_date=datetime.datetime(2022, 4, 13),
            start_time=datetime.time(20, 00),
            type=EventType.LECTURE,
            language=['pl'],
            link="https://discord.gg/gBHsmMX796",
            description=lorem.sentence()
        )
        event.save()
        event = Event(
            title="Wykład CCC",
            start_date=datetime.datetime(2022, 6, 1),
            start_time=datetime.time(20, 00),
            type=EventType.LECTURE,
            language=['pl'],
            link="https://discord.gg/gBHsmMX796"
        )
        event.save()
        event = Event(
            title="Wykład DDD",
            start_date=datetime.datetime(2022, 9, 21),
            start_time=datetime.time(20, 00),
            type=EventType.LECTURE,
            language=['pl'],
            link="https://discord.gg/gBHsmMX796",
            description=lorem.sentence()
        )
        event.save()
        event = Event(
            title="Wykład EEE",
            start_date=datetime.datetime(2022, 2, 23),
            start_time=datetime.time(20, 00),
            type=EventType.LECTURE,
            language=['pl'],
            link="https://discord.gg/gBHsmMX796",
            description=lorem.sentence()
        )
        event.save()
