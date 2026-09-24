"""Parallel paired benchmark with a stated decision rule.

benchmark.py runs games one at a time, which caps a session at a few dozen games and
leaves every small effect buried in seed noise. This runs them across processes and
reports the paired statistics that decide whether a change ships.

Pairing: each seed is played in both seats, and the seed's margin is the mean of the two.
That removes the seat advantage and most of the scenario noise, so the per-seed margin is
the unit of evidence, not the per-game margin.

    python tools/pbench.py --candidate main.py --opponent versions/main_v7.py -n 24 --seed0 50000
    python tools/pbench.py --params '{"hold_cap": 30}' -n 24 --seed0 50000 --label hold30

Each agent runs in its own process, so a wall-clock planning budget sees a loaded machine.
Measured per-turn agent time is ~4ms against a 1s limit, so contention is not a concern at
these worker counts; --jobs 1 reproduces serial timing if that ever changes.
"""
import argparse
import concurrent.futures as futures
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import statistics
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "tools"))


def _play(task):
    """Worker: one game. Imports inside the process so each has its own module state."""
    from harness import run_match
    cand, cand_params, opp, opp_params, seed, seat = task
    specs = [(cand, cand_params), (opp, opp_params)]
    if seat:
        specs.reverse()
    started = time.perf_counter()
    try:
        env, rewards, statuses = run_match(*specs, seed)
    except Exception as exc:
        return {"ok": False, "seed": seed, "candidate_seat": seat, "error": str(exc),
                "error_type": type(exc).__name__, "elapsed_seconds": time.perf_counter() - started}
    a, b = rewards[seat], rewards[1 - seat]
    return {"ok": True, "seed": seed, "candidate_seat": seat,
            "candidate_score": a, "opponent_score": b, "margin": a - b,
            "scores_by_seat": rewards, "statuses_by_seat": statuses,
            "elapsed_seconds": time.perf_counter() - started}


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def paired_stats(by_seed):
    """One observation per seed (mean of both seats). Returns the numbers that decide a ship."""
    seeds = sorted(by_seed)
    obs = [statistics.mean(by_seed[s]) for s in seeds]
    n = len(obs)
    mean = statistics.mean(obs)
    sd = statistics.stdev(obs) if n > 1 else float("nan")
    sem = sd / math.sqrt(n) if n > 1 else float("nan")
    t = mean / sem if n > 1 and sem > 0 else float("nan")
    better = sum(1 for v in obs if v > 0)
    return {"seed_pairs": n, "mean_seed_margin": mean, "sd_seed_margin": sd,
            "sem": sem, "t": t, "seeds_favouring_candidate": better,
            "ci95_low": mean - 1.96 * sem if n > 1 else float("nan"),
            "ci95_high": mean + 1.96 * sem if n > 1 else float("nan")}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--candidate", default="main.py")
    ap.add_argument("--params", default="{}", help="JSON parameter overrides for the candidate")
    ap.add_argument("--opponent", default="versions/main_v7.py")
    ap.add_argument("--opponent-params", default="{}")
    ap.add_argument("-n", type=int, default=16, help="Seeds; each is played in both seats")
    ap.add_argument("--seed0", type=int, default=50000)
    ap.add_argument("--seeds", type=int, nargs="+", help="Explicit seed list, overrides -n/--seed0")
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 4) - 2))
    ap.add_argument("--label", default="", help="Name for the log file")
    ap.add_argument("--output", help="Explicit JSONL path; refuses to overwrite")
    args = ap.parse_args(argv)

    seeds = args.seeds if args.seeds else list(range(args.seed0, args.seed0 + args.n))
    if len(set(seeds)) != len(seeds):
        ap.error("Seeds must be unique")
    try:
        cand_params = json.loads(args.params)
        opp_params = json.loads(args.opponent_params)
    except ValueError as exc:
        ap.error("Bad --params JSON: %s" % exc)

    from harness import describe_agent, resolve_agent_path
    try:
        candidate = describe_agent(args.candidate, cand_params)
        opponent = describe_agent(args.opponent, opp_params)
    except (ValueError, TypeError, OSError) as exc:
        ap.error(str(exc))
    cand_path = resolve_agent_path(args.candidate)
    opp_path = resolve_agent_path(args.opponent)

    stamp = datetime.now(timezone.utc)
    name = args.label or stamp.strftime("pbench_%Y%m%dT%H%M%SZ")
    output = Path(args.output) if args.output else PROJECT_ROOT / "logs" / (name + ".jsonl")
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        ap.error("Refusing to overwrite %s" % output)

    try:
        version = importlib.metadata.version("kaggle-environments")
    except importlib.metadata.PackageNotFoundError:
        version = "unknown"

    tasks = [(cand_path, cand_params, opp_path, opp_params, seed, seat)
             for seed in seeds for seat in (0, 1)]
    header = {"record": "header", "started_utc": stamp.isoformat(), "environment": "kaggriculture",
              "environment_version": version, "jobs": args.jobs, "seeds": seeds,
              "candidate": candidate, "opponent": opponent}
    print("candidate %s %s" % (Path(cand_path).name, cand_params or ""), flush=True)
    print("opponent  %s %s" % (Path(opp_path).name, opp_params or ""), flush=True)
    print("%d games (%d seeds x 2 seats) on %d workers -> %s" %
          (len(tasks), len(seeds), args.jobs, output), flush=True)

    by_seed = {}
    failures = []
    started = time.perf_counter()
    with output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(header) + "\n")
        with futures.ProcessPoolExecutor(max_workers=args.jobs) as pool:
            for i, rec in enumerate(pool.map(_play, tasks), 1):
                stream.write(json.dumps(rec, allow_nan=False) + "\n")
                stream.flush()
                if not rec["ok"]:
                    failures.append(rec)
                    print("FAILED seed=%s seat=%s: %s" % (rec["seed"], rec["candidate_seat"],
                                                          rec["error"]), flush=True)
                    continue
                by_seed.setdefault(rec["seed"], []).append(rec["margin"])
                print("  [%3d/%d] seed %6d seat %d  %+9.0f" %
                      (i, len(tasks), rec["seed"], rec["candidate_seat"], rec["margin"]), flush=True)

    if failures:
        print("\n%d games FAILED; their seeds are excluded from the statistics." % len(failures))
    complete = {s: v for s, v in by_seed.items() if len(v) == 2}
    if not complete:
        print("No complete seed pairs.")
        return 1

    games = [m for v in complete.values() for m in v]
    wins = sum(m > 0 for m in games)
    losses = sum(m < 0 for m in games)
    stats = paired_stats(complete)
    elapsed = time.perf_counter() - started

    print("\n=== %d complete seed pairs, %d games in %.0fs ===" % (len(complete), len(games), elapsed))
    print("per-game     W/L/T %d/%d/%d" % (wins, losses, len(games) - wins - losses))
    print(f"per-seed     mean margin ${stats['mean_seed_margin']:+,.0f}   "
          f"sd ${stats['sd_seed_margin']:,.0f}   sem ${stats['sem']:,.0f}")
    print(f"             95% CI [${stats['ci95_low']:+,.0f}, ${stats['ci95_high']:+,.0f}]   "
          f"t = {stats['t']:+.2f}")
    print(f"             {stats['seeds_favouring_candidate']} of {stats['seed_pairs']} "
          f"seeds favour the candidate")
    verdict = ("SHIP: the interval excludes zero on the positive side"
               if stats["ci95_low"] > 0 else
               "REJECT: the interval excludes zero on the negative side"
               if stats["ci95_high"] < 0 else
               "UNDECIDED: the interval spans zero - more seeds, or the effect is too small to matter")
    print("verdict      %s" % verdict)
    if stats["sd_seed_margin"] == stats["sd_seed_margin"] and stats["sd_seed_margin"] > 0:
        # The paired sd depends on how similar the two agents are: near-identical agents
        # mirror each other across the seat swap and the variance nearly cancels. Treat
        # these counts as a floor, and re-read the sd for each new candidate.
        for target in (500, 1000, 2000):
            need = max(4, math.ceil((1.96 * stats["sd_seed_margin"] / target) ** 2))
            print(f"             detecting a ${target}/seed effect at 95% "
                  f"needs >= {need} seed pairs at this sd")

    stats = {k: (None if isinstance(v, float) and not math.isfinite(v) else v)
             for k, v in stats.items()}
    summary = {"results_file": str(output.resolve()), "seeds": seeds,
               "complete_seed_pairs": sorted(complete), "failures": len(failures),
               "candidate": candidate, "opponent": opponent,
               "per_game": {"games": len(games), "wins": wins, "losses": losses,
                            "ties": len(games) - wins - losses},
               "paired": stats, "verdict": verdict, "elapsed_seconds": elapsed}
    with output.with_suffix(".summary.json").open("x", encoding="utf-8") as stream:
        json.dump(summary, stream, indent=2, allow_nan=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
