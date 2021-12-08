import pytest

from macmahon import Player, Scoring, Score
from macmahon.tests.conftest import alice, bob, dean, eve, cindy


@pytest.mark.parametrize('player, expected_score', [
    (alice, 2),
    (bob, .5),
    (dean, .5),
])
def test_player_score(player: Player, expected_score: float):
    s = Scoring()
    score = s.player_score(player)
    assert score == expected_score


def test_scoring(players):
    expected = [Score(alice, score=2, sos=2, sosos=10.5),
                Score(eve, score=1.5, sos=1.5, sosos=7.5),
                Score(cindy, score=1, sos=4, sosos=6.5),
                Score(bob, score=0.5, sos=3.5, sosos=3.5),
                Score(dean, score=0.5, sos=3, sosos=6)]

    scoring = Scoring()
    players_sorted = scoring.get_scores(players)
    assert players_sorted == expected
