import datetime

from django.views.generic import ListView, DetailView, FormView

from league.forms import PrepareSeasonForm
from league.models import Season, Group, Game, Player
from league.permissions import AdminPermissionRequired


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


class PlayerDetailView(DetailView):
    model = Player
    slug_field = "nick"


class PrepareSeasonView(AdminPermissionRequired, FormView):
    template_name = "league/season_prepare.html"
    form_class = PrepareSeasonForm

    DEFAULT_PROMOTION_COUNT = 2
    DEFAULT_PLAYERS_PER_GROUP = 6

    def form_valid(self, form):
        self.object = Season.objects.prepare_season(
            start_date=form.cleaned_data["start_date"],
            players_per_group=form.cleaned_data["players_per_group"],
            promotion_count=form.cleaned_data["promotion_count"],
        )
        return super().form_valid(form)

    def get_initial(self):
        return {
            "start_date": datetime.date.today(),
            "promotion_count": self.DEFAULT_PROMOTION_COUNT,
            "players_per_group": self.DEFAULT_PLAYERS_PER_GROUP,
        }

    def get_success_url(self):
        return self.object.get_absolute_url()
