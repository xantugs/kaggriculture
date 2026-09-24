"""Many candidate variants per pinned world, sharing one reference replay per game.

A variant is (label, agent_path, {global_name: value}) : the agent is loaded fresh per run and the given
module globals are overwritten before play, so one built file can express many policies.
usage (as a module): run(games, S, variants, out_path) -> list of records
Each record: gid, opp, label, S, us, them, m, rec (recorded margin), rec_ok."""
import sys, os, json, time
from concurrent.futures import ProcessPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))

GAME_FILES = ['loss_0922c.json', 'loss_0922b.json', 'v10v11_top_0922.json', 'v12_all_0922.json', 'strong_new.json']


def load_games(files=GAME_FILES, team='offhand'):
    out = []
    for f in files:
        for i, d in enumerate(json.load(open(os.path.join(HERE, f), encoding='utf-8'))):
            if team in (d['info'].get('TeamNames') or []):
                out.append((f, i))
    return out


_CHAIN = {}


def layer_chain(path):
    """Named layer parent globals (`_X_PARENT = agent`) in file order."""
    import re
    if path not in _CHAIN:
        src = open(path, encoding='utf-8').read()
        _CHAIN[path] = re.findall(r"^(_[A-Za-z0-9_]*PARENT) *= *agent\s*$", src, flags=re.M)
    return _CHAIN[path]


def skip_layers(g, path, names):
    """Bypass each named layer: the next layer's parent becomes this layer's parent."""
    chain = layer_chain(path)
    for n in names:
        k = chain.index(n)
        if k + 1 < len(chain):
            g[chain[k + 1]] = g[n]


def _job(t):
    import lean, pinned
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    f, i, S, variants, team = t
    d = json.load(open(os.path.join(HERE, f), encoding='utf-8'))[i]
    names = d['info']['TeamNames']; P = names.index(team); O = 1 - P
    spawns, shops, rref = pinned.reference(d)
    rec_ok = [int(x) for x in rref] == [int(x) for x in d['rewards']]
    res = []
    for label, path, glb in variants:
        orig = pinned.install_pinned(S // 24, O, spawns, shops)
        try:
            A = lean.load(path)
            for k, v in (glb or {}).items():
                if k == '__skip__':
                    skip_layers(A.__globals__, path, v)
                else:
                    A.__globals__[k] = v
            ag = [None, None]
            ag[P] = pinned._prefixed(A, d['acts'], P, S)
            ag[O] = pinned._tape(d['acts'], O)
            r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
        finally:
            K._end_of_day = orig
        res.append(dict(gid=d['id'], opp=names[O], label=label, S=S, us=r['r'][P], them=r['r'][O],
                        m=(r['r'][P] - r['r'][O]) if r['r'][P] is not None else None,
                        rec=d['rewards'][P] - d['rewards'][O], rec_ok=rec_ok, shops=shops, err=r['err']))
    return res


def run(games, S, variants, out, team='offhand', chunk=None):
    """variants may be split into chunks per job so work spreads across processes."""
    chunk = chunk or len(variants)
    jobs = []
    for f, i in games:
        for c0 in range(0, len(variants), chunk):
            jobs.append((f, i, S, variants[c0:c0 + chunk], team))
    t0 = time.time(); allr = []
    with ProcessPoolExecutor(int(os.environ.get('PIN_WORKERS', '16'))) as ex, open(out, 'a', encoding='utf-8') as fh:
        for rs in ex.map(_job, jobs):
            for r in rs:
                fh.write(json.dumps(r, ensure_ascii=False) + '\n')
            fh.flush(); allr.extend(rs)
    print('runs', len(allr), 'wall', round(time.time() - t0), flush=True)
    return allr


def summary(rs):
    by = {}
    for r in rs:
        by.setdefault(r['label'], []).append(r)
    for lab, xs in by.items():
        xs = [x for x in xs if x['m'] is not None]
        w = sum(x['m'] > 0 for x in xs); n = max(1, len(xs))
        print(f"{lab:14s} {w:3d}-{len(xs)-w:<3d} margin {sum(x['m'] for x in xs)/n:+8.0f} us {sum(x['us'] for x in xs)/n:8.0f} them {sum(x['them'] for x in xs)/n:8.0f}")
