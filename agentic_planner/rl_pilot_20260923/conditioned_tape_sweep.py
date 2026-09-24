"""Evaluate every exact-state elite continuation on held-out day-15 games.

This measures the value of selecting a coordinated plan independently of the
particular nearest-neighbour rule used in conditioned_tape_eval.py.
"""
from collections import Counter
import argparse
import json
import statistics

import conditioned_tape_eval as c


OUT = c.HERE / "conditioned_tape_sweep.json"


def action_counts(game, start=c.S):
    """Small plan fingerprint available from a donor's continuation tape."""
    p = game["_teacher_seat"]
    counts = Counter()
    for step in range(start, len(game["acts"]) - 1):
        a = c.tape_action(game["acts"], p, step)
        for cmd in [a.get("farmer") or []] + list(a.get("hands") or []) + list(a.get("market") or []):
            if not isinstance(cmd, list) or not cmd:
                continue
            name = str(cmd[0])
            counts[name] += 1
            if name in {"PLANT", "BUY_SEED", "SELL", "BUY", "BUY_ANIMAL"} and len(cmd) > 1:
                counts[f"{name}:{cmd[1]}"] += 1
    return dict(counts)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard", type=int, default=0)
    parser.add_argument("--shards", type=int, default=1)
    args = parser.parse_args()
    out = OUT if args.shards == 1 else OUT.with_name(f"{OUT.stem}_{args.shard}.json")
    games = c.load_games()
    by_id = {d["id"]: d for d in games}
    c.METAS = json.loads(c.META_PATH.read_text(encoding="utf-8"))
    tests = [m for i, m in enumerate(c.METAS) if i % 7 == 0][:24]
    test_ids = {m["id"] for m in tests}
    library = [m for m in c.METAS if m["id"] not in test_ids]

    rows = []
    covered = 0
    for ti, tm in enumerate(tests):
        if ti % args.shards != args.shard:
            continue
        donors = [dm for dm in library if dm["key"] == tm["key"] and dm["hands"] == tm["hands"]]
        if not donors:
            continue
        covered += 1
        target = by_id[tm["id"]]
        spawns, shops, _ = c.pinned.reference(target)
        base_metrics = None
        for di, dm in enumerate(donors):
            donor = by_id[dm["id"]]
            row = c.run_target(target, donor, spawns, shops, base_metrics=base_metrics)
            if base_metrics is None:
                base_metrics = {k: row[k] for k in ("base_us", "base_them", "base_err")}
            row["target_shops"] = tm["shops"]
            row["donor_shops"] = dm["shops"]
            row["target_money"] = tm["money"]
            row["donor_money"] = dm["money"]
            row["donor_reward"] = dm["reward"]
            row["plan"] = action_counts(donor)
            rows.append(row)
            print(
                "target", ti + 1, "/", len(tests), "donor", di + 1, "/", len(donors),
                "delta", row["margin_delta"], flush=True,
            )
        out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    groups = {}
    for row in rows:
        groups.setdefault(row["gid"], []).append(row)
    nearest = [min(rs, key=lambda r: r["distance"]) for rs in groups.values()]
    oracle = [max(rs, key=lambda r: r["margin_delta"]) for rs in groups.values()]
    worst = [min(rs, key=lambda r: r["margin_delta"]) for rs in groups.values()]

    def summary(which):
        return {
            "mean": statistics.mean(r["margin_delta"] for r in which),
            "median": statistics.median(r["margin_delta"] for r in which),
            "positive": sum(r["margin_delta"] > 0 for r in which),
            "cash_mean": statistics.mean(r["cash_delta"] for r in which),
        }

    report = {
        "covered_targets": covered,
        "candidate_games": len(rows),
        "all_candidates": summary(rows),
        "nearest": summary(nearest),
        "oracle": summary(oracle),
        "worst": summary(worst),
        "oracle_rows": [
            {k: r[k] for k in ("gid", "donor", "margin_delta", "cash_delta", "target_shops", "donor_shops", "plan")}
            for r in oracle
        ],
    }
    summary_out = c.HERE / ("conditioned_tape_sweep_summary.json" if args.shards == 1
                            else f"conditioned_tape_sweep_summary_{args.shard}.json")
    summary_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
