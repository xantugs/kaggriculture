"""How do opponents that share our opening diverge? Farm composition, land and cash for both seats at given steps.
usage: divergence.py [class=mirror6]"""
import sys, os, json, collections
from concurrent.futures import ProcessPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
import pinmulti
STEPS = tuple(int(x) for x in os.environ.get('DV_STEPS', '167,215,263,311,359,431').split(','))


def comp(farm):
    c = collections.Counter()
    for row in farm['tiles']:
        for t in row:
            if isinstance(t, dict):
                c[t.get('crop') or t.get('animal') or t['kind']] += 1
    c['LAND'] = len(farm['unlocked_quadrants'])
    c['HANDS'] = len(farm['hands'])
    return c


def job(t):
    import lean, pinned
    f, i = t
    d = json.load(open(os.path.join(HERE, f), encoding='utf-8'))[i]
    names = d['info']['TeamNames']; P = names.index('offhand'); O = 1 - P
    snaps = {}; hires = [collections.Counter(), collections.Counter()]
    def w(obs, cfg=None):
        s = obs['step']
        if s in STEPS:
            snaps[s] = (comp(obs['farms'][P]), comp(obs['farms'][O]), obs['farms'][P]['money'], obs['farms'][O]['money'])
        return pinned._tape(d['acts'], 0)(obs, cfg)
    lean.play(None, None, d['info']['seed'], agent_objs=[w, pinned._tape(d['acts'], 1)], max_steps=max(STEPS) + 1)
    return d['id'], names[O], {s: (dict(a), dict(b), ma, mb) for s, (a, b, ma, mb) in snaps.items()}


if __name__ == '__main__':
    want = sys.argv[1] if len(sys.argv) > 1 else 'mirror6'
    if want.endswith('.json'):
        who = sys.argv[2] if len(sys.argv) > 2 else None
        games = [(want, i) for i, d in enumerate(json.load(open(os.path.join(HERE, want), encoding='utf-8'))) if not who or who in ' '.join(d['info']['TeamNames'])]
    else:
        cls = {}
        for r in json.load(open(os.path.join(HERE, 'opp_class.json'), encoding='utf-8')):
            cls[r['gid']] = ('mirror15' if r['sim359'] >= 0.8 else ('mirror6' if r['sim143'] >= 0.9 else 'other'), r['rec'])
        games = [(f, i) for f, i in pinmulti.load_games() if cls.get(json.load(open(os.path.join(HERE, f), encoding='utf-8'))[i]['id'], ('?',))[0] == want]
    with ProcessPoolExecutor(4) as ex:
        res = list(ex.map(job, games))
    keys = ['STRAWBERRY', 'WHEAT', 'TOMATO', 'CARROT', 'MELON', 'COW', 'SHEEP', 'GOOSE', 'LAND', 'HANDS']
    for s in STEPS:
        us = collections.Counter(); them = collections.Counter(); mu = mt = 0; n = 0
        for gid, opp, sn in res:
            if s in sn:
                us.update(sn[s][0]); them.update(sn[s][1]); mu += sn[s][2]; mt += sn[s][3]; n += 1
        print(f"day {s // 24:2d}  " + '  '.join(f"{k[:5]} {us[k]/n:4.1f}|{them[k]/n:4.1f}" for k in keys) + f"  cash {mu/n:6.0f}|{mt/n:6.0f}")
    print(len(res), 'games,', want)
    for gid, opp, sn in res:
        s = STEPS[len(STEPS) // 2]
        if s in sn:
            b = sn[s][1]
            print(' ', opp[:18], {k: b.get(k, 0) for k in keys}, 'cash', int(sn[s][3]))
