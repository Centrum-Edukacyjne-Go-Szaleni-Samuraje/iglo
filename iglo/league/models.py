import datetime
import decimal
import math
import re
import string
from collections import defaultdict
from enum import Enum
from statistics import mean
from typing import Optional

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import F, Q, TextChoices, QuerySet, Avg, Count, Sum
from django.db.models.functions import Round as DjangoRound
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField

from league import texts
from league.utils.paring import round_robin, shuffle_colors, banded_round_robin, Bye
from macmahon import macmahon as mm

DAYS_PER_GAME = 7
NUMBER_OF_BARS = 2


class SeasonState(TextChoices):
    DRAFT = "draft", texts.SEASON_STATE_DRAFT
    IN_PROGRESS = "in_progress", texts.SEASON_STATE_IN_PROGRES
    FINISHED = "finished", texts.SEASON_STATE_FINISHED


class PairingType(TextChoices):
    DEFAULT = "default", texts.PAIRING_TYPE_DEFAULT
    BANDED = "banded", texts.PAIRING_TYPE_BANDED


class SeasonManager(models.Manager):
    def prepare_season(self, start_date: datetime.date, players_per_group: int, promotion_count: int,
                       use_igor: bool=False, pairing_type: str=PairingType.DEFAULT, band_size: int=2,
                       point_difference: float=1.0) -> "Season":
        previous_season = Season.objects.first()
        if previous_season and previous_season.state != SeasonState.FINISHED:
            raise ValueError(texts.PREVIOUS_SEASON_NOT_CLOSED_ERROR)
        season = self.create(
            state=SeasonState.DRAFT,
            number=previous_season.number + 1 if previous_season else 1,
            start_date=start_date,
            end_date=start_date + datetime.timedelta(days=(players_per_group - 1) * DAYS_PER_GAME - 1),
            promotion_count=promotion_count,
            players_per_group=players_per_group,
        )
        season.create_groups(use_igor=use_igor, pairing_type=pairing_type, band_size=band_size,
                            point_difference=point_difference)
        return season

    def get_latest(self) -> Optional["Season"]:
        return Season.objects.prefetch_related("groups").latest("number")


class WrongSeasonStateError(Exception):
    pass


class GamesWithoutResultError(Exception):
    pass


class Season(models.Model):
    number = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    promotion_count = models.SmallIntegerField()
    players_per_group = models.SmallIntegerField()
    state = models.CharField(max_length=16, choices=SeasonState.choices)

    objects = SeasonManager()

    class Meta:
        ordering = ["-number"]

    def __str__(self) -> str:
        return f"#{self.number} ({self.start_date} - {self.end_date})"

    def get_absolute_url(self):
        return reverse("season-detail", kwargs={"number": self.number})

    def start(self) -> None:
        self.validate_state(state=SeasonState.DRAFT)
        # First, calculate initial scores for each group based on its type
        for group in self.groups.all():
            if group.type == GroupType.MCMAHON:
                # McMahon groups - Use the MacMahon algorithm
                members = group.members.all()
                registered_players = [(member.player.nick, member.rank) for member in members]
                initial_ordering = mm.BasicInitialOrdering(number_of_bars=NUMBER_OF_BARS).order(registered_players)
                initial_ordering = {p.name: p for p in initial_ordering}
                for member in members:
                    ordered_player = initial_ordering[member.player.nick]
                    member.initial_score = ordered_player.initial_score
                Member.objects.bulk_update(members, ["initial_score"])
            elif group.type == GroupType.BANDED:
                # Banded group - Set scores based on position and point difference
                members = list(group.members.all())
                total_players = len(members)
                for member in members:
                    # Calculate points using the provided point difference
                    # First player (position 1) gets (total_players-1) * point_difference points
                    # Last player gets 0 points
                    base_points = (total_players - member.order) * group.point_difference
                    member.initial_score = base_points
                Member.objects.bulk_update(members, ["initial_score"])
            # Round Robin groups have default initial_score = 0, no need to set it

        # Now update the state and generate the pairings
        self.state = SeasonState.IN_PROGRESS
        self.save()

        for group in self.groups.all():
            members = list(group.members.all())
            current_date = self.start_date

            if group.type == GroupType.BANDED:
                pairing = banded_round_robin(player_count=len(members), band_size=group.band_size, add_byes=True)
            elif group.type == GroupType.MCMAHON:
                continue
            elif group.type == GroupType.ROUND_ROBIN:
                pairing = round_robin(n=len(members))
            else:
                raise ValueError(f"Unhandled group type: {group.type} - this should not happen")

            for round_number, round_pairs in enumerate(shuffle_colors(paring=pairing), start=1):
                round = Round.objects.create(
                    number=round_number,
                    group=group,
                    start_date=current_date,
                    end_date=current_date + datetime.timedelta(days=DAYS_PER_GAME - 1),
                )
                current_date += datetime.timedelta(days=DAYS_PER_GAME)

                for pair in round_pairs:
                    if isinstance(pair[0], Bye):
                        # We could implement it but it is not needed in Banded, because it always assigns player as black and shuffle skips byes.
                        raise ValueError("not implemented, should not happen.")
                    if group.type == GroupType.BANDED and isinstance(pair[1], Bye):
                        # Special player-with-result pair (player, bye_result) typically for the top and bottom players.
                        player = members[pair[0]]
                        bye_result = pair[1]

                        # Design choice: Create a BYE game with player as black and winner based on bye result.
                        # Note that this game will typically  provide a point depending whether ByeWin/ByeLoss.
                        Game.objects.create(
                            group=group,
                            round=round,
                            black=player,
                            white=None,
                            winner=player if bye_result == Bye.ByeWin else None,
                            win_type=WinType.BYE,
                            date=datetime.datetime.combine(round.end_date, settings.DEFAULT_GAME_TIME),
                        )
                    else:
                        game_members = [members[pair[0]], members[pair[1]]]
                        Game.objects.create(
                            group=group,
                            round=round,
                            black=game_members[0],
                            white=game_members[1],
                            date=datetime.datetime.combine(round.end_date, settings.DEFAULT_GAME_TIME),
                        )

    def finish(self) -> None:
        self.validate_state(state=SeasonState.IN_PROGRESS)
        if Game.objects.filter(group__season=self, win_type__isnull=True).exists():
            Game.objects.filter(group__season=self, win_type__isnull=True).update(win_type=WinType.NOT_PLAYED)
        for group in self.groups.all():
            for position, member in enumerate(group.members_qualification, start=1):
                member.final_order = position
                member.save()
        self.state = SeasonState.FINISHED
        self.save()

    def validate_state(self, state: SeasonState) -> None:
        if self.state != state:
            raise WrongSeasonStateError()

    def reset_groups(self, use_igor: bool, pairing_type: str=PairingType.DEFAULT, band_size: int=2,
                   point_difference: float=1.0) -> None:
        self.validate_state(state=SeasonState.DRAFT)
        self.groups.all().delete()
        self.create_groups(use_igor=use_igor, pairing_type=pairing_type, band_size=band_size,
                         point_difference=point_difference)

    def create_groups(self, use_igor: bool, pairing_type: str=PairingType.DEFAULT, band_size: int=2,
                      point_difference: float=1.0) -> None:
        self.validate_state(state=SeasonState.DRAFT)

        # Get the players
        if use_igor:
            players = Player.objects.filter(auto_join=True).order_by("-igor")
        else:
            try:
                previous_season = Season.objects.get(number=self.number - 1)
                players = previous_season.get_leaderboard()
                players = [player for player in players if player.auto_join]
            except Season.DoesNotExist:
                players = []
            players = self._redistribute_new_players(players=players, players_per_group=self.players_per_group)

        # Handle banded pairing type
        if pairing_type == PairingType.BANDED:
            group = Group.objects.create(
                name='A',
                season=self,
                type=GroupType.BANDED,
                is_egd=False,
                band_size=band_size,
                point_difference=point_difference,
            )
            group.save()

            # Add all players to the single group without setting initial scores
            # Initial scores will be calculated in the start() method
            members_to_create = []

            for player_order, player in enumerate(players, start=1):
                members_to_create.append(
                    Member(
                        group=group,
                        order=player_order,
                        player=player,
                        rank=player.rank,
                        egd_approval=player.egd_approval,  # Copy EGD approval from player
                        ogs_id=player.ogs_id,  # Copy OGS data from player
                        ogs_rating=player.ogs_rating,
                        ogs_deviation=player.ogs_deviation
                    )
                )

            # Bulk create all members at once
            members = Member.objects.bulk_create(members_to_create)
        else:
            # Default behavior - create multiple groups
            self._assign_players_to_groups(players=players)


    def get_leaderboard(self) -> list["Player"]:
        players = []
        for group in self.groups.order_by("name"):
            group_players = [member.player for member in group.members_qualification]
            players = (
                players[: -self.promotion_count]
                + group_players[: self.promotion_count]
                + players[-self.promotion_count :]
                + group_players[self.promotion_count :]
            )
        return players

    def _redistribute_new_players(self, players: list["Player"], players_per_group: int) -> list["Player"]:
        result = players[:]
        new_players = Player.objects.filter(auto_join=True).order_by("-rank").exclude(id__in=[p.id for p in result])
        added_to_group = defaultdict(int)
        for new_player in new_players:
            add_to_next = False
            previous_avg_rank = None
            for group_order in range(math.ceil(len(result) / players_per_group)):
                group_players = result[group_order * players_per_group : (group_order + 1) * players_per_group]
                avg_rank = mean(player.rank for player in group_players)
                if add_to_next and previous_avg_rank > avg_rank:
                    result.insert(group_order * players_per_group + added_to_group[group_order], new_player)
                    added_to_group[group_order] += 1
                    break
                if avg_rank < new_player.rank:
                    add_to_next = True
                previous_avg_rank = avg_rank
            else:
                result.append(new_player)
        return result

    def _assign_players_to_groups(self, players: list["Player"]) -> None:
        last_group = None
        for group_order in range(math.ceil(len(players) / self.players_per_group)):
            group_players = players[group_order * self.players_per_group : (group_order + 1) * self.players_per_group]
            # Note: is_egd is deprecated, we now check per-game eligibility
            # but we keep this for backward compatibility
            is_egd = all(p.egd_approval for p in group_players)
            if len(group_players) < max((self.players_per_group - 1), 2) and last_group:
                group = last_group
                group.type = GroupType.MCMAHON
                group.is_egd = group.is_egd and is_egd  # Deprecated - games are now eligible based on individual player approvals
                group.save()
            else:
                group = Group.objects.create(
                    name=string.ascii_uppercase[group_order],
                    season=self,
                    type=GroupType.ROUND_ROBIN,
                    is_egd=is_egd,  # Deprecated - games are now eligible based on individual player approvals
                )
                last_group = group
            for player_order, player in enumerate(group_players, start=group.members.count() + 1):
                Member.objects.create(
                    group=group,
                    order=player_order,
                    player=player,
                    rank=player.rank,
                    egd_approval=player.egd_approval,  # Copy EGD approval from player
                    ogs_id=player.ogs_id,  # Copy OGS data from player
                    ogs_rating=player.ogs_rating,
                    ogs_deviation=player.ogs_deviation
                )
            # Initial scores will be calculated during season start

    def get_groups(self):
        return (
            self.groups.select_related("teacher")
            .prefetch_related("members__player")
            .order_by("name")
            .annotate(
                members_count=Count("members"),
                supporters_count=Count("members", filter=Q(members__player__is_supporter=True)),
                avg_rank=DjangoRound(Avg("members__rank")),
            )
        )

    @cached_property
    def all_games_to_play(self) -> int:
        # Count actual total games instead of using a formula, excluding BYE games
        # This handles all group types correctly
        return Game.objects.filter(group__season=self).exclude(win_type=WinType.BYE).count()

    @cached_property
    def played_games(self) -> int:
        # Count all non-BYE games with a result
        return Game.objects.filter(
            group__season=self, 
            win_type__isnull=False
        ).exclude(win_type=WinType.BYE).count()

    @property
    def games_progress(self) -> int:
        if self.all_games_to_play == 0:
            return 0
        return int(100 * self.played_games / self.all_games_to_play)


class GameResult(Enum):
    WIN = "W"
    LOSE = "L"


class GroupType(models.TextChoices):
    ROUND_ROBIN = "round_robin", _("Każdy z każdym")
    MCMAHON = "mcmahon", _("McMahon")
    BANDED = "banded", _("Banded Round Robin")


class NotMcmahonGroupError(Exception):
    pass


class ResultSymbol(str, Enum):
    win = "+"
    lose = "-"
    not_played = "?"
    no_result = "X"

    def __str__(self):
        return str(self.value)


class Group(models.Model):
    name = models.CharField(max_length=1)
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name="groups")
    type = models.CharField(choices=GroupType.choices, max_length=16)
    is_egd = models.BooleanField(default=False, help_text="Deprecated. Games are now eligible for EGD export based on individual player approvals.")
    band_size = models.IntegerField(null=True, blank=True, help_text="Band size for banded round robin pairing")
    point_difference = models.FloatField(null=True, blank=True, help_text="Points difference between consecutive players in ranking", default=1.0)
    teacher = models.ForeignKey(
        "review.Teacher", null=True, on_delete=models.SET_NULL, related_name="groups", blank=True
    )

    class Meta:
        ordering = ["-season__number", "name"]

    def __str__(self) -> str:
        return f"{self.name} - season: {self.season}"

    def get_absolute_url(self):
        return reverse(
            "group-detail",
            kwargs={"season_number": self.season.number, "group_name": self.name},
        )

    @cached_property
    def results_table(self) -> list[tuple[int, "Member", list[tuple[str, str]]]]:
        members = self.members_qualification
        player_position = {member.player.nick: idx for idx, member in enumerate(members, start=1)}
        table = []
        for position, member in enumerate(members, start=1):
            games = Game.objects.get_for_member(member)
            records = []
            for game in games:
                opponent = game.get_opponent(member)
                if opponent:
                    opponent_position = player_position[opponent.player.nick]
                    if not game.is_played:
                        result_symbol = ResultSymbol.not_played
                    elif game.winner == member:
                        result_symbol = ResultSymbol.win
                    elif game.winner == opponent:
                        result_symbol = ResultSymbol.lose
                    else:
                        result_symbol = ResultSymbol.no_result
                    records.append((f"{opponent_position}{result_symbol}", game.get_absolute_url()))
                else:
                    records.append((f"0=", game.get_absolute_url()))
            table.append((position, member, records))
        return table

    @property
    def is_first(self) -> bool:
        return self.name == "A"

    @property
    def higher_group_name(self) -> Optional[str]:
        if self.is_first:
            return None
        return chr(ord(self.name) - 1)

    @property
    def lower_group_name(self) -> str:
        return chr(ord(self.name) + 1)

    @cached_property
    def latest_round(self) -> "Round":
        return self.rounds.order_by("-number").first()

    @cached_property
    def members_qualification(self) -> list["Member"]:
        members = list(self.members.select_related("player")
                       .prefetch_related("won_games__black", "won_games__white", "games_as_black", "games_as_white")
                       .all())

        # Note different sorting based on group type.
        if self.type == GroupType.ROUND_ROBIN:
            members.sort(key=lambda member: (
                member.final_order if member.final_order is not None else float('inf'),
                -member.points,
                -member.sodos,
                member.order
            ))
        elif self.type == GroupType.BANDED:
            members.sort(key=lambda member: (
                member.final_order if member.final_order is not None else float('inf'),
                -member.score,
                member.order
            ))
        else:
            members.sort(key=lambda member: (
                member.final_order if member.final_order is not None else float('inf'),
                -member.score,
                -member.sos,
                -member.sosos
            ))

        return members

    def delete_member(self, member_id: int) -> None:
        self.season.validate_state(state=SeasonState.DRAFT)
        member_to_remove = self.members.get(id=member_id)
        self.members.filter(order__gt=member_to_remove.order).update(order=F("order") - 1)
        member_to_remove.delete()

    def move_member(self, member_id: int, positions: int) -> None:
        """
        Move a member up or down by the specified number of positions.

        Args:
            member_id: The ID of the member to move
            positions: Number of positions to move (negative = up, positive = down)
        """
        self.season.validate_state(state=SeasonState.DRAFT)
        member = self.members.get(id=member_id)
        max_order = self.members.count()

        # Calculate new order position
        new_order = member.order + positions
        # Ensure it's within bounds
        new_order = max(1, min(max_order, new_order))

        # If no change needed, return early
        if new_order == member.order:
            return

        # Determine if we're moving up or down
        moving_up = new_order < member.order

        if moving_up:
            # Moving up: Get members that need to move down
            members_to_adjust = self.members.filter(
                order__gte=new_order,
                order__lt=member.order
            ).order_by('-order')

            # Move affected members down
            for other_member in members_to_adjust:
                other_member.order += 1
                other_member.save()
        else:
            # Moving down: Get members that need to move up
            members_to_adjust = self.members.filter(
                order__gt=member.order,
                order__lte=new_order
            ).order_by('order')

            # Move affected members up
            for other_member in members_to_adjust:
                other_member.order -= 1
                other_member.save()

        # Set member to new position
        member.order = new_order
        member.save()

    def move_member_up(self, member_id: int) -> None:
        """Move a member up by 1 position."""
        self.move_member(member_id, -1)

    def move_member_down(self, member_id: int) -> None:
        """Move a member down by 1 position."""
        self.move_member(member_id, 1)

    def add_member(self, player_nick: str) -> None:
        self.season.validate_state(state=SeasonState.DRAFT)
        player = Player.objects.get(nick__iexact=player_nick)
        try:
            current_group = self.season.groups.get(members__player=player)
            if current_group == self:
                return
            current_member = current_group.members.get(player=player)
            current_group.delete_member(member_id=current_member.id)
        except Group.DoesNotExist:
            pass
        Member.objects.create(
            group=self,
            player=player,
            rank=player.rank,
            order=self.members.count() + 1,
            egd_approval=player.egd_approval,
            ogs_id=player.ogs_id,
            ogs_rating=player.ogs_rating,
            ogs_deviation=player.ogs_deviation,
        )

    def swap_member(self, player_nick_to_remove: str, player_nick_to_add: str) -> None:
        member_to_remove = self.members.get(player__nick=player_nick_to_remove)
        self.members.filter(order__gt=member_to_remove.order).update(order=F("order") - 1)
        player_to_add = Player.objects.get(nick=player_nick_to_add)
        new_member = Member.objects.create(
            group=self,
            player=player_to_add,
            rank=player_to_add.rank,
            order=self.members.count(),
            egd_approval=player_to_add.egd_approval,
            ogs_id=player_to_add.ogs_id,
            ogs_rating=player_to_add.ogs_rating,
            ogs_deviation=player_to_add.ogs_deviation,
        )
        member_to_remove.games_as_white.update(white=new_member)
        member_to_remove.games_as_black.update(black=new_member)
        member_to_remove.delete()

    def validate_type(self, group_type: GroupType):
        if self.type != group_type:
            raise NotMcmahonGroupError()

    def start_macmahon_round(self):
        self.validate_type(GroupType.MCMAHON)
        if self.latest_round:
            self.latest_round.validate_is_completed()
            start_date = self.latest_round.end_date + datetime.timedelta(days=1)
            number = self.latest_round.number + 1
        else:
            start_date = self.season.start_date
            number = 1
        days_until_end_of_round = DAYS_PER_GAME - 1
        end_date = start_date + datetime.timedelta(days=days_until_end_of_round)

        new_round = Round.objects.create(group=self, number=number, start_date=start_date, end_date=end_date)

        players = self.get_macmahon_players()
        pairs, bye = mm.prepare_next_round(players)

        for pair in pairs:
            black = Member.objects.get(player__nick=pair.black.name, group=self)
            white = Member.objects.get(player__nick=pair.white.name, group=self)
            Game.objects.create(
                group=self,
                round=new_round,
                black=black,
                white=white,
                date=datetime.datetime.combine(new_round.end_date, settings.DEFAULT_GAME_TIME),
            )
        if bye:
            Game.objects.create_bye_game(self, new_round, Member.objects.get(player__nick=bye.name, group=self))

    def get_macmahon_players(self):
        members = Member.objects.filter(group=self).prefetch_related("player").all()
        players = []
        for member in members:
            player = mm.Player(
                name=member.player.nick,
                rating=member.rank,
                initial_score=member.initial_score,
            )
            games = Game.objects.filter(Q(white=member) | Q(black=member) | Q(winner=member)).all()
            for game in games:
                if game.is_bye:
                    player.games.append(mm.GameRecord("", mm.Color.BYE, mm.ResultType.BYE))
                elif game.is_played:
                    opponent = game.get_opponent(member).player.nick
                    color = mm.Color.BLACK if game.black == member else mm.Color.WHITE
                    result = mm.ResultType.WIN if game.winner == member else mm.ResultType.LOSE
                    player.games.append(mm.GameRecord(opponent, color, result))
            players.append(player)
        return players


class Player(models.Model):
    nick = models.CharField(max_length=32, unique=True)
    first_name = models.CharField(max_length=32)
    last_name = models.CharField(max_length=32)
    user = models.OneToOneField("accounts.User", null=True, on_delete=models.SET_NULL, blank=True)
    rank = models.IntegerField(null=True, blank=True)
    igor = models.IntegerField(null=True, blank=True)
    igor_history = ArrayField(
        models.IntegerField(null=True, blank=True),
        default=list, blank=True, null=True
    )
    ogs_username = models.CharField(max_length=32, null=True, blank=True)
    ogs_rating = models.FloatField(null=True, blank=True)
    ogs_deviation = models.FloatField(null=True, blank=True)
    ogs_id = models.IntegerField(null=True, blank=True)
    kgs_username = models.CharField(max_length=32, null=True, blank=True)
    auto_join = models.BooleanField(default=True)
    egd_pin = models.CharField(max_length=8, null=True, blank=True, validators=[MinLengthValidator(8)])
    egd_approval = models.BooleanField(default=False)
    availability = models.TextField(blank=True)
    is_supporter = models.BooleanField(default=False)
    country = CountryField()
    club = models.CharField(max_length=4, blank=True, validators=[MinLengthValidator(4)])

    def __str__(self) -> str:
        return self.nick

    def get_absolute_url(self) -> str:
        return reverse("player-detail", kwargs={"slug": self.nick})

    def get_egd_profile_url(self) -> Optional[str]:
        if self.egd_pin:
            return f"https://www.europeangodatabase.eu/EGD/Player_Card.php?&key={self.egd_pin}"
        return None


class GameServer(models.TextChoices):
    OGS = ("OGS", "OGS")
    KGS = ("KGS", "KGS")


class MemberResult(Enum):
    PROMOTION = "PROMOTION"
    STAY = "STAY"
    RELEGATION = "RELEGATION"


class MemberManager(models.Manager):
    def get_current_membership(self, player: "Player") -> Optional["Member"]:
        try:
            return self.filter(
                player=player,
                group__season__state__in=[SeasonState.DRAFT, SeasonState.IN_PROGRESS],
            ).latest("group__season__number")
        except Member.DoesNotExist:
            return None


class AlreadyPlayedGamesError(Exception):
    pass


class MembershipHistory(str, Enum):
    NEWBIE = "NEWBIE"
    CONTINUING = "CONTINUING"
    RETURNING = "RETURNING"


class Member(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="memberships")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="members")
    rank = models.IntegerField(null=True)
    order = models.SmallIntegerField()
    final_order = models.SmallIntegerField(null=True)
    initial_score = models.FloatField(default=0.0)
    egd_approval = models.BooleanField(default=False)  # Store EGD approval status for this season
    
    # OGS data copied from player
    ogs_rating = models.FloatField(null=True, blank=True)
    ogs_deviation = models.FloatField(null=True, blank=True)
    ogs_id = models.IntegerField(null=True, blank=True)

    objects = MemberManager()

    class Meta:
        ordering = ["order"]

    def __str__(self) -> str:
        return self.player.nick

    @cached_property
    def points(self) -> int:
        result = 0
        for game in self.won_games.all():
            if game.win_type != WinType.BYE:
                result += 1
        return result

    @cached_property
    def score(self) -> float:
        result = float(self.initial_score)
        for game in self.won_games.all():
            if game.win_type == WinType.NOT_PLAYED and not game.winner:
                result += 0.5
            else:
                result += 1
        return result

    @cached_property
    def sodos(self) -> int:
        result = 0
        for game in self.won_games.all():
            if game.loser:
                result += game.loser.points
        return result

    @cached_property
    def igor(self) -> float:
        return self.player.igor

    @cached_property
    def sos(self) -> float:
        result = 0.0
        for game in self.games_as_white.all():
            opponent = game.get_opponent(self)
            if opponent is not None:  # Skip BYE games
                result += opponent.score
        for game in self.games_as_black.all():
            opponent = game.get_opponent(self)
            if opponent is not None:  # Skip BYE games
                result += opponent.score
        return result

    @cached_property
    def sosos(self) -> float:
        result = 0.0
        for game in self.games_as_white.all():
            opponent = game.get_opponent(self)
            if opponent is not None:  # Skip BYE games
                result += opponent.sos
        for game in self.games_as_black.all():
            opponent = game.get_opponent(self)
            if opponent is not None:  # Skip BYE games
                result += opponent.sos
        return result

    @cached_property
    def result(self) -> MemberResult:
        if self in self.group.members_qualification[: self.group.season.promotion_count] and not self.group.is_first:
            return MemberResult.PROMOTION
        if self in self.group.members_qualification[-self.group.season.promotion_count :]:
            return MemberResult.RELEGATION
        return MemberResult.STAY

    def withdraw(self) -> None:
        self.group.season.validate_state(state=SeasonState.IN_PROGRESS)
        if self.group.members.count() % 2 or self.group.type != GroupType.ROUND_ROBIN:
            raise NotImplementedError()
        played_games = (
            Game.objects.get_for_member(member=self)
            .exclude(win_type__in=[WinType.BYE, WinType.NOT_PLAYED])
            .filter(win_type__isnull=False)
        )
        if played_games.exists():
            raise AlreadyPlayedGamesError()
        self.games_as_black.exclude(win_type=WinType.BYE).update(
            black=None, white=None, win_type=WinType.BYE, winner=F("white")
        )
        self.games_as_white.exclude(win_type=WinType.BYE).update(
            black=None, white=None, win_type=WinType.BYE, winner=F("black")
        )
        self.group.members.filter(order__gt=self.order).update(order=F("order") - 1)
        self.delete()

    @cached_property
    def membership_history(self) -> MembershipHistory:
        previous_season = Season.objects.exclude(
            id=self.group.season_id
        ).filter(groups__members__player_id=self.player_id).values("number").first()
        if not previous_season:
            return MembershipHistory.NEWBIE
        if self.group.season.number - previous_season["number"] == 1:
            return MembershipHistory.CONTINUING
        else:
            return MembershipHistory.RETURNING


def game_upload_to(instance, filename) -> str:
    return f"games/season-{instance.group.season.number}-group-{instance.group.name}-game-{instance.black.player.nick}-{instance.white.player.nick}.sgf"


class RoundNotYetCompletedError(Exception):
    pass


class Round(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="rounds")
    number = models.SmallIntegerField()
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)

    class Meta:
        ordering = ["number"]

    def is_current(self) -> bool:
        if not self.start_date or not self.end_date:
            return False
        return self.start_date <= datetime.date.today() <= self.end_date

    def is_closed(self) -> bool:
        if self.group.type != GroupType.MCMAHON:
            return False
        return self.number != self.group.rounds.last().number

    def is_completed(self) -> bool:
        return all(game.is_played for game in self.games.all())

    def validate_is_completed(self):
        if not self.is_completed():
            raise RoundNotYetCompletedError(f"Round: {self} not yet completed")


class WinType(models.TextChoices):
    POINTS = "points", texts.WIN_TYPE_POINTS
    RESIGN = "resign", texts.WIN_TYPE_RESIGN
    TIME = "time", texts.WIN_TYPE_TIME
    BYE = "bye", texts.WIN_TYPE_BYE
    NOT_PLAYED = "not_played", texts.WIN_TYPE_NOT_PLAYED


class GameManager(models.Manager):
    def get_upcoming_game(self, member: Member) -> Optional["Game"]:
        try:
            return self.get_for_member(member=member).filter(win_type__isnull=True).earliest("round__number")
        except Game.DoesNotExist:
            return None

    def get_for_member(self, member: Member) -> QuerySet:
        return (
            self.filter(Q(white=member) | Q(black=member) | Q(winner=member))
            .order_by("round__number")
            .select_related(
                "white__player__user",
                "black__player__user",
                "winner",
                "group__season",
                "round",
            )
        )

    def create_bye_game(self, group: Group, round: Round, member: Member):
        self.create(
            group=group,
            round=round,
            winner=member,
            win_type=WinType.BYE,
            date=datetime.datetime.combine(round.end_date, settings.DEFAULT_GAME_TIME),
        )

    def get_immediate_games(self):
        now = datetime.datetime.now()
        start = now + datetime.timedelta(hours=2)
        end = now + datetime.timedelta(days=6, hours=23)
        return self.filter(
            win_type__isnull=True,
            group__season__state=SeasonState.IN_PROGRESS,
            upcoming_reminder_sent__isnull=True,
            date__range=(start, end),
        )

    def get_delayed_games(self):
        return self.filter(
            win_type__isnull=True,
            group__season__state=SeasonState.IN_PROGRESS,
            delayed_reminder_sent__isnull=True,
            date__lt=datetime.date.today(),
        )

    def get_latest_finished(self, current_season=False) -> QuerySet:
        queryset = (
            self.prefetch_related("group", "black__player", "white__player", "group__season")
            .order_by("-sgf_updated")
            .filter(sgf_updated__isnull=False)
        )
        if current_season:
            queryset.filter(group__season__state=SeasonState.IN_PROGRESS)
        return queryset

    def get_latest_reviews(self, current_season=False) -> QuerySet:
        queryset = (
            self.prefetch_related("group", "black__player", "white__player", "group__teacher", "group__season")
            .order_by("-review_updated")
            .filter(review_updated__isnull=False)
        )
        if current_season:
            queryset.filter(group__season__state=SeasonState.IN_PROGRESS)
        return queryset

    def get_upcoming_games(self) -> QuerySet:
        now = datetime.datetime.now()
        one_hour_ago = now - datetime.timedelta(hours=1)
        return (
            self.prefetch_related("group", "black__player", "white__player", "group__season")
            .filter(win_type=WinType.NOT_PLAYED, date__gt=one_hour_ago)
            .order_by("date")
        )


def points_difference_validator(value: Optional[decimal.Decimal]) -> None:
    if value is not None:
        if value < 0:
            raise ValidationError(texts.POINTS_DIFFERENCE_NEGATIVE_ERROR)
        if value % 1 != decimal.Decimal("0.5"):
            raise ValidationError(texts.POINTS_DIFFERENCE_HALF_POINT_ERROR)


class Game(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="games")
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name="games")
    black = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name="games_as_black",
        null=True,
        blank=True,
    )
    white = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name="games_as_white",
        null=True,
        blank=True,
    )

    winner = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        null=True,
        related_name="won_games",
        blank=True,
    )
    win_type = models.CharField(choices=WinType.choices, max_length=16, null=True, blank=True)
    points_difference = models.DecimalField(
        null=True,
        blank=True,
        max_digits=4,
        decimal_places=1,
        validators=[points_difference_validator],
    )

    date = models.DateTimeField(null=True, blank=True)
    server = models.CharField(max_length=3, choices=GameServer.choices, blank=True)
    link = models.URLField(null=True, blank=True)
    sgf = models.FileField(null=True, upload_to=game_upload_to, blank=True)
    updated = models.DateTimeField(auto_now=True)

    review_video_link = models.URLField(null=True, blank=True)
    ai_analyse_link = models.URLField(null=True, blank=True)
    upcoming_reminder_sent = models.DateTimeField(null=True)
    delayed_reminder_sent = models.DateTimeField(null=True)

    sgf_updated = models.DateTimeField(null=True)
    review_updated = models.DateTimeField(null=True)

    objects = GameManager()

    def __str__(self) -> str:
        if self.is_bye:
            return f"Bye - {self.winner} "
        return f"B: {self.black} - W: {self.white} - winner: {self.winner}"

    @property
    def is_played(self) -> bool:
        return bool(self.win_type)

    @property
    def is_bye(self):
        return self.win_type == WinType.BYE

    def get_absolute_url(self):
        if self.is_bye:
            return reverse(
                "bye-game-detail",
                kwargs={
                    "season_number": self.group.season.number,
                    "group_name": self.group.name,
                    "bye_player": self.winner,
                },
            )
        return reverse(
            "game-detail",
            kwargs={
                "season_number": self.group.season.number,
                "group_name": self.group.name,
                "black_player": self.black.player.nick,
                "white_player": self.white.player.nick,
            },
        )

    def game_result_for(self, member: Member) -> Optional[GameResult]:
        if not self.win_type:
            return None
        return GameResult.WIN if self.winner == member else GameResult.LOSE

    @property
    def loser(self) -> Optional["Member"]:
        if not self.winner or self.is_bye:
            return None
        return self.white if self.winner == self.black else self.black

    def get_opponent(self, member: Member) -> Optional["Member"]:
        if self.is_bye:
            return None
        return self.white if member == self.black else self.black

    def is_participant(self, player: Player):
        return player in [self.black.player, self.white.player]

    @cached_property
    def external_sgf_link(self) -> Optional[str]:
        if not self.link:
            return None
        match = re.match(settings.OGS_GAME_LINK_REGEX, self.link)
        if not match:
            return None
        return settings.OGS_SGF_LINK_FORMAT.format(id=match.group(1))

    @property
    def sgf_link(self) -> Optional[str]:
        if self.sgf:
            return self.sgf.url
        elif self.external_sgf_link:
            return self.external_sgf_link
        return None

    @property
    def is_delayed(self):
        return not self.win_type and self.date.date() < datetime.date.today()

    @property
    def is_editable_by_player(self):
        return not self.round.is_closed() and self.group.season.state == SeasonState.IN_PROGRESS

    @property
    def is_egd_eligible(self) -> bool:
        """
        Determine if a game is eligible for EGD/EGF submission based on member approvals.
        Both players must exist (not BYE games) and have egd_approval set for this season.
        The game doesn't need to be played yet to be marked as eligible in the UI.
        """
        return (self.black and self.white and
                self.black.egd_approval and
                self.white.egd_approval)


class GameAIAnalyseUploadStatus(TextChoices):
    IN_PROGRESS = "in_progress", "in_progress"
    DONE = "done", "done"
    FAILED = "failed", "failed"


class GameAIAnalyseUpload(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="ai_analyse_uploads")
    sgf_hash = models.CharField(max_length=32, null=True)
    status = models.CharField(max_length=16, choices=GameAIAnalyseUploadStatus.choices)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    error = models.TextField()
    result = models.URLField(null=True)


@receiver(signal=pre_save, sender=Game)
def update_game_timestamps(sender, instance: Game, raw, using, update_fields, **kwargs):
    try:
        db_game: Game = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        pass
    else:
        if db_game.review_updated is None and instance.review_video_link and len(str(instance.review_video_link)) > 0:
            instance.review_updated = datetime.datetime.now()
        if db_game.sgf_updated is None and instance.sgf and len(str(instance.sgf)) > 0:
            instance.sgf_updated = datetime.datetime.now()


@receiver(signal=post_save, sender=Game)
def game_updated(instance, raw, **kwargs):
    from league.tasks import game_ai_analyse_upload_task, game_sgf_fetch_task

    if instance.sgf and not instance.ai_analyse_link:
        game_ai_analyse_upload_task.delay(game_id=instance.id)
    if instance.link and not instance.sgf:
        game_sgf_fetch_task.delay(game_id=instance.id)
