"""Paired evaluation with auditable JSONL records and explicit baseline identity."""
import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
import math
from pathlib import Path
import statistics
import time

from harness import PROJECT_ROOT, MatchError, describe_agent, run_match


# These deliberately different openings are stress tests, not independent bots.
OPPONENTS = {
    "baseline": {},
    "v7": {},
    "melon_rush": {"melon0": 20, "straw0": 0, "goose0": 0, "cow0": 0, "sheep0": 0},
    "crop_heavy": {"invest": 0, "goose0": 0, "cow0": 0, "sheep0": 0},
    "livestock_heavy": {"melon0": 0},
}


def environment_version():
    try:
        return importlib.metadata.version("kaggle-environments")
    except importlib.metadata.PackageNotFoundError:
        import kaggle_environments
        return getattr(kaggle_environments, "__version__", "unknown")


def safe_rewards(rewards):
    if rewards is None:
        return None
    return [r if isinstance(r, (int, float)) and math.isfinite(r) else None for r in rewards]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidate", default="main.py")
    ap.add_argument("--params", default="{}", help="JSON parameter overrides for candidate")
    ap.add_argument("--baseline", default="versions/main_v7.py", help="Immutable source for all opponents")
    ap.add_argument("--opponents", nargs="+", choices=list(OPPONENTS),
                    default=["baseline", "melon_rush", "crop_heavy", "livestock_heavy"])
    ap.add_argument("-n", type=int, default=2, help="Number of seeds per opponent; always both seats")
    ap.add_argument("--seed0", type=int, default=10000, help="Fresh range, separate from previous 100-400 sweeps")
    ap.add_argument("--seeds", type=int, nargs="+", help="Explicit seed list, overrides -n/--seed0")
    ap.add_argument("--output", help="New JSONL path; refuses to overwrite an existing run")
    args = ap.parse_args(argv)
    if args.n < 1:
        ap.error("-n must be positive")
    seeds = args.seeds if args.seeds is not None else list(range(args.seed0, args.seed0 + args.n))
    if len(set(seeds)) != len(seeds):
        ap.error("Seeds must be unique")
    if len(set(args.opponents)) != len(args.opponents):
        ap.error("Opponents must be unique")
    try:
        overrides = json.loads(args.params)
        candidate = describe_agent(args.candidate, overrides)
        opponents = {name: describe_agent(args.baseline, OPPONENTS[name]) for name in args.opponents}
    except (ValueError, TypeError, OSError) as exc:
        ap.error(str(exc))
    version = environment_version()
    timestamp = datetime.now(timezone.utc)
    output = Path(args.output) if args.output else PROJECT_ROOT / "logs" / (
        "benchmark_" + timestamp.strftime("%Y%m%dT%H%M%S_%fZ") + ".jsonl")
    output.parent.mkdir(parents=True, exist_ok=True)
    print("Opponents use the specified baseline source and parameter variants; this is not external competition validation.", flush=True)
    print("Results: %s" % output.resolve(), flush=True)
    summaries = {}
    with output.open("x", encoding="utf-8") as stream:
        for name, opponent in opponents.items():
            margins = []
            for seed in seeds:
                for seat in (0, 1):
                    specs = [(candidate["path"], overrides), (opponent["path"], OPPONENTS[name])]
                    if seat:
                        specs.reverse()
                    record = {
                        "started_utc": datetime.now(timezone.utc).isoformat(),
                        "environment": "kaggriculture", "environment_version": version,
                        "seed": seed, "candidate_seat": seat,
                        "opponent_name": name, "candidate": candidate, "opponent": opponent,
                    }
                    started = time.perf_counter()
                    try:
                        env, rewards, statuses = run_match(*specs, seed)
                    except Exception as exc:
                        record.update({"ok": False, "error": str(exc),
                                       "error_type": type(exc).__name__,
                                       "scores_by_seat": safe_rewards(getattr(exc, "rewards", None)),
                                       "statuses_by_seat": getattr(exc, "statuses", None),
                                       "elapsed_seconds": time.perf_counter() - started})
                        stream.write(json.dumps(record, allow_nan=False) + "\n")
                        stream.flush()
                        print("FAILED %s seed=%s seat=%s: %s" % (name, seed, seat, exc), flush=True)
                        return 1
                    a, b = rewards[seat], rewards[1 - seat]
                    margin = a - b
                    margins.append(margin)
                    record.update({"ok": True, "candidate_score": a, "opponent_score": b,
                                   "scores_by_seat": rewards, "statuses_by_seat": statuses,
                                   "margin": margin, "result": "win" if margin > 0 else "loss" if margin < 0 else "tie",
                                   "configuration": dict(env.configuration), "observations": len(env.steps),
                                   "elapsed_seconds": time.perf_counter() - started})
                    stream.write(json.dumps(record, allow_nan=False) + "\n")
                    stream.flush()
                    print(f"{name} seed={seed} seat={seat}: {record['result']} ${margin:+,.0f}", flush=True)
            wins = sum(m > 0 for m in margins)
            losses = sum(m < 0 for m in margins)
            ties = len(margins) - wins - losses
            summaries[name] = {"games": len(margins), "seeds": len(seeds),
                               "wins": wins, "losses": losses, "ties": ties,
                               "mean_margin": statistics.mean(margins), "median_margin": statistics.median(margins)}
            print(f"{name}: W/L/T {wins}/{losses}/{ties}, {len(seeds)} seeds, "
                  f"mean margin ${statistics.mean(margins):+,.0f}, median ${statistics.median(margins):+,.0f}",
                  flush=True)
    summary_path = output.with_suffix(".summary.json")
    with summary_path.open("x", encoding="utf-8") as stream:
        json.dump({"results_file": str(output.resolve()), "seeds": seeds, "opponents_share_baseline_source": True,
                   "summary": summaries}, stream, indent=2, allow_nan=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
