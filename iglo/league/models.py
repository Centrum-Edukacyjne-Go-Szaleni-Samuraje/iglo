from enum import Enum
from typing import Optional

from django.db import models


class Season(models.Model):
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        ordering = ["-start_date"]

    def __str__(self) -> str:
        return f"{self.start_date} - {self.end_date}"


class Result(Enum):
    WIN = "W"
    LOSE = "L"


class Group(models.Model):
    name = models.CharField(max_length=1)
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name="groups")

    def __str__(self) -> str:
        return f"{self.name} - season: {self.season}"

    def results_as_table(self) -> list[tuple["Player", list[Optional[Result]]]]:
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
                        Result.WIN
                        if game.winner.player == member.player
                        else Result.LOSE
                    )
            table.append((member, row))
        return table


class Player(models.Model):
    nick = models.CharField(max_length=32)

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


class Member(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="members")
    rank = models.CharField(max_length=3, null=True)

    def __str__(self) -> str:
        return f"{self.player} - group: {self.group}"


def game_upload_to(instance, filename) -> str:
    return f"games/game-{instance.id}.sgf"


class Game(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="games")
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
