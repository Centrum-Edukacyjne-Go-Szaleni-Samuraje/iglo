import datetime

from django.contrib import messages
from django.db.models import Q
from django.views.generic import ListView, DetailView, FormView, UpdateView

from league.forms import PrepareSeasonForm, GameResultUpdateForm
from league.models import Season, Group, Game, Player, SeasonState
from league.permissions import AdminPermissionRequired, AdminPermissionForModifyRequired


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
        today = datetime.date.today()
        return super().get_context_data(**kwargs) | {
            "memberships": self.object.memberships.order_by("-group__season__number"),
            "current_game": Game.objects.filter(
                Q(white__player=self.object) | Q(black__player=self.object)
            )
            .filter(winner__isnull=True)
            .earliest("round__number"),
        }


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
