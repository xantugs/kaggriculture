"""Split a games file into per-game files and classify each game by our/rival farm similarity at steps 143/359.
usage: holdprep.py games.json outdir list.json class.json"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
from concurrent.futures import ProcessPoolExecutor
def sig(farm):
    out = []
    for row in farm['tiles']:
        for t in row:
            if t is None or (isinstance(t, dict) and t.get('kind') == 'WEED'): out.append('.')
            elif t == 'LOCKED': out.append('#')
            elif isinstance(t, dict): out.append(str(t.get('crop') or t.get('animal') or t.get('kind')))
            else: out.append('?')
    return out
def job(fn):
    import lean, pinned
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    d = json.load(open(fn, encoding='utf-8'))[0]
    P = d['info']['TeamNames'].index('offhand')
    sims = {}
    opm = K._process_market
    def pm(state, env):
        o = state[0].observation
        if o.step in (143, 359):
            a, b = sig(o.farms[P]), sig(o.farms[1 - P]); sims[o.step] = sum(x == y for x, y in zip(a, b)) / len(a)
        return opm(state, env)
    K._process_market = pm
    try:
        lean.play(None, None, d['info']['seed'], agent_objs=[pinned._tape(d['acts'], 0), pinned._tape(d['acts'], 1)], max_steps=362)
    finally:
        K._process_market = opm
    return d['id'], sims.get(359, 0)
if __name__ == '__main__':
    games = json.load(open(sys.argv[1], encoding='utf-8')); outdir = sys.argv[2]
    os.makedirs(outdir, exist_ok=True); files = []
    for d in games:
        if 'offhand' not in d['info']['TeamNames']: continue
        fn = os.path.join(outdir, '%d.json' % d['id']); json.dump([d], open(fn, 'w', encoding='utf-8')); files.append(fn)
    json.dump(files, open(sys.argv[3], 'w'))
    cls = {}
    with ProcessPoolExecutor(12) as ex:
        for gid, s in ex.map(job, files): cls[str(gid)] = s
    json.dump(cls, open(sys.argv[4], 'w'))
    print('games', len(files), 'mirror(>=0.8)', sum(v >= 0.8 for v in cls.values()))
