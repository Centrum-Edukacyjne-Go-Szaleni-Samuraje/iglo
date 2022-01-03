import datetime
import decimal
import math
import re
import string
from collections import OrderedDict
from enum import Enum
from statistics import mean
from typing import Optional

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q, TextChoices, QuerySet, Avg, Count, Case, When, Value
from django.urls import reverse
from django.utils.functional import cached_property

from league import texts
from league.utils import round_robin, shuffle_colors
from macmahon import macmahon as mm

OGS_GAME_LINK_REGEX = r"https:\/\/online-go\.com\/game\/(\d+)"

DAYS_PER_GAME = 7
NUMBER_OF_BARS = 2


class SeasonState(TextChoices):
    DRAFT = "draft", texts.SEASON_STATE_DRAFT
    IN_PROGRESS = "in_progress", texts.SEASON_STATE_IN_PROGRES
    FINISHED = "finished", texts.SEASON_STATE_FINISHED


class SeasonManager(models.Manager):
    def prepare_season(self, start_date: datetime.date, players_per_group: int, promotion_count: int) -> "Season":
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
        season.create_groups()
        return season

    def get_latest(self) -> Optional["Season"]:
        return (
            Season.objects.prefetch_related("groups")
            .annotate(
                all_games=Count("groups__games"),
                played_games=Count("groups__games", filter=Q(groups__games__win_type__isnull=False)),
            )
            .annotate(
                games_progress=Case(
                    When(all_games__gt=0, then=(F("played_games") * 100) / F("all_games")), default=Value(0)
                )
            )
            .latest("number")
        )


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
        self.state = SeasonState.IN_PROGRESS
        self.save()
        for group in self.groups.filter(type=GroupType.ROUND_ROBIN):
            members = list(group.members.all())
            current_date = self.start_date
            for round_number, round_pairs in enumerate(shuffle_colors(paring=round_robin(n=len(members))), start=1):
                round = Round.objects.create(
                    number=round_number,
                    group=group,
                    start_date=current_date,
                    end_date=current_date + datetime.timedelta(days=DAYS_PER_GAME - 1),
                )
                current_date += datetime.timedelta(days=DAYS_PER_GAME)
                for pair in round_pairs:
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
            raise GamesWithoutResultError()
        self.state = SeasonState.FINISHED
        self.save()

    def validate_state(self, state: SeasonState) -> None:
        if self.state != state:
            raise WrongSeasonStateError()

    def reset_groups(self) -> None:
        self.validate_state(state=SeasonState.DRAFT)
        self.groups.all().delete()
        self.create_groups()

    def create_groups(self) -> None:
        self.validate_state(state=SeasonState.DRAFT)
        try:
            previous_season = Season.objects.get(number=self.number - 1)
            players = previous_season.get_leaderboard()
            players = [player for player in players if player.auto_join]
        except Season.DoesNotExist:
            players = []
        players = self._redistribute_new_players(players=players, players_per_group=self.players_per_group)
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
        for new_player in new_players:
            add_to_next = False
            previous_avg_rank = None
            for group_order in range(math.ceil(len(result) / players_per_group)):
                group_players = result[group_order * players_per_group : (group_order + 1) * players_per_group]
                avg_rank = mean(player.rank for player in group_players)
                if add_to_next and previous_avg_rank > avg_rank:
                    result.insert((group_order + 1) * players_per_group - 1, new_player)
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
            group_players = players[
                group_order * self.players_per_group : (group_order + 1) * self.players_per_group
            ]
            if len(group_players) < max((self.players_per_group - 1), 2) and last_group:
                group = last_group
                group.type = GroupType.MCMAHON
                group.save()
            else:
                group = Group.objects.create(
                    name=string.ascii_uppercase[group_order],
                    season=self,
                    type=GroupType.ROUND_ROBIN,
                )
                last_group = group
            for player_order, player in enumerate(group_players, start=group.members.count() + 1):
                Member.objects.create(
                    group=group,
                    order=player_order,
                    player=player,
                    rank=player.rank,
                )
            if group.type == GroupType.MCMAHON:
                group.set_initial_score()


class GameResult(Enum):
    WIN = "W"
    LOSE = "L"


class GroupType(models.TextChoices):
    ROUND_ROBIN = "round_robin", "Każdy z każdym"
    MCMAHON = "mcmahon", "McMahon"


class NotMcmahonGroupError(Exception):
    pass


class ResultSymbol(str, Enum):
    win = '+'
    lose = '-'
    not_played = '?'
    no_result = 'X'


class Group(models.Model):
    name = models.CharField(max_length=1)
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name="groups")
    type = models.CharField(choices=GroupType.choices, max_length=16)

    def __str__(self) -> str:
        return f"{self.name} - season: {self.season}"

    def get_absolute_url(self):
        return reverse(
            "group-detail",
            kwargs={"season_number": self.season.number, "group_name": self.name},
        )

    @cached_property
    def results_table(self) -> list[tuple[int, "Player", list[tuple[str, str]]]]:
        members = self.members.select_related("player").all()
        sorted_members = sorted(members, key=lambda m: (m.score, m.sodos, m.order), reverse=True)
        enumerated_members = list(enumerate(sorted_members, start=1))
        player_position = OrderedDict()
        for idx, member in enumerated_members:
            player_position[member.player.nick] = idx
        table = []
        for position, member in enumerated_members:
            games = Game.objects.get_for_member(member)
            records = []
            for game in games:
                opponent = game.get_opponent(member)
                opponent_position = player_position[opponent.player.nick]
                if not game.is_played:
                    result_symbol = ResultSymbol.not_played
                elif game.winner == member:
                    result_symbol = ResultSymbol.win
                elif game.winner == opponent:
                    result_symbol = ResultSymbol.lose
                else:
                    result_symbol = ResultSymbol.no_result
                records.append((f'{opponent_position}{result_symbol}', game.get_absolute_url()))
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
    def latest_round(self) -> 'Round':
        return self.rounds.order_by('-number').first()

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
        self.members.filter(order__gt=member_to_remove.order).update(order=F("order") - 1)
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

    def swap_member(self, player_nick_to_remove: str, player_nick_to_add: str) -> None:
        member_to_remove = self.members.get(player__nick=player_nick_to_remove)
        self.members.filter(order__gt=member_to_remove.order).update(order=F("order") - 1)
        player_to_add = Player.objects.get(nick=player_nick_to_add)
        new_member = Member.objects.create(
            group=self,
            player=player_to_add,
            rank=player_to_add.rank,
            order=self.members.count(),
        )
        member_to_remove.games_as_white.update(white=new_member)
        member_to_remove.games_as_black.update(black=new_member)
        member_to_remove.delete()

    def validate_type(self, group_type: GroupType):
        if self.type != group_type:
            raise NotMcmahonGroupError()

    def set_initial_score(self):
        self.season.validate_state(SeasonState.DRAFT)
        self.validate_type(GroupType.MCMAHON)
        members = self.members.all()
        registered_players = [(member.player.nick, member.rank) for member in members]
        initial_ordering = mm.BasicInitialOrdering(number_of_bars=NUMBER_OF_BARS).order(registered_players)
        initial_ordering = {p.name: p for p in initial_ordering}
        for member in members:
            ordered_player = initial_ordering[member.player.nick]
            member.initial_score = ordered_player.initial_score
        Member.objects.bulk_update(members, ['initial_score'])

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

        new_round = Round.objects.create(
            group=self,
            number=number,
            start_date=start_date,
            end_date=end_date
        )

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
                date=datetime.datetime.combine(
                    new_round.end_date, settings.DEFAULT_GAME_TIME
                )
            )
        if bye:
            Game.objects.create_bye_game(self, new_round, Member.objects.get(player__nick=bye.name, group=self))

    def get_macmahon_players(self):
        members = Member.objects.filter(group=self).prefetch_related('player').all()
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
                    player.games.append(mm.GameRecord('', mm.Color.BYE, mm.ResultType.BYE))
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
    ogs_username = models.CharField(max_length=32, null=True, blank=True)
    kgs_username = models.CharField(max_length=32, null=True, blank=True)
    auto_join = models.BooleanField(default=True)
    egd_pin = models.CharField(max_length=8, null=True, blank=True)
    egd_approval = models.BooleanField(default=False)
    availability = models.TextField(blank=True)

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
                group__season__state__in=[SeasonState.DRAFT, SeasonState.IN_PROGRESS],
            ).latest("group__season__number")
        except Member.DoesNotExist:
            return None


class Member(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="memberships")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="members")
    rank = models.IntegerField(null=True)
    order = models.SmallIntegerField()
    initial_score = models.SmallIntegerField(default=0)

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
            result += game.loser.points
        return result

    @cached_property
    def sos(self) -> float:
        result = 0.0
        for game in self.games_as_white.all():
            result += game.get_opponent(self).score
        for game in self.games_as_black.all():
            result += game.get_opponent(self).score
        return result

    @cached_property
    def sosos(self) -> float:
        result = 0.0
        for game in self.games_as_white.all():
            result += game.get_opponent(self).sos
        for game in self.games_as_black.all():
            result += game.get_opponent(self).sos
        return result

    @cached_property
    def result(self) -> MemberResult:
        if self in self.group.members_qualification[: self.group.season.promotion_count] and not self.group.is_first:
            return MemberResult.PROMOTION
        if self in self.group.members_qualification[-self.group.season.promotion_count :]:
            return MemberResult.RELEGATION
        return MemberResult.STAY


def game_upload_to(instance, filename) -> str:
    return f"games/season-{instance.group.season.number}-group-{instance.group.name}-game-{instance.black.player.nick}-{instance.white.player.nick}.sgf"


class RoundNotYetCompletedError(Exception):
    pass


class Round(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="rounds")
    number = models.SmallIntegerField()
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)

    def is_current(self) -> bool:
        if not self.start_date or not self.end_date:
            return False
        return self.start_date <= datetime.date.today() <= self.end_date

    def is_completed(self) -> bool:
        return all(game.is_played for game in self.games.all())

    def validate_is_completed(self):
        if not self.is_completed():
            raise RoundNotYetCompletedError(f'Round: {self} not yet completed')


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

    @property
    def result(self) -> Optional[str]:
        if not self.is_played:
            return None
        if not self.winner or self.is_bye:
            return WinType(self.win_type).label
        winner_color = "B" if self.winner == self.black else "W"
        if self.win_type:
            win_type = (
                self.points_difference or 0.5 if self.win_type == WinType.POINTS else WinType(self.win_type).label
            )
            return f"{winner_color}+{win_type}"
        return winner_color

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

    @cached_property
    def external_sgf_link(self) -> Optional[str]:
        if not self.link:
            return None
        match = re.match(OGS_GAME_LINK_REGEX, self.link)
        if not match:
            return None
        return f"https://online-go.com/api/v1/games/{match.group(1)}/sgf"

    @property
    def sgf_link(self) -> Optional[str]:
        if self.sgf:
            return self.sgf.url
        elif self.external_sgf_link:
            return self.external_sgf_link
        return None

    def is_participant(self, player: Player):
        return player in [self.black.player, self.white.player]
