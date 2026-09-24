"""Identify which local candidate file produced our recorded live actions.
usage: ident.py games.json cand1,cand2,... [team=offhand] [maxgames]"""
import sys, os, json
sys.path.insert(0, '/home/user/kaggriculture/arena')
import lean

def norm(a):
    return json.dumps(a, sort_keys=True) if isinstance(a, dict) else str(a)

def check(d, cand, team='offhand'):
    names = d['info']['TeamNames']; P = names.index(team); O = 1 - P
    acts = d['acts']
    inner = lean.load(cand)
    first = [None]; n = [0]
    def mine(obs, cfg=None):
        t = obs['step']
        a = inner(obs, cfg)
        rec = acts[t + 1][P] if t + 1 < len(acts) else None
        if first[0] is None and norm(a) != norm(rec):
            first[0] = (t, a, rec)
        n[0] += 1
        return rec if isinstance(rec, dict) else {"farmer": ["PASS"], "hands": [], "market": []}
    def opp(obs, cfg=None):
        t = obs['step']
        a = acts[t + 1][O] if t + 1 < len(acts) else None
        return a if isinstance(a, dict) else {"farmer": ["PASS"], "hands": [], "market": []}
    objs = [mine, opp] if P == 0 else [opp, mine]
    r = lean.play(None, None, d['info']['seed'], agent_objs=objs)
    ok = [round(x) for x in r['r']] == [round(x) for x in d['rewards']]
    return ok, first[0]

if __name__ == '__main__':
    games = json.load(open(sys.argv[1]))
    cands = sys.argv[2].split(',')
    team = sys.argv[3] if len(sys.argv) > 3 else 'offhand'
    mx = int(sys.argv[4]) if len(sys.argv) > 4 else 3
    for d in games[:mx]:
        for c in cands:
            ok, first = check(d, c, team)
            fs = 'MATCH ALL' if first is None else 'first diff step %d' % first[0]
            print(d['info']['EpisodeId'], os.path.basename(c), 'replay_ok', ok, fs, flush=True)
