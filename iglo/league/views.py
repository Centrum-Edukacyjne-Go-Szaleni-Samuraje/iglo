import datetime

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, FormView, UpdateView
from league.permissions import AdminPermissionRequired, AdminPermissionForModifyRequired

from league.forms import GameResultUpdateForm
from league.forms import PlayerSettingsForm, PrepareSeasonForm
from league.models import Season, Group, Game, Player, Account, GameServer
from league.models import SeasonState


class SeasonsListView(ListView):
    model = Season

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        return context | {
            "draft_seasons_exists": Season.objects.filter(
                state=SeasonState.DRAFT.value
            ).exists()
        }


class SeasonDetailView(AdminPermissionForModifyRequired, DetailView):
    model = Season

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        return queryset.get(number=self.kwargs["number"])

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        if "action-delete-group" in request.POST:
            self.object.delete_group(group_id=int(request.POST["group_id"]))
        elif "action-add-group" in request.POST:
            self.object.add_group()
        elif "action-start-season" in request.POST:
            self.object.start()
        return self.render_to_response(context)


class GroupDetailView(AdminPermissionForModifyRequired, DetailView):
    model = Group

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        return queryset.get(
            season__number=self.kwargs["season_number"], name=self.kwargs["group_name"]
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        if "action-delete" in request.POST:
            self.object.delete_member(member_id=int(request.POST["member_id"]))
        elif "action-up" in request.POST:
            self.object.move_member_up(member_id=int(request.POST["member_id"]))
        elif "action-down" in request.POST:
            self.object.move_member_down(member_id=int(request.POST["member_id"]))
        elif "action-add" in request.POST:
            try:
                self.object.add_member(player_nick=request.POST["player_nick"])
            except Player.DoesNotExist:
                messages.add_message(
                    self.request,
                    messages.WARNING,
                    "Gracz o podanym nicku nie istnieje.",
                )
        return self.render_to_response(context)


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


class GameUpdateView(AdminPermissionRequired, GameDetailView, UpdateView):
    model = Game
    form_class = GameResultUpdateForm

    def get_success_url(self):
        return self.object.get_absolute_url()

    def form_valid(self, form):
        messages.add_message(
            request=self.request,
            level=messages.SUCCESS,
            message="Gra została zaktualizowana pomyślnie.",
        )
        return super().form_valid(form)

    def test_func(self):
        return super().test_func() or (
            self.request.user.is_authenticated
            and self.request.user.player
            and self.request.user.player.nick
            in [self.kwargs["black_player"], self.kwargs["white_player"]]
        )


class PlayerDetailView(DetailView):
    model = Player
    slug_field = "nick"

    def get_context_data(self, **kwargs):
        try:
            current_game = (
                Game.objects.filter(
                    Q(white__player=self.object) | Q(black__player=self.object)
                )
                .filter(winner__isnull=True)
                .earliest("round__number")
            )
        except Game.DoesNotExist:
            current_game = None
        return super().get_context_data(**kwargs) | {
            "memberships": self.object.memberships.order_by("-group__season__number"),
            "current_game": current_game,
        }


class PlayerSettingsView(FormView):
    template_name = "league/player_settings.html"
    form_class = PlayerSettingsForm
    success_url = reverse_lazy("player-settings")

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if not user.is_authenticated or not (user.is_staff or user.player.nick == kwargs['nick']):
            messages.add_message(
                self.request,
                messages.ERROR,
                "Nie posiadasz uprawnień do edycji tego konta.",
            )
            return redirect('/')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self):
        current_player = get_object_or_404(Player, nick=self.kwargs['nick'])
        context = super().get_context_data()
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
