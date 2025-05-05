import csv
import datetime

from django.conf import settings
from django.contrib import messages
from django.db.models import Count, Exists, OuterRef, Q
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import ListView, DetailView, FormView, UpdateView, RedirectView, TemplateView
from django.views.generic.detail import SingleObjectMixin

from accounts.models import UserRole
from league import texts, tasks
from league.models import PairingType
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
    GroupType,
    WrongSeasonStateError,
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
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['SEASON_REVERT_TO_DRAFT_CONFIRM'] = texts.SEASON_REVERT_TO_DRAFT_CONFIRM
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        if "action-start-season" in request.POST:
            self.object.start()
        elif "action-reset-groups" in request.POST:
            self.object.reset_groups(use_igor=False)
        elif "action-reset-groups-igor" in request.POST:
            self.object.reset_groups(use_igor=True)
        elif "action-finish-season" in request.POST:
            try:
                self.object.finish()
            except GamesWithoutResultError:
                messages.add_message(
                    request=request,
                    level=messages.WARNING,
                    message=texts.GAMES_WITHOUT_RESULT_ERROR,
                )
        elif "action-revert-to-draft" in request.POST:
            # Only admins can revert a season to draft
            if not request.user.is_admin:
                messages.add_message(
                    request=request,
                    level=messages.ERROR,
                    message=texts.SEASON_REVERT_TO_DRAFT_ADMIN_ONLY,
                )
            else:
                try:
                    self.object.revert_to_draft()
                    messages.add_message(
                        request=request,
                        level=messages.SUCCESS,
                        message=texts.SEASON_REVERT_TO_DRAFT_SUCCESS,
                    )
                except GamesWithoutResultError:
                    messages.add_message(
                        request=request,
                        level=messages.ERROR,
                        message=texts.SEASON_REVERT_TO_DRAFT_ERROR,
                    )
                except WrongSeasonStateError:
                    messages.add_message(
                        request=request,
                        level=messages.ERROR,
                        message=texts.SEASON_REVERT_TO_DRAFT_WRONG_STATE,
                    )
        return self.render_to_response(context)


class SeasonDeleteView(UserRoleRequired, TemplateView):
    template_name = "league/season_delete_confirm.html"
    required_roles = [UserRole.REFEREE]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["season"] = get_object_or_404(Season, number=self.kwargs["number"])
        if context["season"].state != SeasonState.DRAFT:
            raise Http404("Only draft seasons can be deleted")
        return context

    def post(self, request, *args, **kwargs):
        season = get_object_or_404(Season, number=self.kwargs["number"])
        if season.state != SeasonState.DRAFT:
            raise Http404("Only draft seasons can be deleted")

        # Store the number for the success message
        season_number = season.number

        # Delete the season
        season.delete()

        messages.success(request, texts.SEASON_DELETE_SUCCESS.format(season_number))
        return redirect("seasons-list")


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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # If we're in the draft state, get previous positions from the last season
        if self.object.season.state == SeasonState.DRAFT:
            context['prev_positions'] = self.get_previous_positions()
            
        return context
    
    def get_previous_positions(self):
        """Get the positions of players from the last finished season's banded group."""
        try:
            # Get the last season (excluding current one)
            last_season = Season.objects.filter(
                number__lt=self.object.season.number,
                state=SeasonState.FINISHED
            ).order_by('-number').first()
            
            if not last_season:
                return {}
                
            # Find the banded group in the last season, if any
            banded_group = Group.objects.filter(
                season=last_season,
                type=GroupType.BANDED
            ).first()
            
            if not banded_group:
                return {}
                
            # Create a dictionary with player_id -> position for all members with final_order
            positions = {}
            for member in Member.objects.filter(
                group=banded_group
            ).select_related('player').order_by('final_order'):
                if member.final_order is not None:
                    positions[member.player.id] = member.final_order
                    
            return positions
            
        except Exception:
            # Return empty dict if any errors occur
            return {}

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        # No need to recalculate scores here - it will be done when season starts
        if "action-move-to-position" in request.POST:
            try:
                member_id = int(request.POST["member_id"])
                target_position = int(request.POST["target_position"])

                member = self.object.members.get(id=member_id)
                current_position = member.order

                # Calculate the position delta
                position_delta = target_position - current_position

                # Only apply if there's an actual change
                if position_delta != 0:
                    self.object.move_member(member_id=member_id, positions=position_delta)
            except (ValueError, KeyError, Member.DoesNotExist):
                # Handle potential errors gracefully
                pass
        elif "action-delete" in request.POST:
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
                    texts.MISSING_PLAYER_ERROR,
                )
        elif "action-pairing" in request.POST:
            self.object.start_macmahon_round()
        return super().get(request, *args, **kwargs)


class GroupGamesView(UserRoleRequiredForModify, GroupObjectMixin, DetailView):
    model = Group
    required_roles = [UserRole.REFEREE]
    template_name = 'league/group_games.html'
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if "action-pairing" in request.POST:
            self.object.start_macmahon_round()
        return super().get(request, *args, **kwargs)


class GroupAllGamesView(GroupObjectMixin, DetailView):
    model = Group
    template_name = 'league/group_all_games.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all games from the group and exclude byes
        games = Game.objects.filter(group=self.object).exclude(win_type=WinType.BYE).select_related('assigned_teacher')
        
        # Custom sort by initial order of both players, higher player first
        games = sorted(games, key=lambda game: (
            min(game.black.order, game.white.order),
            max(game.black.order, game.white.order)
        ))
        
        context['all_games'] = games
        
        # Generate options for grouping dropdown based on number of games
        game_count = len(games)
        group_options = list(range(1, game_count + 1))  # All possible options
        context['group_options'] = group_options
        
        # Get all teachers for dropdown selection
        from review.models import Teacher
        context['available_teachers'] = Teacher.objects.all().order_by('first_name', 'last_name')
        
        # Add success/error messages from session
        context['teacher_assignment_success'] = self.request.session.pop('teacher_assignment_success', False)
        context['teacher_assignment_count'] = self.request.session.pop('teacher_assignment_count', None)
        context['individual_update_success'] = self.request.session.pop('individual_update_success', False)
        context['individual_updated_game_id'] = self.request.session.pop('individual_updated_game_id', None)
        
        # Error messages
        context['permission_error'] = self.request.session.pop('permission_error', False)
        context['json_error'] = self.request.session.pop('json_error', False)
        context['error'] = self.request.session.pop('error', False)
        
        return context
        
    def post(self, request, *args, **kwargs):
        """Handle teacher assignment submission for games in a group.
        
        This method processes teacher assignments from group-based or individual selections.
        Only users with admin, staff, or referee roles can modify teacher assignments.
        """
        import json
        from django.db import transaction
        from review.models import Teacher
        from accounts.models import UserRole
        
        # Check permissions - only admin/staff/referee can modify teacher assignments
        if not (request.user.is_admin or request.user.is_staff or request.user.has_role(UserRole.REFEREE)):
            request.session['permission_error'] = True
            return self.get(request, *args, **kwargs)
        
        self.object = self.get_object()
        
        # Check for game_ids and teacher_ids arrays in form data
        game_ids = request.POST.getlist('game_ids[]')
        teacher_ids = request.POST.getlist('teacher_ids[]')
        
        if not game_ids or len(game_ids) != len(teacher_ids):
            request.session['error'] = True
            return self.get(request, *args, **kwargs)
        
        try:
            # Get all unique teacher IDs for bulk lookup
            unique_teacher_ids = set(filter(None, teacher_ids))
            teachers = Teacher.objects.filter(id__in=unique_teacher_ids)
            teachers_dict = {str(t.id): t for t in teachers}
            
            # Process assignments and prepare bulk update
            games_to_update = []
            updated_game_id = None
            
            # Use a transaction to ensure all updates succeed or fail together
            with transaction.atomic():
                # Create a dictionary of existing assignments for comparison
                existing_assignments = {}
                games = Game.objects.filter(id__in=game_ids, group=self.object).select_related('assigned_teacher')
                for game in games:
                    existing_assignments[str(game.id)] = game.assigned_teacher.id if game.assigned_teacher else None
                
                # Process each game-teacher pair
                for i, game_id in enumerate(game_ids):
                    if i >= len(teacher_ids):
                        break
                        
                    teacher_id = teacher_ids[i]
                    
                    try:
                        # Find the game
                        game = games.get(id=game_id)
                        
                        # Skip if assignment hasn't changed
                        current_teacher_id = existing_assignments.get(str(game_id))
                        if (current_teacher_id is None and not teacher_id) or (current_teacher_id and str(current_teacher_id) == teacher_id):
                            continue
                        
                        if teacher_id:
                            # Get the teacher from our dictionary
                            teacher = teachers_dict.get(teacher_id)
                            if teacher:
                                # Update game with teacher
                                game.assigned_teacher = teacher
                                games_to_update.append(game)
                                updated_game_id = game_id
                        else:
                            # Remove teacher assignment if teacher_id is empty
                            game.assigned_teacher = None
                            games_to_update.append(game)
                            updated_game_id = game_id
                            
                    except Game.DoesNotExist:
                        # Skip games that don't exist
                        continue
                
                # Bulk update all games at once
                if games_to_update:
                    Game.objects.bulk_update(games_to_update, ['assigned_teacher'])
                    num_updates = len(games_to_update)
                    
                    # Check if this is an individual update
                    if request.POST.get('individual_update') == 'true' and updated_game_id:
                        request.session['individual_update_success'] = True
                        request.session['individual_updated_game_id'] = updated_game_id
                    else:
                        request.session['teacher_assignment_success'] = True
                        request.session['teacher_assignment_count'] = num_updates
        except Exception as e:
            # Handle other unexpected errors
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error updating teacher assignments: {str(e)}")
            request.session['error'] = True
        
        # Redirect back to same page to avoid form resubmission
        return redirect('group-all-games', 
                       season_number=self.object.season.number, 
                       group_name=self.object.name)


class GroupEGDExportView(UserRoleRequired, GroupObjectMixin, DetailView):
    model = Group
    required_roles = [UserRole.REFEREE]

    def get(self, request, *args, **kwargs):
        group = self.get_object()
        if not group.all_games_finished:
            raise Http404()

        # Get all EGD-eligible games that have been played
        egd_eligible_games = []
        for round in group.rounds.all():
            for game in round.games.all():
                # For export, we need both EGD eligibility AND the game must be played
                if game.is_egd_eligible and game.is_played and game.win_type != WinType.NOT_PLAYED:
                    egd_eligible_games.append(game)

        # If no games are eligible, create an informational response
        if not egd_eligible_games:
            filename = f"iglo_season_{group.season.number}_group_{group.name}_egd_info.txt"
            response = HttpResponse(
                content_type="text/plain",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )
            response.write("No EGD eligible games found in this group.\n\n")
            response.write("For a game to be eligible for EGD export, both players must have enabled EGD reporting in their settings.\n")
            return response

        # Get all unique players from eligible games
        member_ids = set()
        for game in egd_eligible_games:
            if game.black:
                member_ids.add(game.black.id)
            if game.white:
                member_ids.add(game.white.id)

        filename = f"iglo_season_{group.season.number}_group_{group.name}_egd.txt"
        response = HttpResponse(
            content_type="text/plain",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

        # Create EGD player data only for players with eligible games
        members = Member.objects.filter(id__in=member_ids).select_related('player')

        # Check for players with missing rank or EGD PIN
        players_without_rank = []
        players_without_pin = []

        for member in members:
            if member.rank is None:
                players_without_rank.append(f"{member.player.first_name} {member.player.last_name}")
            if not member.player.egd_pin:
                players_without_pin.append(f"{member.player.first_name} {member.player.last_name}")

        # Prepare error information if needed
        has_errors = bool(players_without_rank or players_without_pin)
        if has_errors:
            filename = f"iglo_season_{group.season.number}_group_{group.name}_egd_error.txt"
            response = HttpResponse(
                content_type="text/plain",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )
            response.write("Cannot generate EGD export: Missing required player information.\n\n")

            if players_without_rank:
                response.write("The following players need ranks assigned:\n")
                for player in players_without_rank:
                    response.write(f"- {player}\n")
                response.write("\n")

            if players_without_pin:
                response.write("The following players need EGD PINs assigned:\n")
                for player in players_without_pin:
                    response.write(f"- {player}\n")
                response.write("\n")

            response.write("Please update this information in the admin panel or fetch data from the EGD website.")
            response.write("\nPlayers can find their EGD PINs at: https://www.europeangodatabase.eu/EGD/")
            return response

        member_id_to_egd_player = {
            member.id: EGDPlayer(
                first_name=member.player.first_name,
                last_name=member.player.last_name,
                rank=gor_to_rank(member.rank),
                country=member.player.country.code,
                club=member.player.club,
                pin=member.player.egd_pin or "",
            )
            for member in members
        }

        # Organize games by round
        rounds_data = []
        current_round = None
        current_round_games = []

        for game in sorted(egd_eligible_games, key=lambda g: g.round.number):
            if current_round != game.round.number:
                if current_round is not None:
                    rounds_data.append(current_round_games)
                current_round = game.round.number
                current_round_games = []

            current_round_games.append(
                EGDGame(
                    white=member_id_to_egd_player[game.white.id] if game.white else None,
                    black=member_id_to_egd_player[game.black.id] if game.black else None,
                    winner=member_id_to_egd_player[game.winner.id] if game.winner else None,
                )
            )

        # Add the last round
        if current_round_games:
            rounds_data.append(current_round_games)

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
            rounds=rounds_data,
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
        tasks.recalculate_igor.delay()
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
        players_igor = self.object.igor_history
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
            "players_igor": players_igor
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
    DEFAULT_USE_IGOR = True

    def form_valid(self, form):
        pairing_type = form.cleaned_data["pairing_type"]
        band_size = form.cleaned_data.get("band_size", 2)
        point_difference = form.cleaned_data.get("point_difference", 1.0)

        self.object = Season.objects.prepare_season(
            start_date=form.cleaned_data["start_date"],
            players_per_group=form.cleaned_data["players_per_group"],
            promotion_count=form.cleaned_data["promotion_count"],
            use_igor=form.cleaned_data["use_igor"],
            pairing_type=pairing_type,
            band_size=band_size,
            point_difference=point_difference
        )
        return super().form_valid(form)

    def get_initial(self):
        return {
            "start_date": datetime.date.today(),
            "promotion_count": self.DEFAULT_PROMOTION_COUNT,
            "players_per_group": self.DEFAULT_PLAYERS_PER_GROUP,
            "use_igor": self.DEFAULT_USE_IGOR,
            "point_difference": 1.0,
        }

    def get_success_url(self):
        return self.object.get_absolute_url()


class LeagueAdminView(TemplateView, UserRoleRequired):
    template_name = "league/league_admin.html"
    required_roles = [UserRole.TEACHER]

    def post(self, request, *args, **kwargs):
        triggering_user_email = self.request.user.email if hasattr(self.request.user, 'email') else None
        
        if "action-update-gor" in request.POST:
            tasks.update_gor.delay(triggering_user_email=triggering_user_email)
            messages.add_message(
                request=request,
                level=messages.SUCCESS,
                message=texts.UPDATE_GOR_MESSAGE,
            )
        elif "action-update-ogs" in request.POST:
            tasks.update_ogs_data.delay(triggering_user_email=triggering_user_email)
            messages.add_message(
                request=request,
                level=messages.SUCCESS,
                message=texts.UPDATE_OGS_MESSAGE,
            )
        elif "action-recalculate-igor" in request.POST:
            tasks.recalculate_igor.delay()
            messages.add_message(
                request=request,
                level=messages.SUCCESS,
                message="IGoR jest przeliczany. To może zająć kilka minut.",
            )
        context = self.get_context_data()
        return self.render_to_response(context)


class GameListView(ListView):
    model = Game
    paginate_by = 30

    def get_queryset(self):
        queryset = Game.objects.get_latest_finished()
        seasons = self.request.GET.get("seasons")
        if seasons:
            seasons = (int(s) for s in seasons.split() if s.isdigit())
            queryset = queryset.filter(group__season__number__in=seasons)
        groups = self.request.GET.get("groups")
        if groups:
            groups = list(groups.upper())
            queryset = queryset.filter(group__name__in=groups)
        player = self.request.GET.get("player")
        if player:
            queryset = queryset.filter(
                Q(black__player__nick__icontains=player) |
                Q(white__player__nick__icontains=player)
            )
        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        return super().get_context_data(object_list=object_list, **kwargs) | {
            "seasons": self.request.GET.get("seasons", ""),
            "groups": self.request.GET.get("groups", ""),
            "player": self.request.GET.get("player", "")
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
