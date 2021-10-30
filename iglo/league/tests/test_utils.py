from django.test import SimpleTestCase

from league.utils import round_robin


class RoundRobinTestCase(SimpleTestCase):
    def test_make_pairs_for_two(self):
        result = round_robin(n=2)

        self.assertEqual(result, [[(0, 1)]])

    def test_make_pairs_for_four(self):
        result = round_robin(n=4)

        self.assertEqual(
            result,
            [
                [(0, 3), (1, 2)],
                [(0, 2), (1, 3)],
                [(0, 1), (2, 3)],
            ],
        )

    def test_make_pairs_for_six(self):
        result = round_robin(n=6)

        self.assertEqual(
            result,
            [
                [(0, 5), (1, 4), (2, 3)],
                [(0, 4), (3, 5), (1, 2)],
                [(0, 3), (2, 4), (1, 5)],
                [(0, 2), (1, 3), (4, 5)],
                [(0, 1), (2, 5), (3, 4)],
            ],
        )
