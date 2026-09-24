"""Prefix counterfactual on recorded games: our seat replays its recorded actions for steps < S, then the candidate
plays; the opponent replays its recorded tape.  From the end of day S//24 the engine RNG is decoupled (decouple.py),
so candidate and baseline face the same town and the opponent the same weeds.
usage: pfx.py dataset(el|own|file.json) S cand1,cand2,... out.jsonl"""
import sys, os, json, glob, lean, ident2, decouple
from concurrent.futures import ProcessPoolExecutor
def dataset(name):
    out = []
    if name == 'el':
        lib = json.load(open('runs/xplib_all.json'))
        idx = {}
        for f in sorted(glob.glob('cf/el/*.json')):
            for i, d in enumerate(json.load(open(f))): idx[d['id']] = (f, i)
        for e in lib: out.append((idx[e['id']][0], idx[e['id']][1], e['team']))
    elif name == 'own':
        for dd in ('v7a', 'v8a', 'v8b', 'v8c', 'v8d'):
            for f in sorted(glob.glob(f'cf/{dd}/*.json')):
                for i, d in enumerate(json.load(open(f))):
                    if 'Khantugs Gantulga' in d['info']['TeamNames']: out.append((f, i, 'Khantugs Gantulga'))
    elif name in ('v9', 'own2'):
        dirs = ['v9a'] + (['v7a', 'v8a', 'v8b', 'v8c', 'v8d'] if name == 'own2' else [])
        for dd in dirs:
            for f in sorted(glob.glob(f'cf/{dd}/*.json')):
                for i, d in enumerate(json.load(open(f))):
                    if 'Khantugs Gantulga' in d['info']['TeamNames']: out.append((f, i, 'Khantugs Gantulga'))
    else:
        out = [tuple(x) for x in json.load(open(name))]
    return out
def prefixed(inner, acts, P, S):
    def f(obs, cfg=None):
        a = inner(obs, cfg)
        t = obs['step']
        if t < S:
            r = acts[t + 1][P] if t + 1 < len(acts) else None
            return r if isinstance(r, dict) else {"farmer": ["PASS"], "hands": [], "market": []}
        return a
    return f
def job(t):
    f, i, team, cand, S = t
    if not os.environ.get('NODECOUPLE'): decouple.install(S // 24)
    d = json.load(open(f))[i]; names = d['info']['TeamNames']; P = names.index(team)
    A = lean.load(cand)
    ag = [ident2._tape(d['acts'], 0), ident2._tape(d['acts'], 1)]; ag[P] = prefixed(A, d['acts'], P, S)
    r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
    rep = {}
    for k in ('_TB_REPORT', '_CP_REPORT', '_XP_REPORT', '_KSUB_REPORT', '_P2_REPORT', '_WRT_REPORT', '_DRIP_REPORT', '_SLOT_REPORT', '_EB_REPORT', '_GLUTH_REPORT', '_C2F_REPORT', '_FG_REPORT', '_WF_REPORT'):
        if k in A.__globals__: rep.update({kk: v for kk, v in A.__globals__[k].items() if isinstance(v, (int, float)) and v})
    return dict(gid=d['id'], team=team, cand=cand, S=S, dc=not os.environ.get('NODECOUPLE'), rec=d['rewards'][P] - d['rewards'][1 - P], us=int(r['r'][P]), m=int(r['r'][P] - r['r'][1 - P]), rep=rep)
if __name__ == '__main__':
    ds, S, cands, out = sys.argv[1], int(sys.argv[2]), sys.argv[3].split(','), sys.argv[4]
    done = set()
    try:
        for l in open(out):
            r = json.loads(l); done.add((r['gid'], r['team'], r['cand'], r['S']))
    except FileNotFoundError: pass
    jobs = []
    for f, i, team in dataset(ds):
        gid = json.load(open(f))[i]['id']
        for c in cands:
            if (gid, team, c, S) not in done: jobs.append((f, i, team, c, S))
    print(len(jobs), 'jobs', flush=True)
    with ProcessPoolExecutor(2) as ex, open(out, 'a') as fh:
        for r in ex.map(job, jobs):
            fh.write(json.dumps(r, ensure_ascii=False) + '\n'); fh.flush()
