from django.db.models import Q
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
        queryset = Game.objects.get_latest_reviews()
        groups = self.request.GET.get("groups")
        if groups:
            groups = list(groups.upper())
            queryset = queryset.filter(group__name__in=groups)
        teacher = self.request.GET.get("teacher")
        if teacher:
            queryset = queryset.filter(
                Q(group__teacher__first_name__icontains=teacher) |
                Q(group__teacher__last_name__icontains=teacher)
            )
        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        return super().get_context_data(object_list=object_list, **kwargs) | {
            "groups": self.request.GET.get("groups", ""),
            "teacher": self.request.GET.get("teacher", "")
        }
