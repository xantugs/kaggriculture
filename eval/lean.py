"""Lean kaggriculture runner: same interpreter, same observation cloning semantics, no framework overhead.
Validated against kaggle_environments' env.run for exact reward equality (see validate())."""
import sys, os, time, json, contextlib, io, warnings, copy
warnings.filterwarnings("ignore")
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    from kaggle_environments.utils import Struct, structify

_CFG_DEFAULTS = {}
for k, v in K.specification["configuration"].items():
    if isinstance(v, dict) and "default" in v:
        _CFG_DEFAULTS[k] = v["default"]
    elif not isinstance(v, dict):
        _CFG_DEFAULTS[k] = v
_CFG_DEFAULTS.setdefault("episodeSteps", 720)
_CFG_DEFAULTS.setdefault("actTimeout", 1)
_CFG_DEFAULTS.setdefault("runTimeout", 1200)

class _Env:
    def __init__(self, seed, overrides=None):
        cfg = dict(_CFG_DEFAULTS)
        if overrides: cfg.update(overrides)
        cfg["seed"] = seed
        self.configuration = Struct(**cfg)
        self.info = {}
        self.done = False

_SRC = {}
def load(path):
    if path not in _SRC:
        raw = open(path, encoding="utf-8").read()
        _SRC[path] = compile(raw, path, "exec")
    code = _SRC[path]
    g = {"__name__": "agent_module_%d" % len(_SRC), "__file__": path}
    d = os.path.dirname(os.path.abspath(path))
    sys.path.append(d)
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            exec(code, g)
    finally:
        sys.path.pop()
    return [v for v in g.values() if callable(v)][-1]

def _hook(d):
    return Struct(**d)

def _clone(o):
    # structify-equivalent deep clone via JSON (agents on Kaggle receive JSON-decoded Structs)
    return json.loads(json.dumps(o), object_hook=_hook)

SHARED = ("farms", "market", "town", "day", "hour", "step")

def play(pa, pb, seed, record=False, cfg_overrides=None, agent_objs=None, max_steps=None):
    """pa plays seat 0, pb seat 1. Returns dict with rewards, statuses, timing."""
    agents = agent_objs if agent_objs is not None else [load(pa), load(pb)]
    env = _Env(seed, cfg_overrides)
    cfgs = [_clone(dict(env.configuration)), _clone(dict(env.configuration))]
    state = [Struct(observation=Struct(step=0, remainingOverageTime=60, player=i), action=None,
                    reward=0, status="ACTIVE", info=Struct()) for i in range(2)]
    with contextlib.redirect_stdout(io.StringIO()):
        K.interpreter(state, env)
    # after reset, kaggle sets cfg seed None; agents never see it
    for c in cfgs: c["seed"] = None
    tmax = [0.0, 0.0]; tsum = [0.0, 0.0]; over = [0.0, 0.0]
    errors = [None, None]
    rec = [] if record else None
    step_counter = 0
    while True:
        obs0 = state[0].observation
        actions = []
        for i in range(2):
            if state[i].status != "ACTIVE":
                actions.append(None); continue
            o = {k: obs0[k] for k in SHARED if k in obs0}
            oi = state[i].observation
            o["player"] = oi["player"]; o["private"] = oi["private"]
            o["remainingOverageTime"] = oi.get("remainingOverageTime", 60)
            ob = _clone(o)
            t = time.perf_counter()
            try:
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    a = agents[i](ob, cfgs[i])
                a = json.loads(json.dumps(a))
            except Exception as e:
                a = e
            dt = time.perf_counter() - t
            tsum[i] += dt; tmax[i] = max(tmax[i], dt); over[i] += max(0.0, dt - 1.0)
            actions.append(a)
        if rec is not None:
            rec.append(actions)
        for i in range(2):
            a = actions[i]
            state[i]["action"] = None
            if state[i].status != "ACTIVE":
                continue
            if isinstance(a, BaseException):
                state[i].status = "ERROR"; errors[i] = repr(a)[:300]
            elif not isinstance(a, dict):
                state[i].status = "INVALID"; errors[i] = "non-dict action %r" % (type(a),)
            else:
                state[i]["action"] = structify(a)
                state[i].action = state[i]["action"]
        # mirror framework: interpreter sees structified state
        with contextlib.redirect_stdout(io.StringIO()):
            K.interpreter(state, env)
        step_counter += 1
        state[0].observation.step = step_counter
        for s in state:
            if s.status in ("ERROR", "INVALID", "TIMEOUT"):
                s.reward = None
        if state[0].observation.step >= env.configuration.episodeSteps - 1:
            for s in state:
                if s.status in ("ACTIVE", "INACTIVE"):
                    s.status = "DONE"
        if all(s.status != "ACTIVE" for s in state):
            break
        if max_steps is not None and step_counter >= max_steps:
            break
    out = {"seed": seed, "r": [state[0].reward, state[1].reward], "st": [state[0].status, state[1].status],
           "tmax": [round(x, 4) for x in tmax], "tsum": [round(x, 3) for x in tsum], "over": [round(x, 3) for x in over],
           "err": errors, "steps": step_counter}
    out["shops"] = list(state[0].observation.town.get("unlocked_shops", []))
    if record:
        out["actions"] = rec
        out["final_obs"] = state[0].observation
    return out

if __name__ == "__main__":
    t = time.time()
    r = play(sys.argv[1], sys.argv[2], int(sys.argv[3]))
    r["wall"] = round(time.time() - t, 2)
    print(json.dumps(r))
