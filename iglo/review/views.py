from django.views.generic import DetailView, ListView

from league.models import Game
from review.models import Teacher


class TeacherListView(ListView):
    model = Teacher

    def get_queryset(self):
        return super().get_queryset().order_by("first_name", "last_name")


class TeacherDetailView(DetailView):
    model = Teacher


class ReviewListView(ListView):
    model = Game  # todo: split reviews from game?
    template_name = "review/review_list.html"
    paginate_by = 30

    def get_queryset(self):
        return Game.objects.get_latest_reviews()
