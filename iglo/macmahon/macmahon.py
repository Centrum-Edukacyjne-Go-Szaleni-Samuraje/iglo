import math

import numpy as np

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Optional, Tuple

from macmahon.optimization import find_maximum_assignment


class ResultType(str, Enum):
    WIN = 'win'
    LOSE = 'lose'
    TIE = 'tie'
    BYE = 'bye'


class Color(str, Enum):
    BLACK = 'black'
    WHITE = 'white'
    BYE = 'bye'


@dataclass(frozen=True)
class GameRecord:
    opponent: Optional[str]
    color: str
    result: ResultType


@dataclass(frozen=True)
class Player:
    name: str
    rating: int
    initial_score: int = 0
    games: list[GameRecord] = field(default_factory=list)


@dataclass(frozen=True)
class Pair:
    black: Player
    white: Player


@dataclass(order=True)
class Score:
    player: Player = field(compare=False)
    score: float = 0
    sos: float = 0
    sosos: float = 0


@dataclass(frozen=True)
class ColorPreference:
    as_black: float
    as_white: float


class BasicInitialOrdering:
    def __init__(self, number_of_bars: int) -> None:
        self.number_of_bars = number_of_bars

    def order(self, players_list: list[Tuple[str, int]]) -> list[Player]:
        players = []
        bars_sizes = self.get_bars_sizes(len(players_list), self.number_of_bars)
        players_left = players_list[:]
        initial_score = 0
        for bar_size in bars_sizes:
            current_bar, players_left = players_left[:bar_size], players_left[bar_size:]
            for name, rating in current_bar:
                players.append(Player(name, rating, initial_score))
            initial_score = initial_score - 1
        return players

    def get_bars_sizes(self, number_of_players: int, number_of_bars: int) -> list[int]:
        bars_sizes = []
        players_left = number_of_players
        bars_left = number_of_bars
        while bars_left:
            bar_size = math.ceil(players_left / bars_left)
            bars_sizes.append(bar_size)
            players_left = players_left - bar_size
            bars_left = bars_left - 1
        return bars_sizes


class Scoring:
    def __init__(self,
                 win_points: float = 1,
                 lose_points: float = 0,
                 tie_points: float = .5,
                 bye_points: float = .5) -> None:
        self.scoring_scheme = {
            ResultType.WIN: win_points,
            ResultType.LOSE: lose_points,
            ResultType.TIE: tie_points,
            ResultType.BYE: bye_points
        }

    def player_score(self, player: Player) -> float:
        return player.initial_score + sum(self.scoring_scheme[game.result] for game in player.games)

    def get_scores(self, players: Iterable[Player]) -> list[Score]:
        scores = {}
        for player in players:
            score = self.player_score(player)
            scores[player.name] = Score(player, score)
        for player in players:
            opponents = (g.opponent for g in player.games if g.result != ResultType.BYE)
            sos = sum(scores[o].score for o in opponents)
            scores[player.name].sos = sos
        for player in players:
            opponents = (g.opponent for g in player.games if g.result != ResultType.BYE)
            sosos = sum(scores[o].sos for o in opponents)
            scores[player.name].sosos = sosos
        return sorted(scores.values(), reverse=True)


Pairing = Tuple[list[Pair], Optional[Player]]


class MacMahon:
    def __init__(self, sorted_players: list[Player]):
        self.players: list[Player] = sorted_players[:]

    def get_pairing(self) -> Pairing:
        bye = self._get_bye()
        pairs = self._get_pairs()
        return pairs, bye

    def _get_pairs(self):
        mmpm = MacMahonPreferenceMatrix(self.players)
        names, preference_matrix = mmpm.get_preference_matrix()
        indices = find_maximum_assignment(preference_matrix)
        pairs = []
        for black_player_index, white_player_index in indices:
            pairs.append(Pair(
                black=self.players[black_player_index],
                white=self.players[white_player_index]
            ))
        return pairs

    def _get_bye(self) -> Optional[Player]:
        if len(self.players) % 2 == 0:
            return None
        for player in self.players[::-1]:
            can_bye = not any(g.result == ResultType.BYE for g in player.games)
            if can_bye:
                self.players.remove(player)
                return player


FORBIDDEN_MATCH = 0


class MacMahonPreferenceMatrix:
    def __init__(self, players: list[Player]):
        self.players = players
        self.names: list[str] = None
        self.position: dict[str, int] = None
        self.possible_opponents: dict[str, list[str]] = None
        self.color_preference: dict[str, ColorPreference] = None
        self.pairs: list[list[Pair]]
        self.n: int = None

    def get_preference_matrix(self):
        self.names = [player.name for player in self.players]
        self.n = len(self.names)
        self.position = {player.name: pos for pos, player in enumerate(self.players)}
        self.possible_opponents = {player.name: self._get_possible_opponents(player) for player in self.players}
        self.color_preference = {player.name: self._get_player_color_preference(player) for player in self.players}

        preferences_matrix = np.full((self.n, self.n), 0)
        for i in range(self.n):
            for j in range(self.n):
                player1, player2 = self.names[i], self.names[j]
                preferences_matrix[i, j] = self._get_match_preference(player1, player2)
        return self.names, preferences_matrix

    def _get_possible_opponents(self, player: Player) -> list[str]:
        past_opponents = [game.opponent for game in player.games]
        excluded_players = past_opponents + [player.name]
        return [opponent.name for opponent in self.players if opponent.name not in excluded_players]

    def _get_match_preference(self, player1: str, player2: str):
        if player2 not in self.possible_opponents[player1]:
            return FORBIDDEN_MATCH

        pos1, pos2 = self.position[player1], self.position[player2]
        distance_preference = (self.n - abs(pos1 - pos2)) / (self.n - 1)

        black, white = self.color_preference[player1].as_black, self.color_preference[player2].as_white
        color_preference = min(black, white)

        preference = distance_preference * color_preference
        return preference

    @staticmethod
    def _get_player_color_preference(player: Player) -> ColorPreference:
        as_black = len([game for game in player.games if game.color == Color.BLACK])
        as_white = len([game for game in player.games if game.color == Color.WHITE])
        return ColorPreference(
            as_black=1 / (max(as_black - as_white, 0) + 1),
            as_white=1 / (max(as_white - as_black, 0) + 1)
        )


def prepare_next_round(players: list[Player]) -> Pairing:
    scoring = Scoring()
    scores = scoring.get_scores(players)
    sorted_players = [score.player for score in scores]
    macmahon = MacMahon(sorted_players)
    return macmahon.get_pairing()
