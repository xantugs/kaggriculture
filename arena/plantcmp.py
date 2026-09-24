import json, glob, sys, collections, lean, ident2
from concurrent.futures import ProcessPoolExecutor
def job(t):
    f, gi = t
    d = json.load(open(f))[gi]; n = d['info']['TeamNames']; P = n.index('Khantugs Gantulga'); acts = d['acts']
    snap = {}
    def spy(obs, cfg=None, ag=ident2._tape(acts, P)):
        s = int(obs['step'])
        if s % 24 == 12 and s // 24 in (1, 5, 8, 12, 16):
            row = []
            for pl in (P, 1 - P):
                c = collections.Counter()
                for r in obs['farms'][pl]['tiles']:
                    for tt in r:
                        if isinstance(tt, dict) and tt.get('kind') == 'PLANT': c[tt.get('crop')] += 1
                        elif isinstance(tt, dict) and tt.get('animal'): c[tt.get('animal')] += 1
                row.append(dict(c))
            snap[s // 24] = row
        return ag(obs, cfg)
    ag = [ident2._tape(acts, 0), ident2._tape(acts, 1)]; ag[P] = spy
    lean.play(None, None, d['info']['seed'], agent_objs=ag, max_steps=16 * 24 + 13)
    return d['id'], n[1 - P][:14], d['rewards'][P] - d['rewards'][1 - P], snap
if __name__ == '__main__':
    G = [(f, i) for f in sorted(glob.glob(sys.argv[1])) for i in range(len(json.load(open(f))))]
    with ProcessPoolExecutor(2) as ex:
        for gid, opp, m, snap in ex.map(job, G):
            u1, t1 = snap[1]; u12, t12 = snap[12]
            print(gid, '%-14s %6d' % (opp, m), 'd1 wheat %s/%s' % (u1.get('WHEAT', 0), t1.get('WHEAT', 0)), '| d12 straw %s/%s melon %s/%s sheep %s/%s cow %s/%s' % (u12.get('STRAWBERRY', 0), t12.get('STRAWBERRY', 0), u12.get('MELON', 0), t12.get('MELON', 0), u12.get('SHEEP', 0), t12.get('SHEEP', 0), u12.get('COW', 0), t12.get('COW', 0)), flush=True)
