"""Early-game scan of recorded games: per day 0-8, our money, hires, animals (placed) vs the rival; flags animal escapes.
usage: early_scan.py games.json out.jsonl [team]"""
import sys, os, json, collections
sys.argv = [sys.argv[0]] + [os.path.abspath(a) if a.endswith(('.json', '.jsonl')) else a for a in sys.argv[1:]]
HERE = '/home/user/kaggriculture/moon'
sys.path.insert(0, os.path.join(HERE, '..', 'arena')); sys.path.insert(0, '/home/user/kaggriculture/gold/harness')
os.chdir(HERE)
import lean
from kaggle_environments.envs.kaggriculture import kaggriculture as K
from pinned4 import _tape
games = json.load(open(sys.argv[1])); out = open(sys.argv[2], 'w'); team = sys.argv[3] if len(sys.argv) > 3 else 'offhand'
for d in games:
    P = d['info']['TeamNames'].index(team); O = 1 - P
    ESC = collections.Counter(); SN = {}; F = [None, None]; ST = [0]
    orig = K._daily_refresh_animals
    def dra(farm, day):
        before = {(x, y): t.get('animal') for y, row in enumerate(farm['tiles']) for x, t in enumerate(row) if isinstance(t, dict) and t.get('animal')}
        orig(farm, day)
        after = {(x, y) for y, row in enumerate(farm['tiles']) for x, t in enumerate(row) if isinstance(t, dict) and t.get('animal')}
        i = 0 if farm is F[P] else 1
        for k, an in before.items():
            if k not in after:
                ESC[(i, day, an)] += 1
    opm = K._process_market
    def pm(state, env):
        F[0], F[1] = state[0].observation.farms[0], state[0].observation.farms[1]
        st = state[0].observation.step
        if st % 24 == 0:
            SN[st // 24] = [(round(state[0].observation.farms[i]['money']), sum(1 for row in state[0].observation.farms[i]['tiles'] for t in row if isinstance(t, dict) and t.get('animal'))) for i in (P, O)]
        return opm(state, env)
    K._daily_refresh_animals, K._process_market = dra, pm
    try:
        r = lean.play(None, None, d['info']['seed'], agent_objs=[_tape(d['acts'], 0), _tape(d['acts'], 1)], max_steps=24 * 12)
    finally:
        K._daily_refresh_animals, K._process_market = orig, opm
    esc = [[('us' if i == 0 else 'them'), day, an, n] for (i, day, an), n in sorted(ESC.items())]
    out.write(json.dumps(dict(id=d['id'], opp=d['info']['TeamNames'][O], rewards=d['rewards'], P=P, esc=esc, snaps=SN)) + '\n'); out.flush()
    if any(e[0] == 'us' for e in esc):
        print(d['id'], d['info']['TeamNames'][O], 'ESCAPES', esc, 'money/animals', {k: v for k, v in SN.items() if k <= 4}, flush=True)
print('done')
