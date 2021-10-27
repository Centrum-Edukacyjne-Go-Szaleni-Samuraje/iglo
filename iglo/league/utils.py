from collections import deque
from typing import Generator, Deque


def _round_robin_even(d: Deque, n: int) -> Generator[list[tuple[int, int]], None, None]:
    for i in range(n - 1):
        yield [tuple(sorted((d[j], d[-j - 1]))) for j in range(n // 2)]
        d[0], d[-1] = d[-1], d[0]
        d.rotate()


def _round_robin_odd(d: Deque, n: int) -> Generator[list[tuple[int, int]], None, None]:
    for i in range(n):
        yield [tuple(sorted((d[j], d[-j - 1]))) for j in range(n // 2)]
        d.rotate()


def round_robin(n: int) -> list[list[tuple[int, int]]]:
    d = deque(range(n))
    if n % 2 == 0:
        return list(_round_robin_even(d, n))
    else:
        return list(_round_robin_odd(d, n))
