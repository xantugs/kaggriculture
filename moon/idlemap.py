import sys, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
from concurrent.futures import ProcessPoolExecutor
def job(fn):
    import lean, pinned
    d = json.load(open(fn, encoding='utf-8'))[0]
    P = d['info']['TeamNames'].index('offhand'); O = 1 - P
    spawns, shops, _ = pinned.reference(d)
    orig = pinned.install_pinned(4, O, spawns, shops)
    A = lean.load(os.path.join(HERE, '..', 'arena', 'cand', 'omw_ad_a1.py'))
    info = {}
    def f(obs, cfg=None):
        a = A(obs, cfg); s = obs['step']
        if s % 24 == 12 and s // 24 in (12, 15, 18, 21, 24):
            me = obs['farms'][obs['player']]
            info[s // 24] = (sorted((x, y) for y, row in enumerate(me['tiles']) for x, t in enumerate(row) if t is None), list(me['unlocked_quadrants']), len(me['hands']))
        return a
    ag = [None, None]; ag[P] = pinned._prefixed(f, d['acts'], P, 96); ag[O] = pinned._tape(d['acts'], O)
    lean.play(None, None, d['info']['seed'], agent_objs=ag)
    return os.path.basename(fn)[:-5], info
if __name__ == '__main__':
    cls = json.load(open('gameclass.json'))
    files = json.load(open('g2800_list.json'))[::5]
    se = 0; cnt = collections.Counter(); per = collections.defaultdict(list); hands = collections.defaultdict(list)
    with ProcessPoolExecutor(int(os.environ.get('WORKERS', '4'))) as ex:
        for gid, info in ex.map(job, files):
            if 'SE' in info.get(15, ([], []))[1]: se += 1
            for day, (em, q, h) in info.items():
                per[day].append(len(em)); hands[day].append(h)
                if day == 15:
                    for p in em: cnt[p] += 1
    print('games', len(files), 'with SE by day 15:', se)
    for day in sorted(per): print('day', day, 'empty tiles mean', round(sum(per[day]) / len(per[day]), 1), 'dist', sorted(per[day]), 'hands mean', round(sum(hands[day]) / len(hands[day]), 1))
    print('most common empty tiles day 15:', cnt.most_common(30))
