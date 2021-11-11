import datetime
import math
import random
import string
from enum import Enum
from typing import Optional

from django.conf import settings
from django.db import models
from django.db.models import F, Q, TextChoices, QuerySet, Avg
from django.db.models.functions import Ord, Chr
from django.urls import reverse
from django.utils.functional import cached_property

from league import texts
from league.utils import round_robin

DAYS_PER_GAME = 7


class SeasonState(TextChoices):
    DRAFT = "draft", texts.SEASON_STATE_DRAFT
    IN_PROGRESS = "in_progress", texts.SEASON_STATE_IN_PROGRES
    FINISHED = "finished", texts.SEASON_STATE_FINISHED


class SeasonManager(models.Manager):
    def prepare_season(
        self, start_date: datetime.date, players_per_group: int, promotion_count: int
    ) -> "Season":
        previous_season = Season.objects.first()
        if previous_season.state != SeasonState.FINISHED:
            raise ValueError(texts.PREVIOUS_SEASON_NOT_CLOSED_ERROR)
        season = self.create(
            state=SeasonState.DRAFT,
            number=previous_season.number + 1,
            start_date=start_date,
            end_date=start_date
            + datetime.timedelta(days=(players_per_group - 1) * DAYS_PER_GAME - 1),
            promotion_count=promotion_count,
            players_per_group=players_per_group,
        )
        season_players = []
        for group in previous_season.groups.order_by("name"):
            group_players = [
                member.player
                for member in group.members_qualification
                if member.player.auto_join
            ]
            season_players = (
                season_players[: -previous_season.promotion_count]
                + group_players[: previous_season.promotion_count]
                + season_players[-previous_season.promotion_count :]
                + group_players[previous_season.promotion_count :]
            )
        season_players.extend(
            Player.objects.filter(auto_join=True)
            .order_by("-rank")
            .exclude(id__in=[p.id for p in season_players])
        )
        last_group = None
        for group_order in range(math.ceil(len(season_players) / players_per_group)):
            group_players = season_players[
                group_order * players_per_group : (group_order + 1) * players_per_group
            ]
            if len(group_players) < max((players_per_group - 1), 2) and last_group:
                group = last_group
                group.type = GroupType.MCMAHON
                group.save()
            else:
                group = Group.objects.create(
                    name=string.ascii_uppercase[group_order],
                    season=season,
                    type=GroupType.ROUND_ROBIN,
                )
                last_group = group
            for player_order, player in enumerate(
                group_players, start=group.members.count() + 1
            ):
                Member.objects.create(
                    group=group,
                    order=player_order,
                    player=player,
                    rank=player.rank,
                )

        return season


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

    def delete_group(self, group_id: int) -> None:
        self.validate_state(state=SeasonState.DRAFT)
        group = self.groups.get(id=group_id)
        self.groups.filter(name__gt=group.name).update(name=Chr(Ord("name") - 1))
        group.delete()

    def add_group(self) -> None:
        self.validate_state(state=SeasonState.DRAFT)
        Group.objects.create(
            season=self,
            name=chr(ord("A") + self.groups.count()),
            type=GroupType.MCMAHON,
        )

    def start(self) -> None:
        self.validate_state(state=SeasonState.DRAFT)
        self.state = SeasonState.IN_PROGRESS
        self.save()
        current_date = self.start_date
        for group in self.groups.filter(type=GroupType.ROUND_ROBIN):
            members = list(group.members.all())
            for round_number, round_pairs in enumerate(
                round_robin(n=len(members)), start=1
            ):
                round = Round.objects.create(
                    number=round_number,
                    group=group,
                    start_date=current_date,
                    end_date=current_date + datetime.timedelta(days=DAYS_PER_GAME - 1),
                )
                current_date += datetime.timedelta(days=DAYS_PER_GAME)
                for pair in round_pairs:
                    game_members = [members[pair[0]], members[pair[1]]]
                    random.shuffle(game_members)
                    Game.objects.create(
                        group=group,
                        round=round,
                        black=game_members[0],
                        white=game_members[1],
                        date=datetime.datetime.combine(
                            round.end_date, settings.DEFAULT_GAME_TIME
                        ),
                    )

    def finish(self) -> None:
        self.validate_state(state=SeasonState.IN_PROGRESS)
        if Game.objects.filter(group__season=self, win_type__isnull=True).exists():
            raise GamesWithoutResultError()
        self.state = SeasonState.FINISHED
        self.save()

    def validate_state(self, state: SeasonState) -> None:
        if self.state != state:
            raise WrongSeasonStateError()


class GameResult(Enum):
    WIN = "W"
    LOSE = "L"


class GroupType(models.TextChoices):
    ROUND_ROBIN = "round_robin", "Każdy z każdym"
    MCMAHON = "mcmahon", "McMahon"


class Group(models.Model):
    name = models.CharField(max_length=1)
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name="groups")
    type = models.CharField(choices=GroupType.choices, max_length=16)

    def __str__(self) -> str:
        return f"{self.name} - season: {self.season}"

    def results_as_table(
        self,
    ) -> list[tuple["Player", list[tuple["Player", Optional[GameResult]]]]]:
        table = []
        players_to_game = {
            frozenset({game.black.player, game.white.player}): game
            for game in self.games.select_related(
                "black__player", "white__player", "winner"
            ).all()
        }
        for member in self.members.select_related("player").all():
            row = []
            for other_member in self.members.select_related("player").all():
                if member == other_member:
                    row.append((other_member, None))
                else:
                    try:
                        game = players_to_game[
                            frozenset({member.player, other_member.player})
                        ]
                        row.append((other_member, game.game_result_for(member)))
                    except KeyError:
                        row.append((other_member, None))
            table.append((member, row))
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
    def members_qualification(self) -> list["Member"]:
        return sorted(
            [
                member
                for member in self.members.select_related("player")
                .prefetch_related("won_games", "games_as_black", "games_as_white")
                .all()
            ],
            key=lambda member: (-member.points, -member.sodos)
            if self.type == GroupType.ROUND_ROBIN
            else (-member.points, -member.score, -member.sos, -member.sosos),
        )

    def delete_member(self, member_id: int) -> None:
        self.season.validate_state(state=SeasonState.DRAFT)
        member_to_remove = self.members.get(id=member_id)
        self.members.filter(order__gt=member_to_remove.order).update(
            order=F("order") - 1
        )
        member_to_remove.delete()

    def move_member_up(self, member_id: int) -> None:
        self.season.validate_state(state=SeasonState.DRAFT)
        member_to_move_up = self.members.get(id=member_id)
        if member_to_move_up.order == 1:
            return
        member_to_move_down = self.members.get(order=member_to_move_up.order - 1)
        member_to_move_down.order += 1
        member_to_move_down.save()
        member_to_move_up.order -= 1
        member_to_move_up.save()

    def move_member_down(self, member_id: int) -> None:
        self.season.validate_state(state=SeasonState.DRAFT)
        member_to_move_down = self.members.get(id=member_id)
        if member_to_move_down.order == self.members.count():
            return
        member_to_move_up = self.members.get(order=member_to_move_down.order + 1)
        member_to_move_up.order -= 1
        member_to_move_up.save()
        member_to_move_down.order += 1
        member_to_move_down.save()

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
        )

    def avg_rank(self) -> int:
        result = self.members.aggregate(avg_rank=Avg("rank"))["avg_rank"]
        return int(result or 0)


class Player(models.Model):
    nick = models.CharField(max_length=32, unique=True)
    first_name = models.CharField(max_length=32)
    last_name = models.CharField(max_length=32)
    user = models.OneToOneField(
        "accounts.User", null=True, on_delete=models.SET_NULL, blank=True
    )
    rank = models.IntegerField(null=True, blank=True)
    ogs_username = models.CharField(max_length=32, null=True, blank=True)
    kgs_username = models.CharField(max_length=32, null=True, blank=True)
    auto_join = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.nick

    def get_absolute_url(self) -> str:
        return reverse("player-detail", kwargs={"slug": self.nick})


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
                group__season__end_date__gte=datetime.date.today(),
            ).latest("group__season__number")
        except Member.DoesNotExist:
            return None


class Member(models.Model):
    player = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name="memberships"
    )
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="members")
    rank = models.IntegerField(null=True)
    order = models.SmallIntegerField()

    objects = MemberManager()

    class Meta:
        ordering = ["order"]

    def __str__(self) -> str:
        return self.player.nick

    @cached_property
    def points(self) -> int:
        return self.won_games.count()

    @cached_property
    def score(self) -> float:
        result = 0.0
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
            result += game.loser.points
        return result

    @cached_property
    def sos(self) -> float:
        result = 0
        for game in self.games_as_white.all():
            result += game.get_opponent(self).score
        for game in self.games_as_black.all():
            result += game.get_opponent(self).score
        return result

    @cached_property
    def sosos(self) -> float:
        result = 0
        for game in self.games_as_white.all():
            result += game.get_opponent(self).sos
        for game in self.games_as_black.all():
            result += game.get_opponent(self).sos
        return result

    @cached_property
    def result(self) -> MemberResult:
        if (
            self
            in self.group.members_qualification[: self.group.season.promotion_count]
            and not self.group.is_first
        ):
            return MemberResult.PROMOTION
        if (
            self
            in self.group.members_qualification[-self.group.season.promotion_count :]
        ):
            return MemberResult.RELEGATION
        return MemberResult.STAY


def game_upload_to(instance, filename) -> str:
    return f"games/season-{instance.group.season.number}-group-{instance.group.name}-game-{instance.black.player.nick}-{instance.white.player.nick}.sgf"


class Round(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="rounds")
    number = models.SmallIntegerField()
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)

    def is_current(self) -> bool:
        if not self.start_date or not self.end_date:
            return False
        return self.start_date <= datetime.date.today() <= self.end_date


class WinType(models.TextChoices):
    POINTS = "points", texts.WIN_TYPE_POINTS
    RESIGN = "resign", texts.WIN_TYPE_RESIGN
    TIME = "time", texts.WIN_TYPE_TIME
    NOT_PLAYED = "not_played", texts.WIN_TYPE_NOT_PLAYED


class GameManager(models.Manager):
    def get_upcoming_game(self, member: Member) -> Optional["Game"]:
        try:
            return (
                self.get_for_member(member=member)
                .filter(win_type__isnull=True)
                .earliest("round__number")
            )
        except Game.DoesNotExist:
            return None

    def get_for_member(self, member: Member) -> QuerySet:
        return (
            self.filter(Q(white=member) | Q(black=member))
            .order_by("round__number")
            .select_related(
                "white__player__user",
                "black__player__user",
                "winner",
                "group__season",
                "round",
            )
        )


class Game(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="games")
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name="games")
    black = models.ForeignKey(
        Member, on_delete=models.CASCADE, related_name="games_as_black"
    )
    white = models.ForeignKey(
        Member, on_delete=models.CASCADE, related_name="games_as_white"
    )

    winner = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        null=True,
        related_name="won_games",
        blank=True,
    )
    win_type = models.CharField(
        choices=WinType.choices, max_length=16, null=True, blank=True
    )
    points_difference = models.DecimalField(
        null=True, blank=True, max_digits=4, decimal_places=1
    )

    date = models.DateTimeField(null=True, blank=True)
    server = models.CharField(max_length=3, choices=GameServer.choices)
    link = models.URLField(null=True, blank=True)
    sgf = models.FileField(null=True, upload_to=game_upload_to, blank=True)

    objects = GameManager()

    def __str__(self) -> str:
        return f"B: {self.black} - W: {self.white} - winner: {self.winner}"

    @property
    def is_played(self) -> bool:
        return bool(self.win_type)

    @property
    def result(self) -> Optional[str]:
        if not self.is_played:
            return None
        if not self.winner:
            return WinType(self.win_type).label
        winner_color = "B" if self.winner == self.black else "W"
        if self.win_type:
            win_type = (
                self.points_difference or 0.5
                if self.win_type == WinType.POINTS
                else WinType(self.win_type).label
            )
            return f"{winner_color}+{win_type}"
        return winner_color

    def get_absolute_url(self):
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
        if not self.winner:
            return None
        return self.white if self.winner == self.black else self.black

    def get_opponent(self, member: Member) -> Member:
        return self.white if member == self.black else self.black
