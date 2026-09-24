"""Label each recorded game's opponent by farm similarity to ours (weeds ignored) at steps 143 and 359.
usage: classify.py out.json"""
import sys, os, json
from concurrent.futures import ProcessPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
import pinmulti


def sig(farm):
    out = []
    for row in farm['tiles']:
        for t in row:
            if t is None or (isinstance(t, dict) and t.get('kind') == 'WEED'):
                out.append('.')
            elif t == 'LOCKED':
                out.append('#')
            else:
                out.append(str(t.get('crop') or t.get('animal') or t.get('kind')))
    return out


def sim(a, b):
    return sum(x == y for x, y in zip(a, b)) / len(a)


def job(t):
    import lean, pinned
    f, i = t
    d = json.load(open(os.path.join(HERE, f), encoding='utf-8'))[i]
    names = d['info']['TeamNames']; P = names.index('offhand'); O = 1 - P
    snaps = {}
    def w(obs, cfg=None):
        s = obs['step']
        if s in (143, 359, 500):
            snaps[s] = (sig(obs['farms'][P]), sig(obs['farms'][O]), obs['farms'][O]['money'], len(obs['farms'][O]['hands']))
        return pinned._tape(d['acts'], 0)(obs, cfg)
    ag = [w, pinned._tape(d['acts'], 1)] if True else None
    lean.play(None, None, d['info']['seed'], agent_objs=ag, max_steps=501)
    out = dict(gid=d['id'], opp=names[O], rec=d['rewards'][P] - d['rewards'][O])
    for s, (a, b, money, hands) in snaps.items():
        out['sim%d' % s] = round(sim(a, b), 3)
    rt = [x for x in snaps[500][1]]
    out['opp_d20'] = {k: rt.count(k) for k in set(rt) if k not in ('.', '#')}
    return out


if __name__ == '__main__':
    games = pinmulti.load_games(pinmulti.GAME_FILES)
    with ProcessPoolExecutor(4) as ex:
        res = list(ex.map(job, games))
    json.dump(res, open(sys.argv[1], 'w', encoding='utf-8'), ensure_ascii=False)
    m = sum(1 for r in res if r['sim143'] >= 0.9)
    print('games', len(res), 'mirror@143', m, 'mirror@359', sum(1 for r in res if r['sim359'] >= 0.8))
