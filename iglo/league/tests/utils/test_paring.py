from django.test import SimpleTestCase

from league.utils.paring import round_robin, shuffle_colors


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

    def test_make_pairs_for_five(self):
        result = round_robin(n=5)

        self.assertEqual(
            result,
            [
                [(0, 4), (1, 3)],
                [(3, 4), (0, 2)],
                [(2, 3), (1, 4)],
                [(1, 2), (0, 3)],
                [(0, 1), (2, 4)],
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


class ShuffleColorsTestCase(SimpleTestCase):
    def test_shuffle_colors(self):
        paring = [
            [(0, 5), (1, 4), (2, 3)],
            [(0, 4), (3, 5), (1, 2)],
            [(0, 3), (2, 4), (1, 5)],
            [(0, 2), (1, 3), (4, 5)],
            [(0, 1), (2, 5), (3, 4)],
        ]

        result = shuffle_colors(paring=paring, randomize=False)

        self.assertEqual(
            result,
            [
                [(0, 5), (1, 4), (2, 3)],
                [(4, 0), (3, 5), (2, 1)],
                [(0, 3), (4, 2), (1, 5)],
                [(2, 0), (3, 1), (5, 4)],
                [(0, 1), (5, 2), (3, 4)],
            ],
        )
