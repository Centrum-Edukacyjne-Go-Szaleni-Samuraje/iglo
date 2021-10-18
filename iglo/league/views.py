from django.views.generic import ListView, DetailView

from league.models import Season, Group, Game


class SeasonsListView(ListView):
    model = Season


class SeasonDetailView(DetailView):
    model = Season

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        return queryset.get(number=self.kwargs["number"])


class GroupDetailView(DetailView):
    model = Group

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        return queryset.get(
            season__number=self.kwargs["season_number"], name=self.kwargs["group_name"]
        )


class GameDetailView(DetailView):
    model = Game

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        return queryset.get(
            group__season__number=self.kwargs["season_number"],
            group__name=self.kwargs["group_name"],
            black__player__nick=self.kwargs["black_player"],
            white__player__nick=self.kwargs["white_player"],
        )
