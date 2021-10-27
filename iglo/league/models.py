import datetime
import string
from enum import Enum
from typing import Optional

from django.db import models
from django.db.models import F
from django.db.models.functions import Ord, Chr
from django.urls import reverse

from league.utils import round_robin

DAYS_PER_GAME = 7


class SeasonState(Enum):
    DRAFT = "DRAFT"
    READY = "READY"


class SeasonManager(models.Manager):
    def prepare_season(
            self, start_date: datetime.date, players_per_group: int, promotion_count: int
    ) -> "Season":
        previous_season = Season.objects.first()
        if previous_season.state == SeasonState.DRAFT.value:
            raise ValueError("Poprzedni sezon nie został rozpoczęty.")
        number_of_members = Member.objects.filter(group__season=previous_season).count()
        season = self.create(
            state=SeasonState.DRAFT.value,
            number=previous_season.number + 1,
            start_date=start_date,
            end_date=start_date + datetime.timedelta(days=(players_per_group - 1) * DAYS_PER_GAME - 1),
            promotion_count=promotion_count,
            players_per_group=players_per_group,
        )
        group_names = string.ascii_uppercase[: number_of_members // players_per_group]
        for group_name in group_names:
            group = Group.objects.create(
                name=group_name,
                season=season,
            )
            is_last = group_name == group_names[-1]
            if previous_season:
                if not group.is_first:
                    self._add_members(
                        group=group,
                        previous_season=previous_season,
                        previous_group_name=group.higher_group_name,
                        results={MemberResult.RELEGATION},
                    )
                self._add_members(
                    group=group,
                    previous_season=previous_season,
                    previous_group_name=group.name,
                    results={MemberResult.STAY, MemberResult.RELEGATION} if is_last else {MemberResult.STAY},
                )
                if not is_last:
                    self._add_members(
                        group=group,
                        previous_season=previous_season,
                        previous_group_name=group.lower_group_name,
                        results={MemberResult.PROMOTION},
                    )
        return season

    def _add_members(
            self,
            group: "Group",
            previous_season: "Season",
            previous_group_name: str,
            results: set["MemberResult"],
    ) -> None:
        try:
            members_count = group.members.count()
            previous_group = previous_season.groups.get(name=previous_group_name)
            for member in previous_group.get_members_qualification():
                if member.result in results:
                    Member.objects.create(
                        group=group,
                        order=members_count + 1,
                        player=member.player,
                        rank=member.rank,
                    )
                    members_count += 1
        except Group.DoesNotExist:
            pass


class SeasonNotInDraft(Exception):
    pass


def raise_if_not_in_draft(season: "Season") -> None:
    if season.state != SeasonState.DRAFT.value:
        raise SeasonNotInDraft()


class Season(models.Model):
    number = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    promotion_count = models.SmallIntegerField()
    players_per_group = models.SmallIntegerField()
    state = models.CharField(max_length=8)

    objects = SeasonManager()

    class Meta:
        ordering = ["-number"]

    def __str__(self) -> str:
        return f"#{self.number} ({self.start_date} - {self.end_date})"

    def get_absolute_url(self):
        return reverse("season-detail", kwargs={"number": self.number})

    def delete_group(self, group_id: int) -> None:
        raise_if_not_in_draft(season=self)
        group = self.groups.get(id=group_id)
        self.groups.filter(name__gt=group.name).update(name=Chr(Ord("name") - 1))
        group.delete()

    def add_group(self) -> None:
        raise_if_not_in_draft(season=self)
        Group.objects.create(
            season=self,
            name=chr(ord("A") + self.groups.count())
        )

    def start(self) -> None:
        raise_if_not_in_draft(season=self)
        self.state = SeasonState.READY.value
        self.save()
        current_date = self.start_date
        for group in self.groups.all():
            members = list(group.members.all())
            for round_number, round_pairs in enumerate(round_robin(n=len(members)), start=1):
                round = Round.objects.create(
                    number=round_number,
                    group=group,
                    start_date=current_date,
                    end_date=current_date + datetime.timedelta(days=DAYS_PER_GAME - 1),
                )
                current_date += datetime.timedelta(days=DAYS_PER_GAME)
                for pair in round_pairs:
                    Game.objects.create(
                        group=group,
                        round=round,
                        black=members[pair[0]],
                        white=members[pair[1]],
                    )


class GameResult(Enum):
    WIN = "W"
    LOSE = "L"


class Group(models.Model):
    name = models.CharField(max_length=1)
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name="groups")

    def __str__(self) -> str:
        return f"{self.name} - season: {self.season}"

    def results_as_table(self) -> list[tuple["Player", list[Optional[GameResult]]]]:
        table = []
        players_to_game = {
            frozenset({game.black.player, game.white.player}): game
            for game in self.games.all()
        }
        for member in self.members.all():
            row = []
            for other_member in self.members.all():
                if member == other_member:
                    row.append(None)
                else:
                    try:
                        game = players_to_game[
                            frozenset({member.player, other_member.player})
                        ]
                        if game.winner:
                            row.append(
                                GameResult.WIN
                                if game.winner.player == member.player
                                else GameResult.LOSE
                            )
                        else:
                            row.append(None)
                    except KeyError:
                        row.append(None)
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

    def get_members_qualification(self) -> list["Member"]:
        return sorted(
            [member for member in self.members.all()],
            key=lambda member: (-member.score, -member.sodos),
        )

    def delete_member(self, member_id: int) -> None:
        raise_if_not_in_draft(season=self.season)
        member_to_remove = self.members.get(id=member_id)
        self.members.filter(order__gt=member_to_remove.order).update(order=F('order') - 1)
        member_to_remove.delete()

    def move_member_up(self, member_id: int) -> None:
        raise_if_not_in_draft(season=self.season)
        member_to_move_up = self.members.get(id=member_id)
        if member_to_move_up.order == 1:
            return
        member_to_move_down = self.members.get(order=member_to_move_up.order - 1)
        member_to_move_down.order += 1
        member_to_move_down.save()
        member_to_move_up.order -= 1
        member_to_move_up.save()

    def move_member_down(self, member_id: int) -> None:
        raise_if_not_in_draft(season=self.season)
        member_to_move_down = self.members.get(id=member_id)
        if member_to_move_down.order == self.members.count():
            return
        member_to_move_up = self.members.get(order=member_to_move_down.order + 1)
        member_to_move_up.order -= 1
        member_to_move_up.save()
        member_to_move_down.order += 1
        member_to_move_down.save()

    def add_member(self, player_nick: str) -> None:
        raise_if_not_in_draft(season=self.season)
        player = Player.objects.get(nick=player_nick)
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


class PlayerManager(models.Manager):
    def register_player(self, user, nick: str, rank: str, ogs: str) -> "Player":
        player = self.create(
            user=user,
            nick=nick,
            rank=rank,
        )
        Account.objects.create(
            player=player,
            name=ogs,
            server=GameServer.OGS,
        )
        return player


class Player(models.Model):
    nick = models.CharField(max_length=32, unique=True)
    user = models.OneToOneField("accounts.User", null=True, on_delete=models.SET_NULL)
    rank = models.CharField(max_length=3)

    objects = PlayerManager()

    def __str__(self) -> str:
        return self.nick


class GameServer(models.TextChoices):
    OGS = ("OGS", "OGS")
    KGS = ("KGS", "KGS")


class Account(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    name = models.CharField(max_length=32)
    server = models.CharField(max_length=3, choices=GameServer.choices)

    def __str__(self) -> str:
        return f"{self.player} - {self.name} - {self.server}"


class MemberResult(Enum):
    PROMOTION = "PROMOTION"
    STAY = "STAY"
    RELEGATION = "RELEGATION"


class Member(models.Model):
    player = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name="memberships"
    )
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="members")
    rank = models.CharField(max_length=3, null=True)
    order = models.SmallIntegerField()

    class Meta:
        ordering = ["order"]

    def __str__(self) -> str:
        return f"{self.player} - group: {self.group}"

    @property
    def score(self) -> int:
        return (
                self.games_as_black.filter(result__startswith="B").count()
                + self.games_as_white.filter(result__startswith="W").count()
        )

    @property
    def sodos(self) -> int:
        result = 0
        for game in self.games_as_black.filter(result__startswith="B"):
            result += game.white.score
        for game in self.games_as_white.filter(result__startswith="W"):
            result += game.black.score
        return result

    @property
    def result(self) -> MemberResult:
        members_qualification = self.group.get_members_qualification()
        if (
                self in members_qualification[: self.group.season.promotion_count]
                and not self.group.is_first
        ):
            return MemberResult.PROMOTION
        if self in members_qualification[-self.group.season.promotion_count:]:
            return MemberResult.RELEGATION
        return MemberResult.STAY


def game_upload_to(instance, filename) -> str:
    return f"games/season-{instance.group.season.number}-group-{instance.group.name}-game-{instance.black.player.nick}-{instance.white.player.nick}.sgf"


class Round(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="rounds")
    number = models.SmallIntegerField()
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)


class Game(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="games")
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name="games")
    black = models.ForeignKey(
        Member, on_delete=models.CASCADE, related_name="games_as_black"
    )
    white = models.ForeignKey(
        Member, on_delete=models.CASCADE, related_name="games_as_white"
    )
    result = models.CharField(max_length=8, null=True)
    date = models.DateTimeField(null=True)
    server = models.CharField(max_length=3, choices=GameServer.choices)
    link = models.URLField(null=True)
    sgf = models.FileField(null=True, upload_to=game_upload_to)

    def __str__(self) -> str:
        return f"B: {self.black} - W: {self.white} - winner: {self.winner}"

    @property
    def winner(self) -> Optional[Member]:
        if not self.result:
            return None
        return self.black if self.result[0] == "B" else self.white
