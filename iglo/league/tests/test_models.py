import datetime

from django.conf import settings
from django.db.models import Q
from django.test import TestCase

from league.models import (
    MemberResult,
    Season,
    SeasonState,
    Game,
    Round,
    Member,
    GroupType,
    GamesWithoutResultError,
)
from league.tests.factories import (
    MemberFactory,
    GroupFactory,
    GameFactory,
    SeasonFactory,
    PlayerFactory,
)


class MemberTestCase(TestCase):
    def test_points(self):
        group = GroupFactory()
        member_1 = MemberFactory(group=group)
        member_2 = MemberFactory(group=group)
        member_3 = MemberFactory(group=group)
        member_4 = MemberFactory(group=group)
        GameFactory(group=group, white=member_1, black=member_2, winner=member_1)
        GameFactory(group=group, white=member_3, black=member_1, winner=member_1)
        GameFactory(group=group, white=member_1, black=member_4, winner=member_4)

        self.assertEqual(member_1.points, 2)

    def test_sodos(self):
        group = GroupFactory()
        member_1 = MemberFactory(group=group)
        member_2 = MemberFactory(group=group)
        member_3 = MemberFactory(group=group)
        member_4 = MemberFactory(group=group)
        GameFactory(group=group, white=member_1, black=member_2, winner=member_1)
        GameFactory(group=group, white=member_3, black=member_1, winner=member_3)
        GameFactory(group=group, white=member_1, black=member_4, winner=member_4)
        GameFactory(group=group, white=member_2, black=member_3, winner=member_2)
        GameFactory(group=group, white=member_4, black=member_2, winner=member_2)
        GameFactory(group=group, white=member_3, black=member_4, winner=member_3)

        self.assertEqual(member_1.sodos, 2)

    def test_result_for_promotion(self):
        group = GroupFactory(name="B")
        member_1 = MemberFactory(group=group)
        member_2 = MemberFactory(group=group)
        member_3 = MemberFactory(group=group)
        GameFactory(group=group, white=member_1, black=member_2, winner=member_1)
        GameFactory(group=group, white=member_1, black=member_3, winner=member_1)
        GameFactory(group=group, white=member_2, black=member_3, winner=member_2)

        self.assertEqual(member_1.result, MemberResult.PROMOTION)

    def test_result_for_relegation(self):
        group = GroupFactory()
        member_1 = MemberFactory(group=group)
        member_2 = MemberFactory(group=group)
        member_3 = MemberFactory(group=group)
        GameFactory(group=group, white=member_1, black=member_2, winner=member_1)
        GameFactory(group=group, white=member_1, black=member_3, winner=member_1)
        GameFactory(group=group, white=member_2, black=member_3, winner=member_2)

        self.assertEqual(member_3.result, MemberResult.RELEGATION)

    def test_result_for_stay(self):
        group = GroupFactory()
        member_1 = MemberFactory(group=group)
        member_2 = MemberFactory(group=group)
        member_3 = MemberFactory(group=group)
        GameFactory(group=group, white=member_1, black=member_2, winner=member_1)
        GameFactory(group=group, white=member_1, black=member_3, winner=member_1)
        GameFactory(group=group, white=member_2, black=member_3, winner=member_2)

        self.assertEqual(member_2.result, MemberResult.STAY)


class SeasonTestCase(TestCase):
    def test_prepare_season_from_previous(self):
        season = SeasonFactory(promotion_count=1, state=SeasonState.FINISHED, number=1)
        group_a_member_1, group_a_member_2, group_a_member_3 = self._create_group(season=season, name="A")
        group_b_member_1, group_b_member_2, group_b_member_3 = self._create_group(season=season, name="B")

        new_season = Season.objects.prepare_season(
            start_date=datetime.date(2021, 1, 1), players_per_group=3, promotion_count=1
        )

        self.assertEqual(new_season.state, SeasonState.DRAFT)
        self.assertEqual(new_season.number, 2)
        self.assertEqual(new_season.start_date, datetime.date(2021, 1, 1))
        self.assertEqual(new_season.end_date, datetime.date(2021, 1, 14))
        self.assertEqual(new_season.players_per_group, 3)
        self.assertEqual(new_season.promotion_count, 1)
        self.assertEqual(new_season.groups.count(), 2)
        new_group_a = new_season.groups.get(name="A")
        self.assertEqual(new_group_a.type, GroupType.ROUND_ROBIN)
        self.assertEqual(new_group_a.members.count(), 3)
        self._check_players_order(
            group=new_group_a,
            players=[
                group_a_member_1.player,
                group_a_member_2.player,
                group_b_member_1.player,
            ],
        )
        new_group_b = new_season.groups.get(name="B")
        self.assertEqual(new_group_b.type, GroupType.ROUND_ROBIN)
        self.assertEqual(new_group_b.members.count(), 3)
        self._check_players_order(
            group=new_group_b,
            players=[
                group_a_member_3.player,
                group_b_member_2.player,
                group_b_member_3.player,
            ],
        )

    def test_prepare_season_with_new_players(self):
        season = SeasonFactory(promotion_count=1, state=SeasonState.FINISHED, number=1)
        group_a_member_1, group_a_member_2, group_a_member_3 = self._create_group(season=season, name="A", rank=1000)
        group_b_member_1, group_b_member_2, group_b_member_3 = self._create_group(season=season, name="B", rank=500)
        group_c_member_1, group_c_member_2, group_c_member_3 = self._create_group(season=season, name="C", rank=100)
        new_player_1 = PlayerFactory(auto_join=True, rank=1200)
        new_player_2 = PlayerFactory(auto_join=True, rank=200)

        new_season = Season.objects.prepare_season(
            start_date=datetime.date(2021, 1, 1), players_per_group=3, promotion_count=1
        )

        self.assertEqual(new_season.groups.count(), 4)
        new_group_a = new_season.groups.get(name="A")
        self._check_players_order(
            group=new_group_a,
            players=[
                group_a_member_1.player,
                group_a_member_2.player,
                group_b_member_1.player,
            ],
        )
        new_group_b = new_season.groups.get(name="B")
        self._check_players_order(
            group=new_group_b,
            players=[group_a_member_3.player, group_b_member_2.player, new_player_1],
        )

        new_group_c = new_season.groups.get(name="C")
        self._check_players_order(
            group=new_group_c,
            players=[
                group_c_member_1.player,
                group_b_member_3.player,
                group_c_member_2.player,
            ],
        )
        new_group_c = new_season.groups.get(name="D")
        self._check_players_order(group=new_group_c, players=[group_c_member_3.player, new_player_2])

    def test_prepare_season_without_resigned_players(self):
        season = SeasonFactory(promotion_count=1, state=SeasonState.FINISHED, number=1)
        group_a_member_1, group_a_member_2, group_a_member_3 = self._create_group(season=season, name="A")
        group_a_member_3.player.auto_join = False
        group_a_member_3.player.save()
        group_b_member_1, group_b_member_2, group_b_member_3 = self._create_group(season=season, name="B")

        new_season = Season.objects.prepare_season(
            start_date=datetime.date(2021, 1, 1), players_per_group=3, promotion_count=1
        )

        new_group_a = new_season.groups.get(name="A")
        self.assertEqual(new_group_a.type, GroupType.ROUND_ROBIN)
        self.assertEqual(new_group_a.members.count(), 3)
        self._check_players_order(
            group=new_group_a,
            players=[
                group_a_member_1.player,
                group_a_member_2.player,
                group_b_member_1.player,
            ],
        )
        new_group_b = new_season.groups.get(name="B")
        self.assertEqual(new_group_b.type, GroupType.ROUND_ROBIN)
        self.assertEqual(new_group_b.members.count(), 2)
        self._check_players_order(
            group=new_group_b,
            players=[
                group_b_member_2.player,
                group_b_member_3.player,
            ],
        )

    def test_prepare_season_with_mcmahon_group(self):
        season = SeasonFactory(promotion_count=1, state=SeasonState.FINISHED, number=1)
        group_a = GroupFactory(season=season, name="A")
        group_a_member_1 = MemberFactory(group=group_a)
        group_a_member_2 = MemberFactory(group=group_a)
        GameFactory(
            group=group_a,
            white=group_a_member_1,
            black=group_a_member_2,
            winner=group_a_member_2,
        )
        new_player_1 = PlayerFactory(rank=100)
        new_player_2 = PlayerFactory(rank=200)
        new_player_3 = PlayerFactory(rank=300)

        new_season = Season.objects.prepare_season(
            start_date=datetime.date(2021, 1, 1), players_per_group=2, promotion_count=1
        )

        self.assertEqual(new_season.groups.count(), 2)
        new_group_a = new_season.groups.get(name="A")
        self.assertEqual(new_group_a.type, GroupType.ROUND_ROBIN)
        new_group_b = new_season.groups.get(name="B")
        self.assertEqual(new_group_b.type, GroupType.MCMAHON)
        self.assertTrue(new_group_b.members.filter(player=new_player_3, order=1).exists())
        self.assertTrue(new_group_b.members.filter(player=new_player_2, order=2).exists())
        self.assertTrue(new_group_b.members.filter(player=new_player_1, order=3).exists())

    def test_prepare_season_without_previous_one(self):
        new_player_1 = PlayerFactory(rank=100)
        new_player_2 = PlayerFactory(rank=200)
        new_player_3 = PlayerFactory(rank=300)

        new_season = Season.objects.prepare_season(
            start_date=datetime.date(2021, 1, 1), players_per_group=3, promotion_count=1
        )

        new_group_a = new_season.groups.get(name="A")
        self.assertEqual(new_group_a.type, GroupType.ROUND_ROBIN)
        self.assertEqual(new_group_a.members.count(), 3)
        self._check_players_order(
            group=new_group_a,
            players=[
                new_player_3,
                new_player_2,
                new_player_1,
            ],
        )

    def test_prepare_season_when_previous_is_in_draft(self):
        SeasonFactory(state=SeasonState.DRAFT)

        with self.assertRaises(ValueError):
            Season.objects.prepare_season(
                start_date=datetime.date(2021, 1, 1),
                players_per_group=3,
                promotion_count=1,
            )

    def test_prepare_season_when_previous_is_in_progress(self):
        SeasonFactory(state=SeasonState.IN_PROGRESS)

        with self.assertRaises(ValueError):
            Season.objects.prepare_season(
                start_date=datetime.date(2021, 1, 1),
                players_per_group=3,
                promotion_count=1,
            )

    def test_delete_group(self):
        season = SeasonFactory(state=SeasonState.DRAFT)
        group_1 = GroupFactory(season=season, name="A")
        group_2 = GroupFactory(season=season, name="B")

        season.delete_group(group_id=group_1.id)

        group_2.refresh_from_db()
        self.assertEqual(season.groups.count(), 1)
        self.assertEqual(group_2.name, "A")

    def test_add_group(self):
        season = SeasonFactory(state=SeasonState.DRAFT)

        season.add_group()

        group = season.groups.get()
        self.assertEqual(season.groups.count(), 1)
        self.assertEqual(group.name, "A")

    def test_start(self):
        season = SeasonFactory(
            state=SeasonState.DRAFT,
            start_date=datetime.date(2021, 1, 1),
            players_per_group=4,
        )
        group = GroupFactory(season=season, type=GroupType.ROUND_ROBIN)
        member_1 = MemberFactory(group=group)
        member_2 = MemberFactory(group=group)
        member_3 = MemberFactory(group=group)
        member_4 = MemberFactory(group=group)

        season.start()

        season.refresh_from_db()
        self.assertEqual(season.state, SeasonState.IN_PROGRESS)
        self.assertEqual(group.rounds.count(), 3)
        round_1 = group.rounds.get(number=1)
        self.assertEqual(round_1.games.count(), 2)
        self.assertEqual(round_1.start_date, datetime.date(2021, 1, 1))
        self.assertEqual(round_1.end_date, datetime.date(2021, 1, 7))
        self.assertTrue(self._game_exists(round_1, member_1, member_4))
        self.assertTrue(self._game_exists(round_1, member_2, member_3))
        round_2 = group.rounds.get(number=2)
        self.assertEqual(round_2.start_date, datetime.date(2021, 1, 8))
        self.assertEqual(round_2.end_date, datetime.date(2021, 1, 14))
        self.assertEqual(round_2.games.count(), 2)
        self.assertTrue(self._game_exists(round_2, member_1, member_3))
        self.assertTrue(self._game_exists(round_2, member_2, member_4))
        round_3 = group.rounds.get(number=3)
        self.assertEqual(round_3.games.count(), 2)
        self.assertEqual(round_3.start_date, datetime.date(2021, 1, 15))
        self.assertEqual(round_3.end_date, datetime.date(2021, 1, 21))
        self.assertTrue(self._game_exists(round_3, member_1, member_2))
        self.assertTrue(self._game_exists(round_3, member_3, member_4))

    def test_finish(self):
        season = SeasonFactory(state=SeasonState.IN_PROGRESS)

        season.finish()

        season.refresh_from_db()
        self.assertEqual(season.state, SeasonState.FINISHED)

    def test_finish_when_games_without_result(self):
        season = SeasonFactory(state=SeasonState.IN_PROGRESS)
        group = GroupFactory(season=season)
        GameFactory(group=group)

        with self.assertRaises(GamesWithoutResultError):
            season.finish()

    def test_start_with_mcmahon_group(self):
        season = SeasonFactory(state=SeasonState.DRAFT, start_date=datetime.date(2021, 1, 1))
        group = GroupFactory(season=season, type=GroupType.MCMAHON)
        MemberFactory(group=group)
        MemberFactory(group=group)

        season.start()

        self.assertFalse(group.rounds.exists())  # this is temporary solution

    def _game_exists(self, round: Round, member_1: Member, member_2: Member) -> bool:
        return (
            Game.objects.filter(
                group=round.group,
                round=round,
                date=datetime.datetime.combine(round.end_date, settings.DEFAULT_GAME_TIME),
            )
            .filter(Q(black=member_1, white=member_2) | Q(black=member_2, white=member_1))
            .exists()
        )

    def _create_group(self, season, name, rank=100):
        group = GroupFactory(season=season, name=name)
        member_1 = MemberFactory(group=group, order=1, player__rank=rank, rank=rank)
        member_2 = MemberFactory(group=group, order=2, player__rank=rank, rank=rank)
        member_3 = MemberFactory(group=group, order=3, player__rank=rank, rank=rank)
        GameFactory(
            group=group,
            white=member_1,
            black=member_2,
            winner=member_1,
        )
        GameFactory(
            group=group,
            white=member_1,
            black=member_3,
            winner=member_1,
        )
        GameFactory(
            group=group,
            white=member_2,
            black=member_3,
            winner=member_2,
        )
        return member_1, member_2, member_3

    def _check_players_order(self, group, players=None):
        for order, player in enumerate(players, start=1):
            self.assertTrue(
                group.members.filter(player=player, order=order).exists(),
                f"Player {player} is not on place {order} in group {group}",
            )


class GroupTestCase(TestCase):
    def test_delete_member(self):
        group = GroupFactory(season__state=SeasonState.DRAFT)
        member_1 = MemberFactory(group=group, order=1)
        member_2 = MemberFactory(group=group, order=2)
        member_3 = MemberFactory(group=group, order=2)

        group.delete_member(member_id=member_2.id)

        member_1.refresh_from_db()
        member_3.refresh_from_db()
        self.assertEqual(group.members.count(), 2)
        self.assertEqual(member_1.order, 1)
        self.assertEqual(member_3.order, 2)

    def test_move_member_up(self):
        group = GroupFactory(season__state=SeasonState.DRAFT)
        member_1 = MemberFactory(group=group, order=1)
        member_2 = MemberFactory(group=group, order=2)

        group.move_member_up(member_id=member_2.id)

        member_1.refresh_from_db()
        member_2.refresh_from_db()
        self.assertEqual(member_2.order, 1)
        self.assertEqual(member_1.order, 2)

    def test_move_member_down(self):
        group = GroupFactory(season__state=SeasonState.DRAFT)
        member_1 = MemberFactory(group=group, order=1)
        member_2 = MemberFactory(group=group, order=2)

        group.move_member_down(member_id=member_1.id)

        member_1.refresh_from_db()
        member_2.refresh_from_db()
        self.assertEqual(member_1.order, 2)
        self.assertEqual(member_2.order, 1)

    def test_add_member(self):
        season = SeasonFactory(state=SeasonState.DRAFT)
        group_1 = GroupFactory(season=season)
        MemberFactory(group=group_1, order=1)
        group_2 = GroupFactory(season=season)
        player = PlayerFactory()
        MemberFactory(group=group_2, player=player)

        group_1.add_member(player_nick=player.nick)

        new_member = group_1.members.get(player=player)
        self.assertEqual(group_1.members.count(), 2)
        self.assertEqual(new_member.group, group_1)
        self.assertEqual(new_member.order, 2)
        self.assertEqual(group_2.members.count(), 0)

    def test_swap_member(self):
        group = GroupFactory(season__state=SeasonState.IN_PROGRESS)
        member_1 = MemberFactory(group=group, order=1)
        member_2 = MemberFactory(group=group, order=2)
        member_3 = MemberFactory(group=group, order=2)
        game_1 = GameFactory(white=member_1, black=member_2, group=group)
        game_2 = GameFactory(white=member_2, black=member_3, group=group)
        new_player = PlayerFactory()

        group.swap_member(player_nick_to_remove=member_2.player.nick, player_nick_to_add=new_player.nick)

        self.assertEqual(group.members.count(), 3)
        self.assertFalse(group.members.filter(id=member_2.id).exists())
        member_1.refresh_from_db()
        member_3.refresh_from_db()
        new_member = group.members.get(player=new_player)
        self.assertEqual(member_1.order, 1)
        self.assertEqual(member_3.order, 2)
        self.assertEqual(new_member.order, 3)
        game_1.refresh_from_db()
        game_2.refresh_from_db()
        self.assertEqual(game_1.black, new_member)
        self.assertEqual(game_2.white, new_member)


class GameTestCase(TestCase):
    def test_external_sgf_link(self):
        game = GameFactory(link="https://online-go.com/game/33759361")

        self.assertEqual(game.external_sgf_link, "https://online-go.com/api/v1/games/33759361/sgf")
