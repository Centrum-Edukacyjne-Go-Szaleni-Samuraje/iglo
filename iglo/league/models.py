from enum import Enum
from typing import Optional, cast

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
            frozenset({game.black, game.white}): game for game in self.games.all()
        }
        for player in self.players.all():
            row = []
            for other_player in self.players.all():
                if player == other_player:
                    row.append(None)
                else:
                    game = players_to_game[frozenset({player, other_player})]
                    row.append(Result.WIN if game.winner == player else Result.LOSE)
            table.append((player, row))
        return table


class Player(models.Model):
    name = models.CharField(
        max_length=32
    )  # TODO: this will be FK to User/Account in the feature
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="players")

    def __str__(self) -> str:
        return f"{self.name} - group: {self.group}"


class Game(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="games")
    black = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name="games_as_black"
    )
    white = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name="games_as_white"
    )
    winner = models.ForeignKey(
        Player, null=True, on_delete=models.CASCADE, related_name="won_games"
    )

    def __str__(self) -> str:
        return f"B: {self.black} - W: {self.white} - winner: {self.winner}"
