from django.db import models
from django.urls import reverse

from league.models import Game


class Teacher(models.Model):
    user = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, related_name="teacher_profile", blank=True
    )
    first_name = models.CharField(max_length=32)
    last_name = models.CharField(max_length=32)
    rank = models.CharField(max_length=5)
    review_info = models.TextField(blank=True)
    slug = models.SlugField(unique=True, null=True)

    def __str__(self) -> str:
        return f"Teacher: {self.first_name} {self.last_name}"

    def get_absolute_url(self):
        return reverse("teacher-detail", kwargs={"slug": self.slug})

    def get_reviews(self):
        return (
            Game.objects.filter(review_video_link__isnull=False, group__in=self.groups.all())
            .select_related("white__player", "black__player", "group__season")
            .order_by("-group__season__number", "group__name")
        )
