"""Unit test optimal lineup functions."""
import unittest
import copy
import ff_espn_api  # pylint: disable=import-error
from collections import defaultdict
from fantasy_coty.main import add_to_optimal


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

        self.optimal = defaultdict(list)

        self.flex = "RB/WR/TE"

        # all of this is garbage in order to create a default BoxPlayer that we can modify
        data = {}
        data["proTeamId"] = 1
        data["player"] = {}
        data["player"]["proTeamId"] = 1
        data["player"]["stats"] = []
        pro_schedule = {}
        pos_rankings = {}
        week = 0
        self.default_player = ff_espn_api.BoxPlayer(
            data, pro_schedule, pos_rankings, week
        )

    def test_basic_optimal(self):
        """Test basic functionality of add_to_optimal()."""
        player0 = copy.deepcopy(self.default_player)
        player0.position = "QB"
        player0.points = 10
        self.optimal = add_to_optimal(self.optimal, self.settings, player0, self.flex)
        self.assertEqual(self.optimal["QB"][0].points, 10)

        player1 = copy.deepcopy(self.default_player)
        player1.position = "QB"
        player1.points = 8
        self.optimal = add_to_optimal(self.optimal, self.settings, player1, self.flex)
        self.assertEqual(self.optimal["QB"][0].points, 10)


if __name__ == "__main__":
    unittest.main()
