"""Small, isolated review probes; does not modify any submitted agent."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location("review_" + name, ROOT / "submit" / name / "main.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def obs(step, shed):
    return {"step": step, "player": 0,
            "farms": [{"hands": [], "farmer": [5, 4]}],
            "private": {"shed": shed}}


def set_route(mod, route):
    mod.ROUTE = route
    mod.N = len(route)
    mod._S = {"done": set(), "step": -1}
    if hasattr(mod, "MAXLOT"):
        mod.MAXLOT = {"WHEAT": 10}


def main():
    report = {}
    for name in ("tape_a2", "tape_c4"):
        mod = load(name)
        set_route(mod, [{"market": []}, {"market": [["SELL", "WHEAT", 10]]}])
        before = mod._agent(obs(0, {"WHEAT": 3}))
        after = mod._agent(obs(1, {"WHEAT": 7}))
        assert before["market"] == [["SELL", "WHEAT", 3]]
        assert after["market"] == []
        report[name + "_finite_partial"] = {"step0_action": before, "step1_action": after,
                                                 "original_quantity": 10, "total_emitted_quantity": 3}

    mod = load("tape_a2")
    set_route(mod, [{"farmer": ["PICKUP", "WHEAT", 2], "market": []},
                    {"market": [["SELL", "WHEAT", 2]]}])
    current = mod._agent(obs(0, {"WHEAT": 2}))
    future = mod._agent(obs(1, {"WHEAT": 2}))
    assert current["farmer"] == ["PICKUP", "WHEAT", 2]
    assert current["market"] == [["SELL", "WHEAT", 2]]
    assert future["market"] == []
    report["pickup_collision"] = {"step0_action": current, "step1_action": future,
                                   "explanation": "Units act before market, so PICKUP can consume all units of a pulled sell, which is nevertheless marked done."}

    capped = load("tape_c4")
    normal_max = {}
    bounded_max = {}
    for step, act in enumerate(capped.ROUTE):
        totals = {}
        for order in act.get("market", []):
            if order and order[0] == "SELL" and 0 < order[2] < 1000:
                totals[order[1]] = totals.get(order[1], 0) + order[2]
        for good, quantity in totals.items():
            normal_max[good] = max(quantity, normal_max.get(good, 0))
        bounded_totals = {}
        for order in act.get("market", []):
            if order and order[0] == "SELL" and 0 < order[2] <= 100:
                bounded_totals[order[1]] = bounded_totals.get(order[1], 0) + order[2]
        for good, quantity in bounded_totals.items():
            bounded_max[good] = max(quantity, bounded_max.get(good, 0))
    report["caps"] = {"actual_MAXLOT": capped.MAXLOT,
                       "max_summed_finite_orders_excluding_1000": normal_max,
                       "max_summed_orders_not_exceeding_shed_capacity": bounded_max,
                       "default_shed_capacity": 100}
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
