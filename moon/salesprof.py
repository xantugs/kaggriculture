"""Selling behaviour of a team from exact replays: per premium product, share of units by hour, mean lot size,
realized price vs base, realized price vs the day's best quote, and timing relative to the opponent's sales
(same day: sold before / same step / after the opponent's first sale of that product).
usage: salesprof.py team max_games D0 D1 files..."""
import sys, os, json, collections, random
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
from concurrent.futures import ProcessPoolExecutor
ITEMS = ('STRAWBERRY', 'WOOL', 'MILK', 'EGG', 'TOMATO', 'CARROT', 'WHEAT', 'MELON', 'FERTILIZER')
BASE = {'WHEAT': 25, 'CARROT': 35, 'TOMATO': 60, 'STRAWBERRY': 120, 'MELON': 250, 'EGG': 50, 'MILK': 160, 'WOOL': 200, 'FERTILIZER': 100}


def job(d):
    import lean, pinned
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    team, D0, D1 = d['_team'], d['_D0'], d['_D1']
    n = d['info']['TeamNames']; P = n.index(team)
    F = [None, None]; S = [0]; sales = []; quotes = collections.defaultdict(list)
    oc, opm = K._commit_unit, K._process_market
    def commit(op, item, price, farm, private, market, cap=100):
        ok = oc(op, item, price, farm, private, market, cap)
        if ok and op == 'SELL' and D0 * 24 <= S[0] < (D1 + 1) * 24:
            who = 0 if farm is F[P] else 1
            sales.append((S[0], who, item, price))
        return ok
    def pm(state, env):
        F[0], F[1] = state[0].observation.farms[0], state[0].observation.farms[1]; S[0] = state[0].observation.step
        pr = state[0].observation.market['prices']
        if D0 * 24 <= S[0] < (D1 + 1) * 24:
            for it in ITEMS: quotes[(S[0] // 24, it)].append(pr[it])
        return opm(state, env)
    K._commit_unit, K._process_market = commit, pm
    try:
        r = lean.play(None, None, d['info']['seed'], agent_objs=[pinned._tape(d['acts'], 0), pinned._tape(d['acts'], 1)])
    finally:
        K._commit_unit, K._process_market = oc, opm
    if [int(x) for x in r['r']] != [int(x) for x in d['rewards']]:
        return None
    st = collections.Counter()
    first_opp = {}
    for s, who, it, p in sales:
        if who == 1: first_opp.setdefault((s // 24, it), s)
    lots = collections.Counter()
    for s, who, it, p in sales:
        if who != 0: continue
        day = s // 24; st['n_' + it] += 1; st['rev_' + it] += p; st['h%02d_' % (s % 24) + it] += 1
        lots[(s, it)] += 1
        best = max(quotes.get((day, it), [p])); st['best_' + it] += best
        fo = first_opp.get((day, it))
        rel = 'noopp' if fo is None else ('before' if s < fo else ('same' if s == fo else 'after'))
        st['rel_%s_%s' % (rel, it)] += 1
    for (s, it), q in lots.items():
        st['lots_' + it] += 1
    return dict(st)


if __name__ == '__main__':
    team, mx, D0, D1, files = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5:]
    gs = []
    for f in files:
        it = (json.loads(l) for l in open(f, encoding='utf-8')) if f.endswith('.jsonl') else json.load(open(f, encoding='utf-8'))
        for d in it:
            if team in (d['info'].get('TeamNames') or []):
                d['_team'] = team; d['_D0'] = D0; d['_D1'] = D1; gs.append(d)
    random.Random(1).shuffle(gs); gs = gs[:mx]
    tot = collections.Counter(); ng = 0
    with ProcessPoolExecutor(int(os.environ.get('WORKERS', '8'))) as ex:
        for r in ex.map(job, gs):
            if r: tot.update(r); ng += 1
    print(f"{team}: games {ng}, days {D0}-{D1}")
    for it in ITEMS:
        n = tot['n_' + it]
        if not n: continue
        hours = sorted(((tot['h%02d_' % h + it], h) for h in range(24)), reverse=True)[:4]
        rel = {k: round(tot['rel_%s_%s' % (k, it)] / n, 2) for k in ('before', 'same', 'after', 'noopp')}
        print(f"  {it:10s} units/game {n / ng:6.1f}  price {tot['rev_' + it] / n:6.1f} ({tot['rev_' + it] / n / BASE[it]:.2f}x base, "
              f"{tot['rev_' + it] / max(1, tot['best_' + it]):.2f} of day-best)  lot {n / max(1, tot['lots_' + it]):5.1f}  "
              f"top hours {[(h, round(c / n, 2)) for c, h in hours]}  vs-opp {rel}")
