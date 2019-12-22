"""Unit test optimal lineup functions."""
import unittest
import ff_espn_api  # pylint: disable=import-error
from collections import defaultdict


class TestAddToOptimal(unittest.TestCase):
    """Test add_to_optimal() function."""

    def setUp(self):
        """Set up settings and optimal objects for each function."""
        self.settings = defaultdict(int)
        self.settings["QB"] = 1
        self.settings["RB"] = 2
        self.settings["WR"] = 2
        self.settings["TE"] = 1
        self.settings["RB/WR/TE"] = 1
        self.settings["D/ST"] = 1
        self.settings["K"] = 1

        self.optimal = defaultdict(ff_espn_api.Player)

        self.flex = "RB/WR/TE"

    def test_basic_optimal(self):
        pass


if __name__ == "__main__":
    unittest.main()
