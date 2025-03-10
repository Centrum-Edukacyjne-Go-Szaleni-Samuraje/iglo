import random
from collections import deque, defaultdict
from enum import Enum
from typing import Generator, Deque, Union, Tuple

class Bye(Enum):
    ByeWin = True
    ByeLoss = False

Pairing = list[list[Union[tuple[int, int], tuple[int, Bye]]]]


def _round_robin_even(d: Deque, n: int) -> Generator[list[tuple[int, int]], None, None]:
    for i in range(n - 1):
        yield [tuple(sorted((d[j], d[-j - 1]))) for j in range(n // 2)]
        d[0], d[-1] = d[-1], d[0]
        d.rotate()


def _round_robin_odd(d: Deque, n: int) -> Generator[list[tuple[int, int]], None, None]:
    for i in range(n):
        yield [tuple(sorted((d[j], d[-j - 1]))) for j in range(n // 2)]
        d.rotate()


def round_robin(n: int) -> Pairing:
    d = deque(range(n))
    if n % 2 == 0:
        return list(_round_robin_even(d, n))
    else:
        return list(_round_robin_odd(d, n))


def banded_round_robin(player_count: int, band_size: int, add_byes: bool) -> Pairing:
  by_round = []
  for player_distance in range(band_size, 0, -1):
    even_round = set() # round nr 2*player_distance
    odd_round = set() # round nr 2*player_distance + 1
    for player in range(player_count):
      opponent = player + player_distance
      if opponent < player_count:
        m = odd_round if (player // player_distance) % 2 == 0 else even_round
        m.add((player, opponent))
    by_round.extend([even_round, odd_round])

  # Add BYE games for players without matches in certain rounds
  if add_byes:
    all_players = set(range(player_count))

    # Post-process each round to add BYE games
    for round_idx, round_set in enumerate(by_round):
      # Find players in this round
      players_in_round = set()
      for p1, p2 in round_set:
        players_in_round.add(p1)
        players_in_round.add(p2)

      # Find missing players
      missing_players = all_players - players_in_round

      # Add appropriate BYE games
      for player in missing_players:
        if player < band_size:
          # Top players get BYE losses
          by_round[round_idx].add((player, Bye.ByeLoss))
        elif player >= player_count - band_size:
          # Bottom players get BYE wins
          by_round[round_idx].add((player, Bye.ByeWin))

  by_round = list(map(list, by_round))
  return by_round


def shuffle_colors(paring: Pairing, randomize: bool = True) -> Pairing:
    colors_count = defaultdict(lambda: defaultdict(int))
    result = []
    for not_shuffled_round in paring:
        shuffled_round = []
        for pair in not_shuffled_round:
            # Check if this is a special BYE pair
            if isinstance(pair[0], Bye) or isinstance(pair[1], Bye):
                # This is a BYE game, we could shuffle, but for simplicity we don't.
                shuffled_round.append(pair)
            else:
                # Regular game between two players
                if randomize and random.randint(0, 1):
                    pair = (pair[1], pair[0])
                if colors_count[pair[0]]["B"] > colors_count[pair[0]]["W"]:
                    pair = (pair[1], pair[0])
                colors_count[pair[0]]["B"] += 1
                colors_count[pair[1]]["W"] += 1
                shuffled_round.append(pair)
        result.append(shuffled_round)
    return result
