from django.views.generic import DetailView, ListView

from review.models import Teacher


class TeacherListView(ListView):
    model = Teacher

    def get_queryset(self):
        return super().get_queryset().order_by("first_name", "last_name")


class TeacherDetailView(DetailView):
    model = Teacher
