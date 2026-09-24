"""How do the teachers issue commands? Pickup quantities, PLACE usage, market order structure, sale sizes vs stock at
market time (after that turn's unit actions). usage: teacher_conv.py games.jsonl "DSM|Vadim Vasilenko" [max_games]"""
import sys, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
import lean
from kaggle_environments.envs.kaggriculture import kaggriculture as K

src, teams = sys.argv[1], sys.argv[2].split('|')
maxg = int(sys.argv[3]) if len(sys.argv) > 3 else 20
C = collections.Counter(); pick = collections.Counter(); place = collections.Counter(); seq = collections.Counter()
sell_frac = collections.Counter(); sell_n = collections.Counter(); buy_n = collections.Counter(); nord = collections.Counter()
sell_after_buy = 0; turns = 0; games = 0
for line in open(src, encoding='utf-8'):
    d = json.loads(line)
    names = d['info']['TeamNames']
    seats = [i for i, n in enumerate(names) if n in teams]
    if not seats:
        continue
    games += 1
    if games > maxg:
        break
    acts = d['acts']
    SH = {}
    opm = K._process_market
    def pm(state, env):
        s = state[0].observation.step
        for p in seats:
            SH[(p, s)] = dict(state[p].observation.private['shed'])
        return opm(state, env)
    K._process_market = pm
    INV = {}
    def tape(p):
        def f(obs, cfg=None):
            t = obs['step']
            INV[(p, t)] = [dict(x) for x in (obs['private'].get('inventories') or [])]
            a = acts[t + 1][p] if t + 1 < len(acts) else None
            return a if isinstance(a, dict) else {"farmer": ["PASS"], "hands": [], "market": []}
        return f
    try:
        lean.play(None, None, d['info']['seed'], agent_objs=[tape(0), tape(1)])
    finally:
        K._process_market = opm
    for p in seats:
        for t in range(719):
            a = acts[t + 1][p] if t + 1 < len(acts) else None
            if not isinstance(a, dict):
                continue
            turns += 1
            cmds = [a.get('farmer')] + list(a.get('hands') or [])
            invs = INV.get((p, t), [])
            for k, c in enumerate(cmds):
                if not isinstance(c, list) or not c:
                    continue
                if c[0] == 'PICKUP':
                    pick[(c[1], int(c[2]) if len(c) > 2 else 1)] += 1
                if c[0] == 'PLACE' and len(c) > 1 and c[1] not in ('GOOSE', 'COW', 'SHEEP'):
                    inv = invs[k] if k < len(invs) else {}
                    carried = int(inv.get(c[1], 0)); q = int(c[2]) if len(c) > 2 else 1
                    place[(c[1], 'all' if q >= carried else ('partial' if q > 0 else 'zero'), len([v for v in inv.values() if v]) > 1)] += 1
            orders = [o for o in (a.get('market') or []) if o]
            nord[len(orders)] += 1
            kinds = []
            for o in orders:
                kd = o[0] if o[0] != 'BUY_PRODUCT' else 'BUY_' + o[1]
                if not kinds or kinds[-1] != kd:
                    kinds.append(kd)
            seq[tuple(kinds)] += 1
            if 'SELL' in kinds and any(k.startswith('BUY') or k == 'HIRE' for k in kinds[:kinds.index('SELL')]):
                sell_after_buy += 1
            shed = SH.get((p, t), {})
            for o in orders:
                if o[0] == 'SELL':
                    have = int(shed.get(o[1], 0)); n = int(o[2])
                    sell_n[(o[1], min(n, 60))] += 1
                    sell_frac['all' if have and n >= have else ('none_avail' if not have else 'part')] += 1
                if o[0] == 'BUY_PRODUCT':
                    buy_n[(o[1], min(int(o[2]), 60))] += 1
print('games', min(games, maxg), 'teacher turns', turns)
print('orders per turn', sorted(nord.items()))
print('top order sequences', seq.most_common(15))
print('turns where a SELL comes after a buy/hire', sell_after_buy)
print('sell size vs stock at market time', dict(sell_frac))
print('pickup quantities (item, n) top', pick.most_common(25))
print('PLACE deposits (item, all/partial, bag had other items)', place.most_common(15))
print('buy quantities top', buy_n.most_common(15))
print('sell quantities top', sell_n.most_common(20))
