"""Endgame regressions using observed states and the real agent entry point.

Run with: python -B -m unittest discover -s tests -p test_endgame.py -v
These tests require only the standard library; they do not simulate a full match.
"""
import copy
import pathlib
import runpy
import unittest


AGENT_PATH = pathlib.Path(__file__).resolve().parents[1] / "main.py"


class EndgameTests(unittest.TestCase):
    def setUp(self):
        self.agent = runpy.run_path(str(AGENT_PATH))["_agent"]

    @staticmethod
    def wheat(planted_day=25, units=4, watered=True):
        return {"kind": "PLANT", "crop": "WHEAT", "planted_day": planted_day,
                "yield_units": units, "watered_today": watered,
                "consecutive_unwatered": 0, "fertilized_until_day": -1}

    def observation(self, step, pos=(4, 4), crops=None, inventory=None,
                    shed=None, hands=None, hand_inventories=None):
        tiles = [[None if x < 5 and y < 5 else "LOCKED"
                  for x in range(10)] for y in range(10)]
        for (x, y), tile in (crops or {}).items():
            tiles[y][x] = copy.deepcopy(tile)
        return {
            "player": 0, "step": step, "day": step // 24, "hour": step % 24,
            "farms": [{"money": 0, "tiles": tiles, "farmer": list(pos),
                       "hands": [list(p) for p in (hands or [])],
                       "unlocked_quadrants": ["NW"]}],
            "private": {"shed": dict(shed or {}), "seeds": {},
                        "inventories": [dict(inventory or {})]
                        + [dict(i) for i in (hand_inventories or [])]},
        }

    def decide(self, *args, **kwargs):
        # Bypass the exception-swallowing public wrapper so failures are visible.
        return self.agent(self.observation(*args, **kwargs), None)

    def test_final_turn_never_harvests_unbankable_produce(self):
        for pos in ((0, 0), (4, 4)):
            with self.subTest(pos=pos):
                result = self.decide(718, pos, {pos: self.wheat()})
                self.assertEqual(result["farmer"], ["PASS"])
                self.assertEqual(result["market"], [])

    def test_rejects_trip_that_fits_nominal_day_but_not_match(self):
        # Step 716 leaves three actions; travel, harvest, return, DROP need four.
        result = self.decide(716, crops={(3, 4): self.wheat()})
        self.assertEqual(result["farmer"], ["PASS"])

    def test_exact_deadline_harvest_return_and_sale_pipeline(self):
        crop = {(3, 4): self.wheat()}
        stages = [
            (715, (4, 4), crop, {}, ["WEST"]),
            (716, (3, 4), crop, {}, ["HARVEST"]),
            (717, (3, 4), {}, {"WHEAT": 4}, ["EAST"]),
            (718, (4, 4), {}, {"WHEAT": 4}, ["DROP"]),
        ]
        for step, pos, crops, inventory, expected in stages:
            with self.subTest(step=step):
                result = self.decide(step, pos, crops, inventory)
                self.assertEqual(result["farmer"], expected)
                self.assertEqual(result["market"],
                                 [["SELL", "WHEAT", 4]] if step == 718 else [])

    def test_skips_last_water_to_save_existing_yield(self):
        result = self.decide(716, (3, 4),
                             {(3, 4): self.wheat(27, 1, False)})
        self.assertEqual(result["farmer"], ["HARVEST"])

    def test_waters_when_extra_yield_can_still_be_sold(self):
        result = self.decide(715, (3, 4),
                             {(3, 4): self.wheat(27, 1, False)})
        self.assertEqual(result["farmer"], ["WATER"])

    def test_does_not_harvest_zero_yield_when_water_cannot_fit(self):
        result = self.decide(716, (3, 4),
                             {(3, 4): self.wheat(27, 0, False)})
        self.assertEqual(result["farmer"], ["PASS"])

    def test_cargo_returns_before_another_harvest_would_strand_it(self):
        result = self.decide(717, (3, 4), {(3, 4): self.wheat()}, {"MILK": 2})
        self.assertEqual(result["farmer"], ["EAST"])
        result = self.decide(718, inventory={"MILK": 2})
        self.assertEqual(result["farmer"], ["DROP"])
        self.assertEqual(result["market"], [["SELL", "MILK", 2]])

    def test_last_turn_delivers_existing_cargo_instead_of_harvesting(self):
        result = self.decide(718, crops={(4, 4): self.wheat()},
                             inventory={"WHEAT": 4})
        self.assertEqual(result["farmer"], ["DROP"])
        self.assertEqual(result["market"], [["SELL", "WHEAT", 4]])

    def test_preserves_early_return_buffer_for_shared_shed(self):
        # A further harvest fits in isolation, but keeping the delivery buffer
        # leaves room for multiple workers to sell through the shared shed.
        result = self.decide(716, (3, 4), {(3, 4): self.wheat()}, {"MILK": 50})
        self.assertEqual(result["farmer"], ["EAST"])

    def test_mixed_cargo_with_animal_reserves_two_delivery_actions(self):
        inventory = {"GOOSE": 1, "MILK": 2, "WHEAT": 3}
        result = self.decide(716, (3, 4), {(3, 4): self.wheat()}, inventory)
        self.assertEqual(result["farmer"], ["EAST"])
        result = self.decide(717, inventory=inventory)
        self.assertEqual(result["farmer"], ["PLACE", "MILK", 2])
        self.assertEqual(result["market"], [["SELL", "MILK", 2]])
        result = self.decide(718, inventory={"GOOSE": 1, "WHEAT": 3})
        self.assertEqual(result["farmer"], ["PLACE", "WHEAT", 3])
        self.assertEqual(result["market"], [["SELL", "WHEAT", 3]])

    def test_simultaneous_deliveries_are_all_sold(self):
        result = self.decide(718, inventory={"WHEAT": 4}, hands=[(4, 4)],
                             hand_inventories=[{"MILK": 2}])
        self.assertEqual(result["farmer"], ["DROP"])
        self.assertEqual(result["hands"], [["DROP"]])
        self.assertCountEqual(result["market"],
                              [["SELL", "WHEAT", 4], ["SELL", "MILK", 2]])

    def test_delivery_never_drops_more_than_available_shed_space(self):
        result = self.decide(718, inventory={"MILK": 3}, shed={"WHEAT": 98},
                             hands=[(4, 4)], hand_inventories=[{"MILK": 3}])
        self.assertEqual(result["farmer"], ["PLACE", "MILK", 2])
        self.assertEqual(result["hands"], [["PASS"]])
        self.assertCountEqual(result["market"],
                              [["SELL", "WHEAT", 98], ["SELL", "MILK", 2]])

    def test_previous_day_harvest_still_uses_overnight_delivery(self):
        result = self.decide(694, (0, 0), {(0, 0): self.wheat(24)})
        self.assertEqual(result["farmer"], ["HARVEST"])


if __name__ == "__main__":
    unittest.main()
