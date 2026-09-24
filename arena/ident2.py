"""For each recorded episode: (1) sanity replay, (2) identify the opponent among candidate agents by
step-by-step action matching (abort at first divergence), (3) counterfactual: our candidate agent in our
seat vs the opponent (identified agent closed-loop if exact match, else the opponent's recorded tape)."""
import json, sys, os, time
from concurrent.futures import ProcessPoolExecutor

FOCUS = "Khantugs Gantulga"

class Diverged(BaseException):
    pass

def norm(a):
    return json.loads(json.dumps(a))

def _tape(acts, p):
    def f(obs, cfg=None):
        t = obs['step']
        a = acts[t + 1][p] if t + 1 < len(acts) else None
        return a if isinstance(a, dict) else {"farmer": ["PASS"], "hands": [], "market": []}
    return f

def ident_job(t):
    import lean
    path, idx, cand = t
    d = json.load(open(path))[idx]
    names = d['info']['TeamNames']; fs = names.index(FOCUS); os_ = 1 - fs
    acts = d['acts']; seed = d['info']['seed']
    o = lean.load(cand)
    last = {"step": -1}
    def wrapped(obs, cfg=None):
        a = norm(o(obs, cfg))
        t = obs['step']
        rec = acts[t + 1][os_] if t + 1 < len(acts) else None
        if isinstance(rec, dict) and a != rec:
            raise Diverged(t)
        last["step"] = t
        return a
    agents = [None, None]; agents[fs] = _tape(acts, fs); agents[os_] = wrapped
    try:
        r = lean.play(None, None, seed, agent_objs=agents)
        ok = [int(x) for x in r['r']] == [int(x) for x in d['rewards']]
        return (d['id'], cand, 720 if ok else 719, ok)
    except Diverged as e:
        return (d['id'], cand, int(e.args[0]), False)

def cf_job(t):
    import lean
    path, idx, mine, opp = t
    d = json.load(open(path))[idx]
    names = d['info']['TeamNames']; fs = names.index(FOCUS); os_ = 1 - fs
    acts = d['acts']; seed = d['info']['seed']
    agents = [None, None]
    agents[fs] = lean.load(mine)
    agents[os_] = lean.load(opp) if opp else _tape(acts, os_)
    r = lean.play(None, None, seed, agent_objs=agents)
    return (d['id'], mine, opp, r['r'][fs], r['r'][os_], r['st'])

if __name__ == '__main__':
    mode = sys.argv[1]; path = sys.argv[2]
    n = len(json.load(open(path)))
    if mode == 'ident':
        cands = sys.argv[3].split(',')
        jobs = [(path, i, c) for i in range(n) for c in cands]
        with ProcessPoolExecutor(2) as ex:
            for res in ex.map(ident_job, jobs, chunksize=1):
                print(json.dumps(res), flush=True)
    elif mode == 'cf':
        mine = sys.argv[3]
        opp = json.loads(open(sys.argv[4]).read()) if len(sys.argv) > 4 else {}
        data = json.load(open(path))
        jobs = [(path, i, mine, opp.get(str(data[i]['id']))) for i in range(n)]
        with ProcessPoolExecutor(2) as ex:
            for res in ex.map(cf_job, jobs, chunksize=1):
                print(json.dumps(res), flush=True)
