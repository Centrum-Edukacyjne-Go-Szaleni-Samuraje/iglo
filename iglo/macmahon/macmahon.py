import math
import random

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Optional, Iterator, Tuple


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
    can_play_as_black: bool
    can_play_as_white: bool
    should_play_as_black: bool
    should_play_as_white: bool


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
        self.players = sorted_players[:]
        self.position = {player.name: pos for pos, player in enumerate(self.players)}

    def get_pairing(self) -> Pairing:
        pairs = []
        bye = self._get_bye(self.players)
        while len(self.players):
            player1 = self._get_first_player()
            player2 = self._get_second_player(player1)
            player1_color_preference = self._get_color_preference(player1)
            player2_color_preference = self._get_color_preference(player2)
            player1_color, _ = self._determine_colors(player1_color_preference, player2_color_preference)
            if player1_color == Color.BLACK:
                pairs.append(Pair(player1, player2))
            else:
                pairs.append(Pair(player2, player1))
        return pairs, bye

    def _get_bye(self, players: list[Player]) -> Optional[Player]:
        if len(players) % 2 == 0:
            return None
        for player in players[::-1]:
            can_bye = not any(g.result == ResultType.BYE for g in player.games)
            if can_bye:
                players.remove(player)
                return player

    def _get_first_player(self) -> Player:
        sorted_players = sorted(self.players, key=lambda player: (len(list(self._possible_opponents(player))), self.position[player.name]))
        first_player = sorted_players[0]
        self.players.remove(first_player)
        return first_player

    def _get_second_player(self, player1: Player) -> Player:
        player1_position = self.position[player1.name]
        possible_opponents = self._possible_opponents(player1)
        sorted_opponents = sorted(possible_opponents, key=lambda player: abs(self.position[player.name] - player1_position))
        second_player = sorted_opponents[0]
        self.players.remove(second_player)
        return second_player

    def _possible_opponents(self, player: Player) -> Iterator[Player]:
        past_opponents = [g.opponent for g in player.games]
        excluded_players = past_opponents + [player.name]
        return (opponent for opponent in self.players if opponent.name not in excluded_players)

    def _get_color_preference(self, player: Player) -> ColorPreference:
        color_history = [g.color for g in player.games if g.color != Color.BYE]
        if not color_history:
            return ColorPreference(True, True, True, True)
        games_as_black = sum(1 for c in color_history if c == Color.BLACK)
        games_as_white = sum(1 for c in color_history if c == Color.WHITE)
        can_play_black = games_as_black - games_as_white < 2
        can_play_white = games_as_white - games_as_black < 2
        should_play_black = color_history[-1] == Color.WHITE
        should_play_white = color_history[-1] == Color.BLACK
        return ColorPreference(can_play_black, can_play_white, should_play_black, should_play_white)

    def _determine_colors(self, p1: ColorPreference, p2: ColorPreference) -> Tuple[Color, Color]:
        if not p1.can_play_as_black:
            return Color.WHITE, Color.BLACK
        if not p1.can_play_as_white:
            return Color.BLACK, Color.WHITE
        if not p2.can_play_as_black:
            return Color.BLACK, Color.WHITE
        if not p2.can_play_as_white:
            return Color.WHITE, Color.BLACK
        if not p1.should_play_as_black:
            return Color.WHITE, Color.BLACK
        if not p1.should_play_as_white:
            return Color.BLACK, Color.WHITE
        if not p2.should_play_as_black:
            return Color.BLACK, Color.WHITE
        if not p2.should_play_as_white:
            return Color.WHITE, Color.BLACK
        colors = [Color.WHITE, Color.BLACK]
        random.shuffle(colors)
        return tuple(colors)


def prepare_next_round(players: list[Player]) -> Pairing:
    scoring = Scoring()
    scores = scoring.get_scores(players)
    sorted_players = [score.player for score in scores]
    macmahon = MacMahon(sorted_players)
    return macmahon.get_pairing()
