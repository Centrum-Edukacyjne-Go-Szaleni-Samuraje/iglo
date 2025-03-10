import datetime
from decimal import Decimal

from django.test import SimpleTestCase

from league.utils.egd import (
    create_tournament_table,
    TournamentClass,
    Location,
    DatesRange,
    TimeLimit,
    ByoYomi,
    Player,
    Game,
    gor_to_rank,
)


class CreateTournamentTableTestCase(SimpleTestCase):
    def test_create_tournament_table_with_all_conditions(self):
        """
        Test tournament export with all edge cases:
        - Regular games played between players
        - BYE games (winner without black/white)
        - Forfeited games (winner is None) 
        - Round without EGD eligible games
        - Game not played (represented by 0-)
        - Player with non-ASCII characters in name
        
        The test checks exact string equality of the entire output format
        to ensure compatibility with the EGD submission format.
        """
        player_1 = Player(first_name="Paweł", last_name="Nowak", rank="6d", country="PL", club="Wars", pin="12312312")
        player_2 = Player(first_name="Adam", last_name="Kowąlski", rank="3d", country="UK", club="Lond", pin="34534534")
        player_3 = Player(first_name="Piotr", last_name="Wójcik", rank="15k", country="PL", club="Krak", pin="56756756")
        player_4 = Player(first_name="Maria", last_name="Schmidt", rank="1k", country="DE", club="Berl", pin="78978978")

        # Create rounds with different scenarios
        rounds = [
            # Round 1: Regular games
            [
                Game(  # Regular game player 1 vs player 2
                    black=player_1,
                    white=player_2,
                    winner=player_1,  # Winner as black
                ),
                Game(  # BYE game - player 3 gets a bye
                    black=None,
                    white=None,
                    winner=player_3,
                ),
            ],
            # Round 2: Mix of regular, not played and bye games
            [
                Game(  # Regular game player 3 vs player 1 
                    black=player_3,
                    white=player_1,
                    winner=player_1,  # Winner as white
                ),
                Game(  # BYE game - player 2 gets a bye
                    black=None,
                    white=None,
                    winner=player_2,
                ),
            ],
            # Round 3: More edge cases
            [
                Game(  # Regular game player 2 vs player 3
                    black=player_2,
                    white=player_3,
                    winner=player_2,  # Winner as black
                ),
                Game(  # BYE game - player 1 gets a bye
                    black=None,
                    white=None,
                    winner=player_1,
                ),
            ],
            # Round 4: Game not played scenario 
            [
                Game(  # Not played game (winner is None - forfeited or not played)
                    black=player_1,
                    white=player_4,
                    winner=None,  # No winner
                ),
                Game(  # Regular game player 2 vs player 3
                    black=player_2,
                    white=player_3,
                    winner=player_3,  # Winner as white
                ),
            ],
            # Round 5: Empty round - no eligible games
            [],
        ]

        result = create_tournament_table(
            klass=TournamentClass.D,
            name="Test Tournament #1",
            location=Location(
                country="PL",
                city="Warsaw",
            ),
            dates=DatesRange(
                start=datetime.date(2022, 1, 15),
                end=datetime.date(2022, 1, 20),
            ),
            handicap=None,
            komi=Decimal("6.5"),
            time_limit=TimeLimit(
                basic=40,
                byo_yomi=ByoYomi(
                    duration=30,
                    periods=3,
                ),
            ),
            players=[
                player_1,
                player_2,
                player_3,
                player_4,
            ],
            rounds=rounds,
        )

        # Check for exact string equality with the expected output
        self.maxDiff = None
        self.assertMultiLineEqual(
            result,
            "\n".join(
                [
                    "; CL[D]",
                    "; EV[Test Tournament #1]",
                    "; PC[PL, Warsaw]",
                    "; DT[2022-01-15,2022-01-20]",
                    "; HA[h9]",
                    "; KM[6.5]",
                    "; TM[62.5]",
                    ";",
                    "1 Nowak Pawel    6d  PL Wars  3  0  0  0  2+/b  3+/w  0+    0-    |12312312",
                    "2 Kowalski Adam  3d  UK Lond  2  0  0  0  1-/w  0+    3+/b  3-/b  |34534534",
                    "3 Wojcik Piotr   15k PL Krak  2  0  0  0  0+    1-/b  2-/w  2+/w  |56756756",
                    "4 Schmidt Maria  1k  DE Berl  0  0  0  0  0-    |78978978",
                ]
            ),
        )


class GorToRankTestCase(SimpleTestCase):
    def test_for_kyu(self):
        self.assertEqual(gor_to_rank(2000), "1k")
        self.assertEqual(gor_to_rank(-900), "30k")
        self.assertEqual(gor_to_rank(100), "20k")
        self.assertEqual(gor_to_rank(149), "20k")
        self.assertEqual(gor_to_rank(150), "19k")

    def test_for_dan(self):
        self.assertEqual(gor_to_rank(2100), "1d")
        self.assertEqual(gor_to_rank(2900), "9d")
        self.assertEqual(gor_to_rank(2149), "1d")
        self.assertEqual(gor_to_rank(2150), "2d")
