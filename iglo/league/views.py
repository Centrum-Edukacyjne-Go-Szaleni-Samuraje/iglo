from django.views.generic import ListView, DetailView

from league.models import Season, Group


class SeasonsListView(ListView):
    model = Season


class SeasonDetailView(DetailView):
    model = Season


class GroupDetailView(DetailView):
    model = Group
