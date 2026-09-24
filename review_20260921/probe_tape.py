"""Review-only instrumentation. Leaves submitted agent artifacts unchanged."""
from pathlib import Path
import collections
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from harness import _load_agent_module, make


def probe(opponent_id, seed=210000):
    mod = _load_agent_module(ROOT / "submit" / "tape_a2" / "main.py")
    if opponent_id == "plain":
        rival = _load_agent_module(ROOT / "submit" / "tape_champion" / "main.py").agent
    else:
        route = json.loads((ROOT.parent / "routes" / ("route_" + opponent_id + ".json")).read_text())["route"]

        def rival(obs, config=None):
            a = route[min(obs.get("step", 0), len(route) - 1)]
            hands = a.get("hands") or []
            n = len(obs["farms"][obs["player"]].get("hands") or [])
            return {"farmer": a.get("farmer") or ["PASS"],
                    "hands": [hands[i] if i < len(hands) else ["PASS"] for i in range(n)],
                    "market": list(a.get("market") or [])[:10]}

    events = []

    def tracked(obs, config=None):
        previous = set(mod._S["done"])
        a = mod.agent(obs, config)
        ids = sorted(mod._S["done"] - previous)
        if ids:
            pulled = a["market"][-len(ids):]
            pickups = collections.Counter()
            for action in [a["farmer"], *a["hands"]]:
                if action and action[0] == "PICKUP":
                    pickups[action[1]] += action[2] if len(action) > 2 else 1
            for (future, slot), emitted in zip(ids, pulled):
                original = mod.ROUTE[future]["market"][slot]
                assert original[1] == emitted[1]
                events.append({"step": obs["step"], "future_step": future, "slot": slot,
                               "good": original[1], "scheduled": original[2],
                               "emitted": emitted[2], "partial": emitted[2] < original[2],
                               "oversized_request": original[2] > env.configuration.shedCapacity,
                               "same_good_pickup_requested": pickups[original[1]]})
        return a

    env = make("kaggriculture", debug=True, configuration={"seed": seed})
    env.run([tracked, rival])
    final = env.steps[-1]
    assert all(s.status == "DONE" for s in final)
    priv = final[0].observation["private"]
    remaining = collections.Counter(priv.get("shed") or {})
    for inv in priv.get("inventories") or []:
        remaining.update(inv)
    result = {"opponent": opponent_id, "seed": seed,
              "scores": [s.reward for s in final],
              "pulled_orders": len(events),
              "partial_ordinary_orders": sum(e["partial"] and not e["oversized_request"] for e in events),
              "partial_oversized_orders": sum(e["partial"] and e["oversized_request"] for e in events),
              "pickup_overlaps": sum(e["same_good_pickup_requested"] > 0 for e in events),
              "remaining_stock": {k: v for k, v in remaining.items() if v},
              "events": events}
    out = Path(__file__).with_name("probe_" + opponent_id + ".json")
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "events"}), flush=True)


if __name__ == "__main__":
    for opponent in ("plain", "111211276"):
        probe(opponent)
