"""Local evaluation harness: independent agent instances, multi-seed, both seats."""
import importlib.util, sys, time, warnings, itertools, json, os, math
from pathlib import Path
warnings.filterwarnings("ignore")
import contextlib, io
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    from kaggle_environments import make

_counter = itertools.count()
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BUILTIN_AGENTS = {"starter", "random", "pass"}


class MatchError(RuntimeError):
    """A game failed; its rewards must not enter strategy comparisons."""
    def __init__(self, message, rewards=None, statuses=None):
        super().__init__(message)
        self.rewards = rewards
        self.statuses = statuses


def resolve_agent_path(path):
    """Accept paths from the caller, project root, tools, or versions directory."""
    path = str(path)
    if path in BUILTIN_AGENTS:
        return path
    requested = Path(path).expanduser()
    candidates = [requested] if requested.is_absolute() else [
        Path.cwd() / requested,
        PROJECT_ROOT / requested,
        PROJECT_ROOT / "tools" / requested,
        PROJECT_ROOT / "versions" / requested,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate.resolve())
    raise FileNotFoundError("Agent file not found: %s (searched %s)" % (
        path, ", ".join(str(p) for p in candidates)))


def _load_agent_module(path, params=None, debug=True):
    if params is not None and not isinstance(params, dict):
        raise TypeError("Agent parameter overrides must be a JSON object")
    path = resolve_agent_path(path)
    if path in BUILTIN_AGENTS:
        if params:
            raise ValueError("Built-in agent %s does not accept parameter overrides" % path)
        return path
    name = "agent_mod_%d" % next(_counter)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError("Cannot import agent file: %s" % path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if params:
        defaults = getattr(mod, "PARAMS", None)
        if not isinstance(defaults, dict):
            raise ValueError("Agent %s has no PARAMS dictionary" % path)
        unknown = set(params) - set(defaults)
        if unknown:
            raise ValueError("Unknown agent parameters for %s: %s" % (
                path, ", ".join(sorted(unknown))))
        mod.PARAMS.update(params)
    if hasattr(mod, "DEBUG"):
        mod.DEBUG = debug
    if not callable(getattr(mod, "agent", None)):
        raise ValueError("Agent file has no callable agent: %s" % path)
    return mod

def load_agent(path, params=None, debug=True):
    """Fresh module instance each call (own globals/memory) so self-play is honest."""
    mod = _load_agent_module(path, params, debug)
    return mod if isinstance(mod, str) else mod.agent


def describe_agent(path, params=None, debug=True):
    """Capture effective parameters and source identity for reproducible results."""
    import hashlib
    path = resolve_agent_path(path)
    mod = _load_agent_module(path, params, debug)
    return {
        "path": path,
        "sha256": None if isinstance(mod, str) else hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        "params": {} if isinstance(mod, str) else dict(getattr(mod, "PARAMS", {})),
        "overrides": dict(params or {}),
        "debug": debug,
    }

def run_match(spec0, spec1, seed, debug=True, steps=None):
    a0 = load_agent(*spec0, debug=debug) if isinstance(spec0, tuple) else load_agent(spec0, debug=debug)
    a1 = load_agent(*spec1, debug=debug) if isinstance(spec1, tuple) else load_agent(spec1, debug=debug)
    configuration = {"seed": seed}
    if steps is not None:
        configuration["episodeSteps"] = steps
    env = make("kaggriculture", debug=debug, configuration=configuration)
    env.run([a0, a1])
    last = env.steps[-1]
    rewards = [last[0].reward, last[1].reward]
    statuses = [last[0].status, last[1].status]
    if statuses != ["DONE", "DONE"]:
        raise MatchError("Game seed %s failed: statuses=%s, rewards=%s" % (
            seed, statuses, rewards), rewards, statuses)
    if any(isinstance(r, bool) or not isinstance(r, (int, float)) or not math.isfinite(r)
           for r in rewards):
        raise MatchError("Game seed %s returned invalid rewards: %s" % (
            seed, rewards), rewards, statuses)
    return env, rewards, statuses

def evaluate(specA, specB, seeds, both_seats=True, verbose=True):
    """Returns list of (moneyA, moneyB) over seeds (and both seatings)."""
    res = []
    for seed in seeds:
        seatings = [(specA, specB, 0)] + ([(specB, specA, 1)] if both_seats else [])
        for s0, s1, a_seat in seatings:
            t = time.time()
            env, rew, st = run_match(s0, s1, seed)
            mA, mB = (rew[0], rew[1]) if a_seat == 0 else (rew[1], rew[0])
            res.append((mA, mB))
            if verbose:
                print(f"  seed {seed} seatA={a_seat}: A=${mA:9.0f}  B=${mB:9.0f}  status={st}  ({time.time()-t:.1f}s)", flush=True)
    n = len(res)
    wins = sum(1 for a, b in res if a > b); ties = sum(1 for a, b in res if a == b)
    print(f"A mean ${sum(a for a,_ in res)/n:,.0f} | B mean ${sum(b for _,b in res)/n:,.0f} | A wins {wins}/{n} ties {ties}")
    return res

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("a"); ap.add_argument("b"); ap.add_argument("-n", type=int, default=4)
    ap.add_argument("--seed0", type=int, default=100)
    ap.add_argument("--one-seat", action="store_true")
    args = ap.parse_args()
    evaluate(args.a, args.b, range(args.seed0, args.seed0 + args.n), both_seats=not args.one_seat)
