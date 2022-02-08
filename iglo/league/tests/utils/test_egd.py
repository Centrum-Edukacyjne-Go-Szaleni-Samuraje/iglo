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
    def test_create_tournament_table(self):
        player_1 = Player(name="Jan Nowak", rank="6d", country="PL", club="Wars", pin="12312312")
        player_2 = Player(name="Adam Kowalski", rank="3d", country="UK", club="Lond", pin="34534534")
        player_3 = Player(name="Piotr Wójcik", rank="15k", country="PL", club="Krak", pin="56756756")

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
            ],
            rounds=[
                [
                    Game(
                        black=player_1,
                        white=player_2,
                        winner=player_1,
                    ),
                    Game(
                        black=None,
                        white=None,
                        winner=player_3,
                    ),
                ],
                [
                    Game(
                        black=player_3,
                        white=player_1,
                        winner=player_1,
                    ),
                    Game(
                        black=None,
                        white=None,
                        winner=player_2,
                    ),
                ],
                [
                    Game(
                        black=player_2,
                        white=player_3,
                        winner=player_2,
                    ),
                    Game(
                        black=None,
                        white=None,
                        winner=player_1,
                    ),
                ],
            ],
        )

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
                    "1 Jan Nowak      6d  PL Wars  3  0  0  0  2+/b  3+/w  0+    |12312312",
                    "2 Adam Kowalski  3d  UK Lond  2  0  0  0  1-/w  0+    3+/b  |34534534",
                    "3 Piotr Wojcik   15k PL Krak  1  0  0  0  0+    1-/b  2-/w  |56756756",
                ]
            ),
        )

class GorToRankTestCase(SimpleTestCase):

    def test_for_kyu(self):
        self.assertEqual(gor_to_rank(2000), "1k")
        self.assertEqual(gor_to_rank(100), "20k")
        self.assertEqual(gor_to_rank(-900), "30k")

    def test_for_dan(self):
        self.assertEqual(gor_to_rank(2100), "1d")
        self.assertEqual(gor_to_rank(2900), "9d")

