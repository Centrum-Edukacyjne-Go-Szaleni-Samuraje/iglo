from django.contrib.postgres.fields import ArrayField
from django.db import models


class EventType(models.TextChoices):
    SEASON = 'season', 'Sezon'
    LECTURE = 'lecture', 'Wykład'


class Event(models.Model):
    title = models.TextField()
    type = models.CharField(max_length=10, choices=EventType.choices)
    start_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    language = ArrayField(models.CharField(max_length=2), default=list, null=True, blank=True)
    link = models.URLField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["start_date", "start_time"]

    @property
    def is_expanded(self):
        return self.end_date is not None
