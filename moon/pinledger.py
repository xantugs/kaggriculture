"""Money flows of a pinned candidate vs the recorded rival, split by rival class, plus the day the gap opens.
Each game is replayed pinned from S (as pinmulti) with ledger hooks on sales, purchases, hires and land.
usage: pinledger.py cand S out.json [GLIST=g2800_list.json GCLASS=gameclass.json]
prints, per class (MIR sim>=0.8 / DIV), mean per game: income per product (units), spend per kind, and
end-of-day money difference them-us on selected days; out.json keeps the per-game ledgers."""
import sys, os, json, collections
from concurrent.futures import ProcessPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))


def job(t):
    import lean, pinned
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    fn, path, S, team = t
    d = json.load(open(fn, encoding='utf-8'))[0]
    names = d['info']['TeamNames']; P = names.index(team); O = 1 - P
    spawns, shops, _ = pinned.reference(d)
    led = [collections.Counter(), collections.Counter()]; units = [collections.Counter(), collections.Counter()]
    money = [[], []]; F = [None, None]
    oc, opm, ohire, oland = K._commit_unit, K._process_market, K._do_hire, K._do_buy_land
    orig = pinned.install_pinned(S // 24, O, spawns, shops)
    oeod = K._end_of_day

    def who(farm):
        return 0 if farm is F[P] else 1

    def commit(op, it, price, farm, private, market, cap=100):
        ok = oc(op, it, price, farm, private, market, cap)
        if ok:
            w = who(farm)
            if op == 'SELL': led[w][it] += price; units[w][it] += 1
            elif op == 'BUY_PRODUCT': led[w]['buy_' + it] -= price
            elif op == 'BUY_SEED': led[w]['seed'] -= price
            elif op == 'BUY_ANIMAL': led[w]['anim_' + it] -= price; units[w]['anim_' + it] += 1
        return ok

    def hire(farm, private, bs, mult=1):
        m0 = farm['money']; r = ohire(farm, private, bs, mult); led[who(farm)]['hire'] += farm['money'] - m0; return r

    def land(farm, bs):
        m0 = farm['money']; r = oland(farm, bs); led[who(farm)]['land'] += farm['money'] - m0; return r

    def pm(state, env):
        F[0], F[1] = state[0].observation.farms[0], state[0].observation.farms[1]
        return opm(state, env)

    def eod(state, env, day):
        fs = state[0].observation.farms
        money[0].append(fs[P]['money']); money[1].append(fs[O]['money'])
        return oeod(state, env, day)
    K._commit_unit, K._process_market, K._do_hire, K._do_buy_land, K._end_of_day = commit, pm, hire, land, eod
    try:
        A = lean.load(path)
        ag = [None, None]
        ag[P] = pinned._prefixed(A, d['acts'], P, S)
        ag[O] = pinned._tape(d['acts'], O)
        r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
    finally:
        K._commit_unit, K._process_market, K._do_hire, K._do_buy_land, K._end_of_day = oc, opm, ohire, oland, orig
    return dict(gid=str(d['id']), opp=names[O], us=r['r'][P], them=r['r'][O], led=[dict(x) for x in led],
                units=[dict(x) for x in units], money=money)


if __name__ == '__main__':
    cand, S, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    path = cand if cand.endswith('.py') else os.path.join(HERE, '..', 'arena', 'cand', cand + '.py')
    files = json.load(open(os.path.join(HERE, os.environ.get('GLIST', 'g2800_list.json'))))
    cls = {str(k): v for k, v in json.load(open(os.path.join(HERE, os.environ.get('GCLASS', 'gameclass.json')))).items()}
    with ProcessPoolExecutor(int(os.environ.get('PIN_WORKERS', '16'))) as ex:
        rs = list(ex.map(job, [(f, path, S, 'offhand') for f in files]))
    json.dump(rs, open(out, 'w', encoding='utf-8'), ensure_ascii=False)
    for grp in ('MIR', 'DIV'):
        g = [r for r in rs if (cls.get(r['gid'], 0) >= 0.8) == (grp == 'MIR') and r['us'] is not None]
        if not g: continue
        n = len(g); w = sum(r['us'] > r['them'] for r in g)
        print(f'== {grp} games {n}  wins {w}  us {sum(r["us"] for r in g)/n:.0f}  them {sum(r["them"] for r in g)/n:.0f}')
        L = [collections.Counter(), collections.Counter()]; U = [collections.Counter(), collections.Counter()]
        for r in g:
            for s in (0, 1): L[s].update(r['led'][s]); U[s].update(r['units'][s])
        for k in sorted(set(L[0]) | set(L[1]), key=lambda k: -abs(L[1][k] - L[0][k])):
            if abs(L[1][k] - L[0][k]) / n < 150: continue
            print(f'  {k:18s} us {L[0][k]/n:8.0f} ({U[0][k]/n:6.1f})   them {L[1][k]/n:8.0f} ({U[1][k]/n:6.1f})   them-us {(L[1][k]-L[0][k])/n:+7.0f}')
        days = [4, 8, 12, 16, 20, 24, 26, 28, 29]
        print('  money them-us by day: ' + '  '.join(
            f'd{dd} {sum(r["money"][1][dd] - r["money"][0][dd] for r in g if len(r["money"][0]) > dd)/n:+.0f}' for dd in days))
