import random
from operator import itemgetter
from unittest import mock

import pytest

from macmahon.macmahon import MacMahon, Color, ColorPreference, Pair, prepare_next_round, Scoring, \
    MacMahonPreferenceMatrix
from macmahon.tests.conftest import alice, bob, cindy, dean, eve, floyd, player_with_no_games, player_with_only_bye


def test_get_bye_odd_players(players):
    mm = MacMahon(players)
    bye = mm._get_bye()
    assert bye == cindy


def test_get_bye_even_players(players):
    players = players[:4]
    mm = MacMahon(players)
    bye = mm._get_bye()
    assert bye is None


# @pytest.mark.parametrize('player, expected', [
#     (alice, ColorPreference(0, 1)),
#     (bob, ColorPreference(0, 0)),
#     (dean, ColorPreference(2, 0)),
#     (floyd, ColorPreference(0, 2)),
#     (player_with_no_games, ColorPreference(0, 0)),
#     (player_with_only_bye, ColorPreference(0, 0))
# ])
# def test_get_player_color_preference(player, expected):
#     color_preference = MacMahon._get_player_color_preference(player)
#     assert color_preference == expected


def test_possible_opponents(players):
    players_names = [player.name for player in players]
    expected_names = itemgetter(1, 3, 4)(players_names)
    mm = MacMahonPreferenceMatrix(players)
    possible_opponents = mm._get_possible_opponents(floyd)
    assert list(possible_opponents) == list(expected_names)


# def test_get_pairing(sorted_players):
#     expected_pairs = [
#         Pair(alice, eve),
#         Pair(bob, dean)
#     ]
#     mm = MacMahon(sorted_players)
#     pairs, bye = mm.get_pairing()
#     assert bye == cindy
#     assert pairs == expected_pairs
#
#
# def test_real_live_round_2(real_live_players_round_2):
#     pairs, bye = prepare_next_round(real_live_players_round_2)
#     pair1, pair2, pair3, pair4 = pairs
#
#     assert pair1.as_black.name == 'Kubit'
#     assert pair1.white.name == 'HornedRat'
#     assert pair2.as_black.name == 'Patryk'
#     assert pair2.white.name == 'Sylwia'
#     assert pair3.as_black.name == 'Mithirii'
#     assert pair3.white.name == 'KJKZ'
#     assert pair4.as_black.name == 'kam'
#     assert pair4.white.name == 'JetBrain'
#     assert bye is None
#
#
# def test_real_live_round_3(real_live_players_round_3):
#     pairs, bye = prepare_next_round(real_live_players_round_3)
#     pair1, pair2, pair3, pair4 = pairs
#
#     assert pair1.as_black.name == 'Kubit'
#     assert pair1.white.name == 'Patryk'
#     assert pair2.as_black.name == 'HornedRat'
#     assert pair2.white.name == 'Mithirii'
#     assert pair3.as_black.name == 'Sylwia'
#     assert pair3.white.name == 'kam'
#     assert pair4.as_black.name == 'JetBrain'
#     assert pair4.white.name == 'KJKZ'
#     assert bye is None
#
#
# def test_real_live_round_4(real_live_players_round_4):
#     pairs, bye = prepare_next_round(real_live_players_round_4)
#     pair1, pair2, pair3, pair4 = pairs
    #
    # assert pair1.black.name == 'Mithirii'
    # assert pair1.white.name == 'Kubit'
    # assert pair2.black.name == 'kam'
    # assert pair2.white.name == 'HornedRat'
    # assert pair3.black.name == 'Patryk'
    # assert pair3.white.name == 'KJKZ'
    # assert pair4.black.name == 'Sylwia'
    # assert pair4.white.name == 'JetBrain'
#     assert bye is None
#
#
# def test_real_live_s19r5(real_live_s19r5):
#     pairs, bye = prepare_next_round(real_live_s19r5)
#
#     assert bye.name == 'MareczKa'


# def test_genetic_macmahon(real_live_players_round_4):
#     scoring = Scoring()
#     scores = scoring.get_scores(real_live_players_round_4)
#     sorted_players = [score.player for score in scores]
#     macmahon = GeneticMacMahon(sorted_players)
#
#     print(macmahon.get_pairing())
#     print(macmahon.get_pairing())
#     print(macmahon.get_pairing())
#     print(macmahon.get_pairing())
#     # (['Polymorph', 'ric', 'Tomko', 'Arina', 'sir_husky_potato', 'Patryk'], < Player: MareczKa >)
#     # (['ric', 'Polymorph', 'Tomko', 'Arina', 'sir_husky_potato', 'Patryk'], <Player: MareczKa>)
#     # ['sir_husky_potato', 'Patryk', 'Polymorph', 'ric', 'Tomko', 'Arina'], < Player: MareczKa >)
#     # (['Tomko', 'Arina', 'sir_husky_potato', 'Patryk', 'Polymorph', 'ric'], < Player: MareczKa >)
#
#     # iterations = 57
#     # fitness = 0.5
#     # (['Mithirii', 'Kubit', 'JetBrain', 'Patryk', 'kam', 'HornedRat', 'Sylwia', 'KJKZ'], None)
#     # iterations = 54
#     # fitness = 0.625
#     # (['HornedRat', 'kam', 'JetBrain', 'Patryk', 'Mithirii', 'Kubit', 'Sylwia', 'KJKZ'], None)
#     # iterations = 53
#     # fitness = 0.5
#     # (['JetBrain', 'HornedRat', 'Mithirii', 'Kubit', 'Sylwia', 'KJKZ', 'kam', 'Patryk'], None)
#     # iterations = 66
#     # fitness = 0.5
#     # (['HornedRat', 'KJKZ', 'JetBrain', 'Sylwia', 'Mithirii', 'Kubit', 'kam', 'Patryk'], None)
