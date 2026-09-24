"""Mean (opponent - us) cash by day in recorded games, split by class. usage: cashgap.py"""
import sys, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
from concurrent.futures import ProcessPoolExecutor
def job(fn):
    import lean, pinned
    d = json.load(open(fn, encoding='utf-8'))[0]
    n = d['info']['TeamNames']; P = n.index('offhand'); money = {}
    def w(p, inner):
        def f(obs, cfg=None):
            s = int(obs['step'])
            if s % 24 == 0 and p == P: money[s // 24] = (obs['farms'][P]['money'], obs['farms'][1 - P]['money'])
            return inner(obs, cfg)
        return f
    r = lean.play(None, None, d['info']['seed'], agent_objs=[w(0, pinned._tape(d['acts'], 0)), w(1, pinned._tape(d['acts'], 1))])
    money[30] = (r['r'][P], r['r'][1 - P])
    return d['id'], money
if __name__ == '__main__':
    cls = json.load(open(os.path.join(HERE, 'gameclass.json'))); files = json.load(open(os.path.join(HERE, 'g2800_list.json')))
    acc = {'MIRROR': collections.defaultdict(list), 'DIVERGENT': collections.defaultdict(list)}
    with ProcessPoolExecutor(3) as ex:
        for gid, money in ex.map(job, files):
            c = cls.get(str(gid))
            if c is None: continue
            k = 'MIRROR' if c >= 0.8 else 'DIVERGENT'
            for dday, (u, o) in money.items(): acc[k][dday].append(o - u)
    for k in acc:
        print(k, ' '.join(f"d{dd}:{sum(v) / len(v):+.0f}" for dd, v in sorted(acc[k].items()) if dd % 2 == 0 or dd == 29 or dd == 30))
