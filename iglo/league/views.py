import csv
import datetime

from django.contrib import messages

from django.db.models import Q, Count, Exists, OuterRef
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView, FormView, UpdateView

from accounts.models import UserRole
from league import texts
from league.forms import (
    GameResultUpdateForm,
    PlayerUpdateForm,
    GameResultUpdateRefereeForm,
    GameResultUpdateTeacherForm,
)
from league.forms import PrepareSeasonForm
from league.models import (
    Season,
    Group,
    Game,
    Player,
    Member,
    GamesWithoutResultError,
    WinType,
)
from league.models import SeasonState
from league.permissions import (
    AdminPermissionRequired,
    UserRoleRequiredForModify,
    UserRoleRequired,
)


class SeasonsListView(ListView):
    model = Season
    paginate_by = 10

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        return context | {
            "can_prepare_season": not Season.objects.exclude(
                state=SeasonState.FINISHED
            ).exists()
        }

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(number_of_players=Count("groups__members"))
            .order_by("-number")
        )


class SeasonDetailView(UserRoleRequiredForModify, DetailView):
    model = Season
    required_roles = [UserRole.REFEREE]

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        return get_object_or_404(
            queryset.prefetch_related("groups__members__player"),
            number=self.kwargs["number"],
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        if "action-start-season" in request.POST:
            self.object.start()
        elif "action-reset-groups" in request.POST:
            self.object.reset_groups()
        elif "action-finish-season" in request.POST:
            try:
                self.object.finish()
            except GamesWithoutResultError:
                messages.add_message(
                    request=request,
                    level=messages.WARNING,
                    message=texts.GAMES_WITHOUT_RESULT_ERROR,
                )
        return self.render_to_response(context)


class SeasonExportCSVView(UserRoleRequired, View):
    required_roles = [UserRole.REFEREE]

    def get(self, request, number):
        response = HttpResponse(
            content_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="season-{number}.csv"'
            },
        )
        writer = csv.DictWriter(response, fieldnames=["nick", "name", "group", "email", "auto_join", "egd_approval"])
        writer.writeheader()
        for member in (
            Member.objects.filter(group__season__number=number)
            .order_by("group__name", "order")
            .select_related("player__user", "group")
        ):
            writer.writerow(
                {
                    "nick": member.player.nick,
                    "name": f"{member.player.first_name} {member.player.last_name}",
                    "group": member.group.name,
                    "email": member.player.user.email if member.player.user else "",
                    "auto_join": member.player.auto_join,
                    "egd_approval": member.player.egd_approval,
                }
            )
        return response


class GroupDetailView(UserRoleRequiredForModify, DetailView):
    model = Group
    required_roles = [UserRole.REFEREE]

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        return get_object_or_404(
            queryset.prefetch_related(
                "rounds__games__white__player",
                "rounds__games__black__player",
                "rounds__games__winner__player",
                "members__player",
            ).annotate(
                all_games_finished=~Exists(Game.objects.filter(
                    group=OuterRef('id'),
                    win_type__isnull=True
                ))),
            season__number=self.kwargs["season_number"],
            name__iexact=self.kwargs["group_name"],
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        if "action-delete" in request.POST:
            self.object.delete_member(member_id=int(request.POST["member_id"]))
            self.object.set_initial_score()
        elif "action-up" in request.POST:
            self.object.move_member_up(member_id=int(request.POST["member_id"]))
            self.object.set_initial_score()
        elif "action-down" in request.POST:
            self.object.move_member_down(member_id=int(request.POST["member_id"]))
            self.object.set_initial_score()
        elif "action-add" in request.POST:
            try:
                self.object.add_member(player_nick=request.POST["player_nick"])
            except Player.DoesNotExist:
                messages.add_message(
                    self.request,
                    messages.WARNING,
                    texts.MISSING_PLAYER_ERROR,
                )
        elif "action-pairing" in request.POST:
            self.object.start_macmahon_round()
        return self.render_to_response(context)


class GameDetailView(DetailView):
    model = Game

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        if "bye_player" in self.kwargs:
            return get_object_or_404(
                queryset,
                group__season__number=self.kwargs["season_number"],
                group__name__iexact=self.kwargs["group_name"],
                winner__player__nick__iexact=self.kwargs["bye_player"],
                win_type=WinType.BYE,
            )
        return get_object_or_404(
            queryset,
            group__season__number=self.kwargs["season_number"],
            group__name__iexact=self.kwargs["group_name"],
            black__player__nick__iexact=self.kwargs["black_player"],
            white__player__nick__iexact=self.kwargs["white_player"],
        )


class GameUpdateView(UserRoleRequired, GameDetailView, UpdateView):
    model = Game
    required_roles = [UserRole.REFEREE, UserRole.TEACHER]

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
        game = self.get_object()  # TODO: this is not prefect
        return super().test_func() or (
            self.request.user.is_authenticated
            and hasattr(self.request.user, "player")
            and game.is_participant(self.request.user.player)
            and game.group.season.state == SeasonState.IN_PROGRESS
        )

    def get_form_class(self):
        if self.request.user.has_role(UserRole.REFEREE):
            return GameResultUpdateRefereeForm
        if self.request.user.has_role(UserRole.TEACHER):
            game = self.get_object()
            if hasattr(self.request.user, "player") and game.is_participant(
                self.request.user.player
            ):
                return GameResultUpdateForm
            return GameResultUpdateTeacherForm
        return GameResultUpdateForm


class PlayerDetailView(DetailView):
    model = Player
    slug_field = "nick__iexact"

    def get_context_data(self, **kwargs):
        current_membership = Member.objects.get_current_membership(player=self.object)
        memberships = self.object.memberships.order_by(
            "-group__season__number"
        ).select_related("group__season")
        if current_membership:
            current_games = Game.objects.get_for_member(member=current_membership)
            upcoming_game = Game.objects.get_upcoming_game(member=current_membership)
            memberships = memberships.exclude(id=current_membership.id)
        else:
            current_games = None
            upcoming_game = None
        return super().get_context_data(**kwargs) | {
            "current_membership": current_membership,
            "memberships": memberships,
            "current_games": current_games,
            "upcoming_game": upcoming_game,
        }


class PlayerUpdateView(AdminPermissionRequired, UpdateView):
    model = Player
    form_class = PlayerUpdateForm
    slug_field = "nick"

    def form_valid(self, form):
        messages.add_message(
            self.request,
            messages.SUCCESS,
            texts.PLAYER_UPDATE_SUCCESS,
        )
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.get_absolute_url()

    def test_func(self):
        return super().test_func() or (
            self.request.user.is_authenticated
            and self.request.user.player
            and self.request.user.player.nick == self.kwargs["slug"]
        )


class PrepareSeasonView(UserRoleRequired, FormView):
    template_name = "league/season_prepare.html"
    form_class = PrepareSeasonForm
    required_roles = [UserRole.REFEREE]

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


class TeachersListView(ListView):
    template_name = 'league/teachers_list.html'

    def get_queryset(self):
        season_number = self.kwargs['number']
        return Group.objects.filter(season__number=season_number, teacher__isnull=False).prefetch_related('teacher')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        season = Season.objects.get(number=self.kwargs['number'])
        context['season_number'] = season.number
        context['season_is_finished'] = season.state == SeasonState.FINISHED
        return context
