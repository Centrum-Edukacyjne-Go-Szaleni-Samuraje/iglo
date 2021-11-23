import pytest

from macmahon import GameRecord, Player, ResultType, Color, Scoring

alice = Player('Alice', 400, 0, games=[
    GameRecord('Bob', Color.BLACK, ResultType.WIN),
    GameRecord('Cindy', Color.WHITE, ResultType.WIN),
    GameRecord('Dean', Color.WHITE, ResultType.LOSE),
])
bob = Player('Bob', 300, 0, games=[
    GameRecord('Alice', Color.WHITE, ResultType.LOSE),
    GameRecord('Eve', Color.BLACK, ResultType.LOSE),
    GameRecord('', Color.BYE, ResultType.BYE),
])
cindy = Player('Cindy', 300, 0, games=[
    GameRecord('Dean', Color.WHITE, ResultType.WIN),
    GameRecord('Alice', Color.BLACK, ResultType.LOSE),
    GameRecord('Eve', Color.WHITE, ResultType.LOSE),
])
dean = Player('Dean', 200, -1, games=[
    GameRecord('Cindy', Color.BLACK, ResultType.LOSE),
    GameRecord('', Color.BYE, ResultType.BYE),
    GameRecord('Alice', Color.BLACK, ResultType.WIN),
])
eve = Player('Eve', 100, -1, games=[
    GameRecord('', Color.BYE, ResultType.BYE),
    GameRecord('Bob', Color.WHITE, ResultType.WIN),
    GameRecord('Cindy', Color.BLACK, ResultType.WIN),
])
floyd = Player('Floyd', 50, -2, games=[
    GameRecord('Alice', Color.WHITE, ResultType.WIN),
    GameRecord('', Color.BYE, ResultType.BYE),
    GameRecord('Cindy', Color.WHITE, ResultType.LOSE),
])


@pytest.fixture
def players():
    return [alice, bob, cindy, dean, eve]


@pytest.fixture
def sorted_players(players):
    s = Scoring()
    return [score.player for score in s.get_scores(players)]
