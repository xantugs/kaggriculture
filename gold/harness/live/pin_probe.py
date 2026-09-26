"""One pinned game with a candidate: daily farm composition of both sides + money + seeds bought.
usage: pin_probe.py games.json gid S cand.py [team]"""
import sys, os, json, collections
sys.argv = [sys.argv[0]] + [os.path.abspath(a) if a.endswith(('.json', '.py')) else a for a in sys.argv[1:]]
HERE = '/home/user/kaggriculture/moon'
sys.path.insert(0, os.path.join(HERE, '..', 'arena')); sys.path.insert(0, '/home/user/kaggriculture/gold/harness')
os.chdir(HERE)
import pinned4
from kaggle_environments.envs.kaggriculture import kaggriculture as K
path, gid, S, cand = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
team = sys.argv[5] if len(sys.argv) > 5 else 'offhand'
games = json.load(open(path)); idx = [i for i, g in enumerate(games) if str(g['id']) == gid][0]
d = games[idx]; P = d['info']['TeamNames'].index(team); O = 1 - P
OUT = []; SEEDS = collections.Counter()
opm = K._process_market
def snap(farm):
    c = collections.Counter()
    for row in farm['tiles']:
        for t in row:
            if isinstance(t, dict):
                c[(t.get('crop') or t.get('animal') or t.get('kind'))[:2].lower()] += 1
            elif t is None:
                c['..'] += 1
    return ' '.join('%s%d' % kv for kv in sorted(c.items()))
def pm(state, env):
    st = state[0].observation.step
    if st % 24 == 0 and st >= 24 * 10:
        f = state[0].observation.farms
        OUT.append('d%02d $%6d $%6d | us %-58s | them %s' % (st // 24, f[P]['money'], f[O]['money'], snap(f[P]), snap(f[O])))
    act = state[P].action if isinstance(state[P].action, dict) else {}
    for o in (act.get('market') or []):
        if isinstance(o, list) and len(o) >= 3 and o[0] == 'BUY_SEED':
            SEEDS[(st // 24, o[1])] += int(o[2])
    return opm(state, env)
K._process_market = pm
row = pinned4.job((path, idx, team, cand, S))
K._process_market = opm
print('\n'.join(OUT))
print('result us %s them %s m %s' % (row.get('us'), row.get('them'), row.get('m')))
print('seed orders by day (us):', sorted(SEEDS.items()))
print('led_us  ', row.get('led_us')); print('led_them', row.get('led_them'))
