import pytest

from macmahon import BasicInitialOrdering


@pytest.mark.parametrize('players_number, bars_number, expected_bars_sizes', [
    (5, 2, [3, 2]),
    (6, 2, [3, 3]),
    (6, 3, [2, 2, 2]),
    (7, 2, [4, 3]),
    (7, 3, [3, 2, 2]),
    (8, 3, [3, 3, 2]),
    (17, 2, [9, 8]),
    (17, 3, [6, 6, 5]),
    (17, 4, [5, 4, 4, 4])
])
def test_basic_initial_ordering__get_bars_sizes(players_number, bars_number, expected_bars_sizes):
    io = BasicInitialOrdering(bars_number)
    bars_sizes = io.get_bars_sizes(players_number, bars_number)
    assert bars_sizes == expected_bars_sizes


def test_basic_initial_ordering__order_5_players_2_bars(registered_players):
    registered_players = registered_players[:5]
    io = BasicInitialOrdering(2)
    ordered_players = io.order(registered_players)
    ordered_names = [p.name for p in ordered_players]
    initial_score = [p.initial_score for p in ordered_players]
    assert ordered_names == ['Alice', 'Bob', 'Cindy', 'Dean', 'Eve']
    assert initial_score == [0, 0, 0, -1, -1]


def test_basic_initial_ordering__order_5_players_3_bars(registered_players):
    registered_players = registered_players[:5]
    io = BasicInitialOrdering(3)
    ordered_players = io.order(registered_players)
    ordered_names = [p.name for p in ordered_players]
    initial_score = [p.initial_score for p in ordered_players]
    assert ordered_names == ['Alice', 'Bob', 'Cindy', 'Dean', 'Eve']
    assert initial_score == [0, 0, -1, -1, -2]


def test_basic_initial_ordering__order_6_players_2_bars(registered_players):
    registered_players = registered_players[:6]
    io = BasicInitialOrdering(2)
    ordered_players = io.order(registered_players)
    ordered_names = [p.name for p in ordered_players]
    initial_score = [p.initial_score for p in ordered_players]
    assert ordered_names == ['Alice', 'Bob', 'Cindy', 'Dean', 'Eve', 'Floyd']
    assert initial_score == [0, 0, 0, -1, -1, -1]


def test_basic_initial_ordering__order_6_players_3_bars(registered_players):
    registered_players = registered_players[:6]
    io = BasicInitialOrdering(3)
    ordered_players = io.order(registered_players)
    ordered_names = [p.name for p in ordered_players]
    initial_score = [p.initial_score for p in ordered_players]
    assert ordered_names == ['Alice', 'Bob', 'Cindy', 'Dean', 'Eve', 'Floyd']
    assert initial_score == [0, 0, -1, -1, -2, -2]
