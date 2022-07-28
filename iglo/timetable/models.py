from datetime import timedelta

from django.contrib.postgres.fields import ArrayField
from django.db import models


class EventType(models.TextChoices):
    SEASON = 'season', 'Sezon'
    LECTURE = 'lecture', 'Wykład'


class Event(models.Model):
    title = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=EventType.choices)
    start_date = models.DateField()
    start_time = models.TimeField(null=True)
    end_date = models.DateField(null=True)
    end_time = models.TimeField(null=True)
    language = ArrayField(models.CharField(max_length=2), null=True)

    class Meta:
        ordering = ["start_date", "start_time"]

    @property
    def is_expanded(self):
        return self.end_date is not None
