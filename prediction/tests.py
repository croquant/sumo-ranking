from django.test import SimpleTestCase

from rikishi.utils import convert_long_to_short_rank


class ConvertLongToShortRankTests(SimpleTestCase):
    def test_maegashira_one_east(self):
        self.assertEqual(
            convert_long_to_short_rank("Maegashira 1 East"),
            "m1e",
        )

    def test_ozeki(self):
        self.assertEqual(convert_long_to_short_rank("Ozeki"), "o")

    def test_empty_string_returns_none(self):
        self.assertIsNone(convert_long_to_short_rank(""))
