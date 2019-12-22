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
        # test basic replacement functionality
        qb1 = copy.deepcopy(self.default_player)
        qb1.position = "QB"
        qb1.points = 10
        self.optimal = add_to_optimal(self.optimal, self.settings, qb1, self.flex)
        self.assertEqual(self.optimal["QB"][0].points, 10)
        self.assertEqual(len(self.optimal["QB"]), self.settings["QB"])

        qb2 = copy.deepcopy(self.default_player)
        qb2.position = "QB"
        qb2.points = 8
        self.optimal = add_to_optimal(self.optimal, self.settings, qb2, self.flex)
        self.assertEqual(self.optimal["QB"][0].points, 10)
        self.assertEqual(len(self.optimal["QB"]), self.settings["QB"])

        qb3 = copy.deepcopy(self.default_player)
        qb3.position = "QB"
        qb3.points = 12
        self.optimal = add_to_optimal(self.optimal, self.settings, qb3, self.flex)
        self.assertEqual(self.optimal["QB"][0].points, 12)
        self.assertEqual(len(self.optimal["QB"]), self.settings["QB"])

        rb1 = copy.deepcopy(self.default_player)
        rb1.position = "RB"
        rb1.points = 20
        self.optimal = add_to_optimal(self.optimal, self.settings, rb1, self.flex)
        self.assertEqual(self.optimal["RB"][0].points, rb1.points)
        self.assertLess(len(self.optimal["RB"]), self.settings["RB"])

        rb2 = copy.deepcopy(self.default_player)
        rb2.position = "RB"
        rb2.points = 12
        self.optimal = add_to_optimal(self.optimal, self.settings, rb2, self.flex)
        self.assertIn(rb1.points, [x.points for x in self.optimal["RB"]])
        self.assertIn(rb2.points, [x.points for x in self.optimal["RB"]])
        self.assertEqual(len(self.optimal["RB"]), self.settings["RB"])

        # test adding to FLEX when less than the other 2 RBs
        rb3 = copy.deepcopy(self.default_player)
        rb3.position = "RB"
        rb3.points = 8
        self.optimal = add_to_optimal(self.optimal, self.settings, rb3, self.flex)
        self.assertIn(rb1.points, [x.points for x in self.optimal["RB"]])
        self.assertIn(rb2.points, [x.points for x in self.optimal["RB"]])
        self.assertEqual(len(self.optimal["RB"]), self.settings["RB"])
        self.assertIn(rb3.points, [x.points for x in self.optimal[self.flex]])
        self.assertEqual(len(self.optimal[self.flex]), self.settings[self.flex])

        # test bumping one RB from RB2 to FLEX
        rb4 = copy.deepcopy(self.default_player)
        rb4.position = "RB"
        rb4.points = 16
        self.optimal = add_to_optimal(self.optimal, self.settings, rb4, self.flex)
        self.assertIn(rb1.points, [x.points for x in self.optimal["RB"]])
        self.assertIn(rb4.points, [x.points for x in self.optimal["RB"]])
        self.assertEqual(len(self.optimal["RB"]), self.settings["RB"])
        self.assertIn(rb2.points, [x.points for x in self.optimal[self.flex]])
        self.assertEqual(len(self.optimal[self.flex]), self.settings[self.flex])

        # test putting something straight away in flex
        rb5 = copy.deepcopy(self.default_player)
        rb5.position = "RB"
        rb5.points = 14
        self.optimal = add_to_optimal(self.optimal, self.settings, rb5, self.flex)
        self.assertIn(rb1.points, [x.points for x in self.optimal["RB"]])
        self.assertIn(rb4.points, [x.points for x in self.optimal["RB"]])
        self.assertEqual(len(self.optimal["RB"]), self.settings["RB"])
        self.assertIn(rb5.points, [x.points for x in self.optimal[self.flex]])
        self.assertEqual(len(self.optimal[self.flex]), self.settings[self.flex])

        # test putting in low WRs with flex spot full
        wr1 = copy.deepcopy(self.default_player)
        wr1.position = "WR"
        wr1.points = 5
        self.optimal = add_to_optimal(self.optimal, self.settings, wr1, self.flex)
        self.assertIn(wr1.points, [x.points for x in self.optimal["WR"]])
        self.assertLess(len(self.optimal["WR"]), self.settings["WR"])

        wr2 = copy.deepcopy(self.default_player)
        wr2.position = "WR"
        wr2.points = 7
        self.optimal = add_to_optimal(self.optimal, self.settings, wr2, self.flex)
        self.assertIn(wr1.points, [x.points for x in self.optimal["WR"]])
        self.assertIn(wr2.points, [x.points for x in self.optimal["WR"]])
        self.assertEqual(len(self.optimal["WR"]), self.settings["WR"])

        # test putting in a very high WR, shouldn't bump anything to FLEX
        wr3 = copy.deepcopy(self.default_player)
        wr3.position = "WR"
        wr3.points = 30
        self.optimal = add_to_optimal(self.optimal, self.settings, wr3, self.flex)
        self.assertIn(wr3.points, [x.points for x in self.optimal["WR"]])
        self.assertIn(wr2.points, [x.points for x in self.optimal["WR"]])
        self.assertEqual(len(self.optimal["WR"]), self.settings["WR"])
        self.assertIn(rb5.points, [x.points for x in self.optimal[self.flex]])
        self.assertEqual(len(self.optimal[self.flex]), self.settings[self.flex])

        # two more receivers, the second one should bump something to FLEX
        wr4 = copy.deepcopy(self.default_player)
        wr4.position = "WR"
        wr4.points = 28
        self.optimal = add_to_optimal(self.optimal, self.settings, wr4, self.flex)
        self.assertIn(wr3.points, [x.points for x in self.optimal["WR"]])
        self.assertIn(wr4.points, [x.points for x in self.optimal["WR"]])
        self.assertEqual(len(self.optimal["WR"]), self.settings["WR"])
        self.assertIn(rb5.points, [x.points for x in self.optimal[self.flex]])
        self.assertEqual(len(self.optimal[self.flex]), self.settings[self.flex])

        # this should bump WR4 to FLEX
        wr5 = copy.deepcopy(self.default_player)
        wr5.position = "WR"
        wr5.points = 29
        self.optimal = add_to_optimal(self.optimal, self.settings, wr5, self.flex)
        self.assertIn(wr3.points, [x.points for x in self.optimal["WR"]])
        self.assertIn(wr5.points, [x.points for x in self.optimal["WR"]])
        self.assertEqual(len(self.optimal["WR"]), self.settings["WR"])
        self.assertIn(wr4.points, [x.points for x in self.optimal[self.flex]])
        self.assertEqual(len(self.optimal[self.flex]), self.settings[self.flex])

        # finally, this should go directly in FLEX
        wr6 = copy.deepcopy(self.default_player)
        wr6.position = "WR"
        wr6.points = 28.5
        self.optimal = add_to_optimal(self.optimal, self.settings, wr6, self.flex)
        self.assertIn(wr3.points, [x.points for x in self.optimal["WR"]])
        self.assertIn(wr5.points, [x.points for x in self.optimal["WR"]])
        self.assertEqual(len(self.optimal["WR"]), self.settings["WR"])
        self.assertIn(wr6.points, [x.points for x in self.optimal[self.flex]])
        self.assertEqual(len(self.optimal[self.flex]), self.settings[self.flex])


if __name__ == "__main__":
    unittest.main()
