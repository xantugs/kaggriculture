"""Regressions for the experimental full crop-forecast correction.

The corrected forecast is retained separately because it lost the fresh-seed
comparison. The default main.py keeps the independently tested endgame change.
"""

import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

_path = Path(__file__).resolve().parents[1] / "versions" / "main_v8_full_buffer.py"
_spec = importlib.util.spec_from_file_location("forecast_experiment", _path)
agent = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(agent)


class CropForecastTests(unittest.TestCase):
    def make_state(self, day=1):
        observation = {
            "player": 0,
            "day": day,
            "hour": 0,
            "farms": [{
                "money": 10000,
                "tiles": [[None for _ in range(10)] for _ in range(10)],
                "farmer": [4, 4],
            }],
        }
        state = agent.parse(observation, None)
        state.last_day = 29
        memory = {"plan": {}, "plan_day": {}, "tau": 3.0,
                  "t0": 0.0, "fert_use": {}}
        return state, memory

    @staticmethod
    def booked(context, crop):
        return {day: units for day, units in enumerate(context["added"][crop])
                if units}

    def test_full_crop_yield_is_booked_with_and_without_fertilizer(self):
        for crop, dates in (("TOMATO", (9, 10, 11, 12)),
                            ("STRAWBERRY", (11, 13, 15, 17))):
            for fertilized, units in ((False, 1), (True, 2)):
                with self.subTest(crop=crop, fertilized=fertilized):
                    state, memory = self.make_state()
                    memory["fert_use"][crop] = fertilized
                    context = agent.build_context(state, memory)
                    row = next(row for row in agent.evaluate_uses(state, memory, context)
                               if row["use"] == crop)
                    expected = dict.fromkeys(dates, units)
                    self.assertEqual(expected, row["sched"])

                    agent.add_to_pipeline(state, memory, context, crop)
                    self.assertEqual(expected, self.booked(context, crop))
                    agent.add_to_pipeline(state, memory, context, crop)
                    self.assertEqual(dict.fromkeys(dates, 2 * units),
                                     self.booked(context, crop))

    def test_late_planting_books_only_harvests_available_before_finish(self):
        for crop, day, dates in (("TOMATO", 20, (28, 29)),
                                 ("STRAWBERRY", 17, (27, 29))):
            for fertilized, units in ((False, 1), (True, 2)):
                with self.subTest(crop=crop, fertilized=fertilized):
                    state, memory = self.make_state(day)
                    memory["fert_use"][crop] = fertilized
                    context = agent.build_context(state, memory)
                    row = next(row for row in agent.evaluate_uses(state, memory, context)
                               if row["use"] == crop)
                    expected = dict.fromkeys(dates, units)
                    self.assertEqual(expected, row["sched"])
                    agent.add_to_pipeline(state, memory, context, crop)
                    self.assertEqual(expected, self.booked(context, crop))

    def test_same_day_plans_are_rebooked_in_each_fresh_context(self):
        state, memory = self.make_state()
        memory["plan"] = {(0, 0): "TOMATO", (1, 0): "STRAWBERRY"}
        memory["plan_day"] = dict.fromkeys(memory["plan"], state.day)
        memory["fert_use"] = {"TOMATO": True, "STRAWBERRY": True}
        state.tiles = [["LOCKED" for _ in range(10)] for _ in range(10)]
        state.tiles[0][0] = state.tiles[0][1] = None
        state.me["tiles"] = state.tiles
        expected_plan = dict(memory["plan"])

        with patch.dict(agent.PARAMS, {"invest": 0}):
            for _ in range(2):
                context = agent.build_context(state, memory)
                agent.plan_tiles(state, memory, context, budget=0, seed_budget=0)
                self.assertEqual(expected_plan, memory["plan"])
                self.assertEqual({9: 2, 10: 2, 11: 2, 12: 2},
                                 self.booked(context, "TOMATO"))
                self.assertEqual({11: 2, 13: 2, 15: 2, 17: 2},
                                 self.booked(context, "STRAWBERRY"))

    def test_new_investment_reserves_its_fertilized_supply(self):
        state, memory = self.make_state()
        memory["fert_use"]["TOMATO"] = True
        context = agent.build_context(state, memory)
        candidate = {"use": "TOMATO", "v": 100, "npv": 1000, "cost": 50}

        def candidates(state, memory, context, fillers_only=False):
            return [] if fillers_only else [candidate]

        with patch.object(agent, "evaluate_uses", side_effect=candidates), \
                patch.object(agent.time, "perf_counter", return_value=0.0):
            remaining = agent.plan_tiles(state, memory, context, budget=50,
                                         seed_budget=0)
        self.assertEqual(0, remaining)
        self.assertEqual(["TOMATO"], list(memory["plan"].values()))
        self.assertEqual({9: 2, 10: 2, 11: 2, 12: 2},
                         self.booked(context, "TOMATO"))

    def test_next_investment_accounts_for_all_previously_planned_supply(self):
        state, memory = self.make_state()
        memory["fert_use"]["TOMATO"] = True
        context = agent.build_context(state, memory)
        for item in agent.PRODUCTS:
            context["base"][item] = [float(agent.MARKET_PARAMS[item]["I0"])] * 32
        reference = copy.deepcopy(context)
        for day in (9, 10, 11, 12):
            reference["added"]["TOMATO"][day] = 20
        for _ in range(10):
            agent.add_to_pipeline(state, memory, context, "TOMATO")

        def tomato_profit(ctx):
            return next(row["npv"] for row in agent.evaluate_uses(state, memory, ctx)
                        if row["use"] == "TOMATO")

        self.assertAlmostEqual(tomato_profit(reference), tomato_profit(context))
        self.assertLess(tomato_profit(context), 0)


if __name__ == "__main__":
    unittest.main()
