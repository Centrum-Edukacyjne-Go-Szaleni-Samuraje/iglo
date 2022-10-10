import csv
import datetime

from django.conf import settings
from django.contrib import messages
from django.db.models import Count, Exists, OuterRef
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views import View
from django.views.generic import ListView, DetailView, FormView, UpdateView, RedirectView, TemplateView
from django.views.generic.detail import SingleObjectMixin

from accounts.models import UserRole
from league import texts, tasks
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
    AlreadyPlayedGamesError,
)
from league.models import SeasonState
from league.permissions import (
    AdminPermissionRequired,
    UserRoleRequiredForModify,
    UserRoleRequired,
)
from league.utils.egd import create_tournament_table, DatesRange, Player as EGDPlayer, Game as EGDGame, gor_to_rank


class SeasonsListView(ListView):
    model = Season
    paginate_by = 10

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        return context | {"can_prepare_season": not Season.objects.exclude(state=SeasonState.FINISHED).exists()}

    def get_queryset(self):
        return super().get_queryset().annotate(number_of_players=Count("groups__members")).order_by("-number")


class SeasonDetailView(UserRoleRequiredForModify, DetailView):
    model = Season
    required_roles = [UserRole.REFEREE]

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        return get_object_or_404(
            queryset.prefetch_related("groups__members__player", "groups__teacher"),
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
            headers={"Content-Disposition": f'attachment; filename="season-{number}.csv"'},
        )
        writer = csv.DictWriter(
            f=response,
            fieldnames=[
                "nick",
                "name",
                "rank",
                "email",
                "auto_join",
                "egd_approval",
                "egd_profile",
                "group",
                "season_rank",
            ],
        )
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
                    "rank": member.player.rank,
                    "email": member.player.user.email if member.player.user else "",
                    "auto_join": member.player.auto_join,
                    "egd_approval": member.player.egd_approval,
                    "egd_profile": member.player.get_egd_profile_url(),
                    "group": member.group.name,
                    "season_rank": member.rank,
                }
            )
        return response


class GroupObjectMixin(SingleObjectMixin):
    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        return get_object_or_404(
            queryset.prefetch_related(
                "rounds__games__white__player",
                "rounds__games__black__player",
                "rounds__games__winner__player",
                "rounds__games__group__season",
                "members__player",
                "teacher",
            ).annotate(
                all_games_finished=~Exists(Game.objects.filter(group=OuterRef("id"), win_type__isnull=True)),
                rounds_number=Count("rounds", distinct=True),
            ),
            season__number=self.kwargs["season_number"],
            name__iexact=self.kwargs["group_name"],
        )


class GroupDetailView(UserRoleRequiredForModify, GroupObjectMixin, DetailView):
    model = Group
    required_roles = [UserRole.REFEREE]

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
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
        return super().get(request, *args, **kwargs)


class GroupEGDExportView(UserRoleRequired, GroupObjectMixin, DetailView):
    model = Group
    required_roles = [UserRole.REFEREE]

    def get(self, request, *args, **kwargs):
        group = self.get_object()
        if not group.all_games_finished:
            raise Http404()
        filename = f"iglo_season_{group.season.number}_group_{group.name}.txt"
        response = HttpResponse(
            content_type="text/plain",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
        member_id_to_egd_player = {
            member.id: EGDPlayer(
                first_name=member.player.first_name,
                last_name=member.player.last_name,
                rank=gor_to_rank(member.rank),
                country=member.player.country.code,
                club=member.player.club,
                pin=member.player.egd_pin or "",
            )
            for member in group.members_qualification
        }
        data = create_tournament_table(
            klass=settings.EGD_SETTINGS["CLASS"],
            name=settings.EGD_SETTINGS["NAME"].format(season_number=group.season.number, group_name=group.name),
            location=settings.EGD_SETTINGS["LOCATION"],
            dates=DatesRange(
                start=group.season.start_date,
                end=group.season.end_date,
            ),
            handicap=None,
            komi=settings.EGD_SETTINGS["KOMI"],
            time_limit=settings.EGD_SETTINGS["TIME_LIMIT"],
            players=list(member_id_to_egd_player.values()),
            rounds=[
                [
                    EGDGame(
                        white=member_id_to_egd_player[game.white.id] if game.white else None,
                        black=member_id_to_egd_player[game.black.id] if game.black else None,
                        winner=member_id_to_egd_player[game.winner.id] if game.winner else None,
                    )
                    for game in round.games.all()
                ]
                for round in group.rounds.all()
            ],
        )
        response.write(data)
        return response


class GameDetailRedirectView(RedirectView):
    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        if "bye_player" in kwargs.keys():
            return reverse(
                "bye-game-detail",
                kwargs=kwargs,
            )
        return reverse(
            "game-detail",
            kwargs=kwargs,
        )


class GameDetailView(DetailView):
    model = Game

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        queryset = queryset.select_related("white__player", "black__player")
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
            and game.is_editable_by_player
        )

    def get_form_class(self):
        if self.request.user.has_role(UserRole.REFEREE):
            return GameResultUpdateRefereeForm
        if self.request.user.has_role(UserRole.TEACHER):
            game = self.get_object()
            if hasattr(self.request.user, "player") and game.is_participant(self.request.user.player):
                return GameResultUpdateForm
            return GameResultUpdateTeacherForm
        return GameResultUpdateForm


class PlayersListView(ListView):
    model = Player
    paginate_by = 30

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .filter(memberships__isnull=False)
            .annotate(seasons=Count("memberships"))
            .order_by("-seasons", "-rank", "nick")
            .distinct()
        )
        keyword = self.request.GET.get("keyword")
        if keyword:
            queryset = queryset.filter(nick__icontains=keyword)
        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        return super().get_context_data(object_list=object_list, **kwargs) | {
            "keyword": self.request.GET.get("keyword", "")
        }


class PlayerDetailView(UserRoleRequiredForModify, DetailView):
    model = Player
    slug_field = "nick__iexact"
    required_roles = [UserRole.REFEREE]

    def get_context_data(self, **kwargs):
        current_membership = Member.objects.get_current_membership(player=self.object)
        memberships = self.object.memberships.order_by("-group__season__number").select_related("group__season")
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

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        current_membership = Member.objects.get_current_membership(player=self.object)
        if "action-withdraw" in request.POST and current_membership:
            try:
                current_membership.withdraw()
                messages.add_message(
                    self.request,
                    messages.SUCCESS,
                    texts.MEMBER_WITHDRAW_SUCCESS,
                )
            except AlreadyPlayedGamesError:
                messages.add_message(
                    self.request,
                    messages.WARNING,
                    texts.ALREADY_PLAYED_GAMES_ERROR,
                )
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


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


class LeagueAdminView(TemplateView, UserRoleRequired):
    template_name = "league/league_admin.html"
    required_roles = [UserRole.TEACHER]

    def post(self, request, *args, **kwargs):
        if "action-update-gor" in request.POST:
            tasks.update_gor.delay(triggering_user_email=self.request.user.email)
            messages.add_message(
                request=request,
                level=messages.SUCCESS,
                message=texts.UPDATE_GOR_MESSAGE,
            )
        context = self.get_context_data()
        return self.render_to_response(context)


class GameListView(ListView):
    model = Game
    paginate_by = 30

    def get_queryset(self):
        queryset = Game.objects.get_latest_finished()
        groups = self.request.GET.get("groups")
        if groups:
            groups = list(groups.upper())
            queryset = queryset.filter(group__name__in=groups)
        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        return super().get_context_data(object_list=object_list, **kwargs) | {
            "groups": self.request.GET.get("groups", "")
        }


class UpcomingGameListView(ListView):
    model = Game
    template_name = "league/upcoming_games_list.html"
    paginate_by = 30

    def get_queryset(self):
        queryset = Game.objects.get_upcoming_games()
        groups = self.request.GET.get("groups")
        if groups:
            groups = list(groups.upper())
            queryset = queryset.filter(group__name__in=groups)
        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        return super().get_context_data(object_list=object_list, **kwargs) | {
            "groups": self.request.GET.get("groups", "")
        }
