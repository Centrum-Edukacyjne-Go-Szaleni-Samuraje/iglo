import random
from operator import itemgetter
from unittest import mock

import pytest

from macmahon.macmahon import MacMahon, Color, ColorPreference, Pair, prepare_next_round
from macmahon.tests.conftest import alice, bob, cindy, dean, eve, floyd, player_with_no_games, player_with_only_bye, \
    sylwia, patryk, jetbrain, kjkz, kubit, hornedrat, mithirii, kam


def test_get_bye_odd_players(players):
    mm = MacMahon(players)
    bye = mm._get_bye(players)
    assert bye == cindy


def test_get_bye_even_players(players):
    players = players[:4]
    mm = MacMahon(players)
    bye = mm._get_bye(players)
    assert bye is None


@pytest.mark.parametrize('player, expected', [
    (alice, ColorPreference(True, True, True, False)),
    (bob, ColorPreference(True, True, False, True)),
    (dean, ColorPreference(False, True, False, True)),
    (floyd, ColorPreference(True, False, True, False)),
    (player_with_no_games, ColorPreference(True, True, True, True)),
    (player_with_only_bye, ColorPreference(True, True, True, True))
])
def test_get_color_preference(player, expected):
    mm = MacMahon([])
    color_preference = mm._get_color_preference(player)
    assert color_preference == expected


def test_determine_color_preference_should_play_different_colors():
    p1_preference = ColorPreference(True, True, True, False)
    p2_preference = ColorPreference(True, True, False, True)
    mm = MacMahon([])
    colors = mm._determine_colors(p1_preference, p2_preference)
    assert colors == (Color.BLACK, Color.WHITE)


def test_determine_color_preference_should_play_same_colors():
    p1_preference = ColorPreference(True, True, True, False)
    p2_preference = ColorPreference(True, True, True, False)
    mm = MacMahon([])
    colors = mm._determine_colors(p1_preference, p2_preference)
    assert colors == (Color.BLACK, Color.WHITE)


def test_determine_color_preference_can_play_different_colors():
    p1_preference = ColorPreference(True, False, True, False)
    p2_preference = ColorPreference(False, True, False, True)
    mm = MacMahon([])
    colors = mm._determine_colors(p1_preference, p2_preference)
    assert colors == (Color.BLACK, Color.WHITE)


def test_determine_color_preference_can_play_same_colors():
    p1_preference = ColorPreference(True, False, True, False)
    p2_preference = ColorPreference(True, False, True, False)
    mm = MacMahon([])
    colors = mm._determine_colors(p1_preference, p2_preference)
    assert colors == (Color.BLACK, Color.WHITE)


def test_determine_color_preference_second_player_cannot_play_one_colors():
    p1_preference = ColorPreference(True, True, True, False)
    p2_preference = ColorPreference(True, False, True, False)
    mm = MacMahon([])
    colors = mm._determine_colors(p1_preference, p2_preference)
    assert colors == (Color.WHITE, Color.BLACK)


def test_determine_color_preference_second_player_should_not_play_one_colors():
    p1_preference = ColorPreference(True, True, True, True)
    p2_preference = ColorPreference(True, True, True, False)
    mm = MacMahon([])
    colors = mm._determine_colors(p1_preference, p2_preference)
    assert colors == (Color.WHITE, Color.BLACK)


def test_do_nigiri_if_players_played_no_game_yet():
    p1_preference = ColorPreference(True, True, True, True)
    p2_preference = ColorPreference(True, True, True, True)
    mm = MacMahon([])
    with mock.patch.object(random, 'shuffle') as shuffle_mock:
        mm._determine_colors(p1_preference, p2_preference)
        shuffle_mock.assert_called_once_with([Color.WHITE, Color.BLACK])


def test_possible_opponents(players):
    expected = itemgetter(1, 3, 4)(players)
    mm = MacMahon(players)
    possible_opponents = mm._possible_opponents(floyd)
    assert list(possible_opponents) == list(expected)


def test_get_pairing(sorted_players):
    expected_pairs = [
        Pair(alice, eve),
        Pair(bob, dean)
    ]
    mm = MacMahon(sorted_players)
    pairs, bye = mm.get_pairing()
    assert bye == cindy
    assert pairs == expected_pairs


def test_real_live_round_2(real_live_players_round_2):
    pairs, bye = prepare_next_round(real_live_players_round_2)
    pair1, pair2, pair3, pair4 = pairs

    assert pair1.black.name == kubit.name
    assert pair1.white.name == hornedrat.name
    assert pair2.black.name == mithirii.name
    assert pair2.white.name == patryk.name
    assert pair3.black.name == jetbrain.name
    assert pair3.white.name == kjkz.name
    assert pair4.black.name == kam.name
    assert pair4.white.name == sylwia.name
    assert bye is None


def test_real_live_round_3(real_live_players_round_3):
    pairs, bye = prepare_next_round(real_live_players_round_3)
    pair1, pair2, pair3, pair4 = pairs

    assert pair1.black.name == kubit.name
    assert pair1.white.name == patryk.name
    assert pair2.black.name == sylwia.name
    assert pair2.white.name == mithirii.name
    assert pair3.black.name == hornedrat.name
    assert pair3.white.name == kam.name
    assert pair4.black.name == jetbrain.name
    assert pair4.white.name == kjkz.name
    assert bye is None


def test_real_live_round_4(real_live_players_round_4):
    pairs, bye = prepare_next_round(real_live_players_round_4)
    pair1, pair2, pair3, pair4 = pairs

    assert pair1.black.name == mithirii.name
    assert pair1.white.name == kubit.name
    assert pair2.black.name == patryk.name
    assert pair2.white.name == kam.name
    assert pair3.black.name == sylwia.name
    assert pair3.white.name == kjkz.name
    assert pair4.black.name == jetbrain.name
    assert pair4.white.name == hornedrat.name
    assert bye is None
