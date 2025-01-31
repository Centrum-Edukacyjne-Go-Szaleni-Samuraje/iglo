import random
from collections import deque, defaultdict
from typing import Generator, Deque

Pairing = list[list[tuple[int, int]]]


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


def banded_round_robin(player_count: int, band_size: int) -> Pairing:
  by_round = []
  for player_distance in range(band_size, 0, -1):
    round_2pd_0 = set() # round 2*player_distance
    round_2pd_1 = set() # round 2*player_distance + 1
    for player in range(player_count):
      opponent = player + player_distance
      if opponent < player_count:
        m = round_2pd_1 if (player // player_distance) % 2 == 0 else round_2pd_0
        m.add((player, opponent))
    by_round.append(round_2pd_0)
    by_round.append(round_2pd_1)
  by_round = list(map(list, by_round))
  return by_round


def shuffle_colors(paring: Pairing, randomize: bool = True) -> Pairing:
    colors_count = defaultdict(lambda: defaultdict(int))
    result = []
    for not_shuffled_round in paring:
        shuffled_round = []
        for pair in not_shuffled_round:
            if randomize and random.randint(0, 1):
                pair = (pair[1], pair[0])
            if colors_count[pair[0]]["B"] > colors_count[pair[0]]["W"]:
                pair = (pair[1], pair[0])
            colors_count[pair[0]]["B"] += 1
            colors_count[pair[1]]["W"] += 1
            shuffled_round.append(pair)
        result.append(shuffled_round)
    return result
