"""Does our local v9 reproduce its live games? v9 in our seat from step 0 vs the opponent's recorded tape."""
import sys, json, glob, lean, ident2
from concurrent.futures import ProcessPoolExecutor
def job(t):
    f, i, cand = t
    d = json.load(open(f))[i]; names = d['info']['TeamNames']; P = names.index('Khantugs Gantulga')
    A = lean.load(cand); first = {}
    def spy(obs, cfg=None):
        a = A(obs, cfg); s = obs['step']
        rec = d['acts'][s + 1][P] if s + 1 < len(d['acts']) else None
        if 'div' not in first and isinstance(rec, dict) and json.dumps(a, sort_keys=True) != json.dumps(rec, sort_keys=True):
            first['div'] = s
        return a
    ag = [ident2._tape(d['acts'], 0), ident2._tape(d['acts'], 1)]; ag[P] = spy
    r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
    return d['id'], names[1 - P][:14], d['rewards'][P] - d['rewards'][1 - P], int(r['r'][P] - r['r'][1 - P]), first.get('div')
if __name__ == '__main__':
    G = [(f, i) for f in sorted(glob.glob(sys.argv[1])) for i in range(len(json.load(open(f))))]
    with ProcessPoolExecutor(2) as ex:
        for r in ex.map(job, [(f, i, sys.argv[2]) for f, i in G]): print(r, flush=True)
