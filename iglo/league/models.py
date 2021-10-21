from enum import Enum
from typing import Optional

from django.db import models


class Season(models.Model):
    number = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    promotion_count = models.SmallIntegerField()

    class Meta:
        ordering = ["-number"]

    def __str__(self) -> str:
        return f"#{self.number} ({self.start_date} - {self.end_date})"


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
                    game = players_to_game[
                        frozenset({member.player, other_member.player})
                    ]
                    row.append(
                        GameResult.WIN
                        if game.winner.player == member.player
                        else GameResult.LOSE
                    )
            table.append((member, row))
        return table


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
        members = sorted(
            [member for member in self.group.members.all()],
            key=lambda member: (-member.score, -member.sodos),
        )
        if self in members[:self.group.season.promotion_count]:
            return MemberResult.PROMOTION
        if self in members[-self.group.season.promotion_count:]:
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
