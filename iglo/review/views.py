from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

from review.models import Teacher


class TeacherListView(ListView):
    model = Teacher

    def get_queryset(self):
        return super().get_queryset().order_by("first_name", "last_name")


class TeacherDetailView(DetailView):
    model = Teacher

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        return get_object_or_404(
            queryset,
            first_name__iexact=self.kwargs["first_name"],
            last_name__iexact=self.kwargs["last_name"],
        )
