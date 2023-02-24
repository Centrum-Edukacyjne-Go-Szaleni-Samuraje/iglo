from dataclasses import replace

import pytest

from macmahon.macmahon import Player, GameRecord, Color, ResultType, Scoring

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
player_with_no_games = Player('Gwen', 1050, 0, games=[])
player_with_only_bye = Player('Hugh', 1050, 0, games=[
    GameRecord('', Color.BYE, ResultType.BYE)
])


@pytest.fixture
def players():
    return [alice, bob, cindy, dean, eve]


@pytest.fixture
def sorted_players(players):
    s = Scoring()
    return [score.player for score in s.get_scores(players)]


@pytest.fixture
def registered_players():
    return [
        ('Alice', 400),
        ('Bob', 300),
        ('Cindy', 300),
        ('Dean', 200),
        ('Eve', 100),
        ('Floyd', 50)
    ]


sylwia = Player('Sylwia', 506, 0, [
    GameRecord('Kubit', Color.BLACK, ResultType.LOSE),
    GameRecord('Patryk', Color.WHITE, ResultType.LOSE),
    GameRecord('kam', Color.WHITE, ResultType.WIN),
])
kubit = Player('Kubit', 446, 0, [
    GameRecord('Sylwia', Color.WHITE, ResultType.WIN),
    GameRecord('HornedRat', Color.BLACK, ResultType.WIN),
    GameRecord('Patryk', Color.BLACK, ResultType.WIN),
])
patryk = Player('Patryk', 415, 0, [
    GameRecord('HornedRat', Color.BLACK, ResultType.LOSE),
    GameRecord('Sylwia', Color.BLACK, ResultType.WIN),
    GameRecord('Kubit', Color.WHITE, ResultType.LOSE),
])
hornedrat = Player('HornedRat', 428, 0, [
    GameRecord('Patryk', Color.WHITE, ResultType.WIN),
    GameRecord('Kubit', Color.WHITE, ResultType.LOSE),
    GameRecord('Mithirii', Color.BLACK, ResultType.LOSE),
])
jetbrain = Player('JetBrain', 100, -1, [
    GameRecord('Mithirii', Color.BLACK, ResultType.LOSE),
    GameRecord('kam', Color.WHITE, ResultType.WIN),
    GameRecord('KJKZ', Color.WHITE, ResultType.LOSE),
])
mithirii = Player('Mithirii', 100, -1, [
    GameRecord('JetBrain', Color.WHITE, ResultType.WIN),
    GameRecord('KJKZ', Color.BLACK, ResultType.WIN),
    GameRecord('HornedRat', Color.WHITE, ResultType.WIN),
])
kjkz = Player('KJKZ', 130, -1, [
    GameRecord('kam', Color.BLACK, ResultType.WIN),
    GameRecord('Mithirii', Color.WHITE, ResultType.LOSE),
    GameRecord('JetBrain', Color.BLACK, ResultType.WIN),
])
kam = Player('kam', 100, -1, [
    GameRecord('KJKZ', Color.WHITE, ResultType.LOSE),
    GameRecord('JetBrain', Color.BLACK, ResultType.LOSE),
    GameRecord('Sylwia', Color.BLACK, ResultType.LOSE),
])


@pytest.fixture
def real_live_players():
    return [sylwia, kubit, patryk, hornedrat, jetbrain, mithirii, kjkz, kam]


@pytest.fixture
def real_live_players_round_2(real_live_players):
    return [replace(player, games=player.games[:1]) for player in real_live_players]


@pytest.fixture
def real_live_players_round_3(real_live_players):
    return [replace(player, games=player.games[:2]) for player in real_live_players]


@pytest.fixture
def real_live_players_round_4(real_live_players):
    return [replace(player, games=player.games[:3]) for player in real_live_players]


@pytest.fixture
def real_live_s19r5():
    return [
        Player('Patryk',            395,  0, [
            GameRecord('ric', Color.WHITE, ResultType.WIN),
            GameRecord('Arina', Color.BLACK, ResultType.LOSE),
            GameRecord('MareczKa', Color.BLACK, ResultType.LOSE),
            GameRecord('', Color.BYE, ResultType.BYE)
        ]),
        Player('ric',               499,  0, [
            GameRecord('Patryk', Color.BLACK, ResultType.LOSE),
            GameRecord('MareczKa', Color.WHITE, ResultType.LOSE),
            GameRecord('', Color.BYE, ResultType.BYE),
            GameRecord('Tomko', Color.BLACK, ResultType.WIN)
        ]),
        Player('MareczKa',          100,  0, [
            GameRecord('Arina', Color.WHITE, ResultType.LOSE),
            GameRecord('ric', Color.BLACK, ResultType.WIN),
            GameRecord('Patryk', Color.WHITE, ResultType.WIN),
            GameRecord('sir_husky_potato', Color.WHITE, ResultType.LOSE)
        ]),
        Player('Arina',             100,  0, [
            GameRecord('MareczKa', Color.BLACK, ResultType.WIN),
            GameRecord('Patryk', Color.WHITE, ResultType.WIN),
            GameRecord('sir_husky_potato', Color.BLACK, ResultType.LOSE),
            GameRecord('Polymorph', Color.WHITE, ResultType.WIN)
        ]),
        Player('sir_husky_potato',  400, -1, [
            GameRecord('Tomko', Color.BLACK, ResultType.WIN),
            GameRecord('Polymorph', Color.WHITE, ResultType.WIN),
            GameRecord('Arina', Color.WHITE, ResultType.WIN),
            GameRecord('MareczKa', Color.BLACK, ResultType.WIN)
        ]),
        Player('Tomko',             100, -1, [
            GameRecord('sir_husky_potato', Color.WHITE, ResultType.LOSE),
            GameRecord('', Color.BYE, ResultType.BYE),
            GameRecord('Polymorph', Color.BLACK, ResultType.WIN),
            GameRecord('ric', Color.WHITE, ResultType.LOSE)
        ]),
        Player('Polymorph',          18, -1, [
            GameRecord('', Color.BYE, ResultType.BYE),
            GameRecord('sir_husky_potato', Color.BLACK, ResultType.LOSE),
            GameRecord('Tomko', Color.WHITE, ResultType.LOSE),
            GameRecord('Arina', Color.BLACK, ResultType.LOSE)
        ])
    ]
