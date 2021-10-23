from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, FormView

from league.forms import PlayerSettingsForm, PrepareSeasonForm
from league.models import Season, Group, Game, Player, Account, GameServer


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


class PlayerSettingsView(LoginRequiredMixin, FormView):
    template_name = "league/player_settings.html"
    form_class = PlayerSettingsForm
    success_url = reverse_lazy("player-settings")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_player = Player.objects.get(user=self.request.user)
        context['nick'] = current_player.nick
        context['rank'] = current_player.rank
        try:
            ogs_account = Account.objects.get(player=current_player, server=GameServer.OGS)
            context['nick_ogs'] = ogs_account.name
        except ObjectDoesNotExist:
            pass
        try:
            kgs_account = Account.objects.get(player=current_player, server=GameServer.KGS)
            context['nick_kgs'] = kgs_account.name
        except ObjectDoesNotExist:
            pass
        return context

    def form_valid(self, form):
        current_player = Player.objects.get(user=self.request.user)
        if new_nick := form.cleaned_data['nick']:
            current_player.nick = new_nick
        if new_rank := form.cleaned_data['rank']:
            current_player.rank = new_rank
        current_player.save()

        if new_ogs_nick := form.cleaned_data.get('nick_ogs'):
            ogs_account, _ = Account.objects.get_or_create(player=current_player, server=GameServer.OGS)
            ogs_account.name = new_ogs_nick
            ogs_account.save()
        if new_kgs_nick := form.cleaned_data.get('nick_kgs'):
            kgs_account, _ = Account.objects.get_or_create(player=current_player, server=GameServer.KGS)
            kgs_account.name = new_kgs_nick
            kgs_account.save()

        if any(form.cleaned_data.values()):
            messages.add_message(
                self.request,
                messages.SUCCESS,
                "Twoje dane zostały zmienione.",
            )
        return super().form_valid(form)

      
class PrepareSeasonView(FormView):
    template_name = "league/season_prepare.html"
    form_class = PrepareSeasonForm

    def form_valid(self, form):
        self.object = Season.objects.prepare_season(
            start_date=form.cleaned_data["start_date"],
            players_per_group=form.cleaned_data["players_per_group"],
            promotion_count=form.cleaned_data["promotion_count"],
        )
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.get_absolute_url()
