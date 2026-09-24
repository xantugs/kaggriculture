"""Per-product flow from day D0 for seat 0 vs a fixed opponent, averaged over seeds (16 procs):
harvested, sold, avg price, revenue, night overflow, and costs. usage: flowagg.py agent.py seeds(a-b) [D0] [opp]"""
import sys, os, collections, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
from concurrent.futures import ProcessPoolExecutor
D1 = int(os.environ.get('D1', '31'))


def job(t):
    path, seed, D0, opp = t
    import lean, decouple
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    decouple.install(0)
    A = lean.load(path); B = lean.load(opp)
    ops = collections.Counter(); harv = collections.Counter(); sold = collections.Counter(); rev = collections.Counter(); cost = collections.Counter(); lost = collections.Counter()
    F = [None]; S = [0]; PV = [None]
    oa, oc, opm, oh, odrop = K._apply_unit_action, K._commit_unit, K._process_market, K._do_hire, K._drop_inventories_to_shed
    def hook(farm, private, actor, command, *a, **k):
        if farm is F[0] and command and D0 * 24 <= S[0] < D1 * 24:
            ops[command[0]] += 1
        if farm is F[0] and command and command[0] in ('HARVEST', 'COLLECT_FERTILIZER') and D0 * 24 <= S[0] < D1 * 24:
            before = dict(private['inventories'][actor]); r = oa(farm, private, actor, command, *a, **k)
            for it, q in private['inventories'][actor].items(): harv[it] += max(0, q - before.get(it, 0))
            return r
        return oa(farm, private, actor, command, *a, **k)
    def commit(op, item, price, farm, private, market, cap=100):
        ok = oc(op, item, price, farm, private, market, cap)
        if ok and farm is F[0] and D0 * 24 <= S[0] < D1 * 24:
            if op == 'SELL': sold[item] += 1; rev[item] += price
            else: cost[op + ':' + item] += price; cost['n_' + op + ':' + item] += 1
        return ok
    def hire(farm, private, bs, mult=1):
        m0 = farm['money']; oh(farm, private, bs, mult)
        if farm is F[0] and D0 * 24 <= S[0] < D1 * 24: cost['HIRE'] += m0 - farm['money']
    def drop(private, cap):
        if private is PV[0] and S[0] >= D0 * 24:
            before = collections.Counter(private['shed'])
            for inv in private['inventories']: before.update(inv)
            odrop(private, cap); after = collections.Counter(private['shed'])
            for it in before:
                if before[it] > after[it]: lost[it] += before[it] - after[it]
            return
        return odrop(private, cap)
    def pm(state, env):
        F[0] = state[0].observation.farms[0]; S[0] = state[0].observation.step; PV[0] = state[0].observation.private
        return opm(state, env)
    K._apply_unit_action, K._commit_unit, K._process_market, K._do_hire, K._drop_inventories_to_shed = hook, commit, pm, hire, drop
    r = lean.play(None, None, seed, agent_objs=[A, B])
    return dict(r=r['r'], ops=ops, harv=harv, sold=sold, rev=rev, cost=cost, lost=lost)


if __name__ == '__main__':
    path = sys.argv[1]; a, b = map(int, sys.argv[2].split('-')); D0 = int(sys.argv[3]) if len(sys.argv) > 3 else 15
    opp = sys.argv[4] if len(sys.argv) > 4 else os.path.join(HERE, '..', 'arena', 'cand', 'omw_v15b.py')
    tot = {k: collections.Counter() for k in ('harv', 'sold', 'rev', 'cost', 'lost', 'ops')}; n = 0; us = them = 0
    with ProcessPoolExecutor(16) as ex:
        for res in ex.map(job, [(path, s, D0, opp) for s in range(a, b + 1)]):
            n += 1; us += res['r'][0]; them += res['r'][1]
            for k in tot: tot[k].update(res[k])
    print(f"{os.path.basename(path)}: n {n} us {us / n:.0f} them {them / n:.0f}")
    for it in sorted(set(tot['harv']) | set(tot['sold'])):
        if it in ('COW', 'GOOSE', 'SHEEP'): continue
        s = tot['sold'][it]
        print(f"  {it:11s} harv {tot['harv'][it] / n:6.1f} sold {s / n:6.1f} @ {tot['rev'][it] / max(1, s):6.1f} rev {tot['rev'][it] / n:8.0f}  lost {tot['lost'][it] / n:5.1f}")
    print('  costs/game:', {k: round(v / n) for k, v in sorted(tot['cost'].items(), key=lambda kv: -kv[1])[:9] if not k.startswith('n_')})
    for k in ('BUY_PRODUCT:WHEAT', 'BUY_PRODUCT:FERTILIZER'):
        u = tot['cost'].get('n_' + k, 0)
        if u: print(f"  {k}: {u / n:.0f} units/game @ {tot['cost'][k] / u:.1f}")
    print('  ops/game:', {k: round(v / n) for k, v in sorted(tot['ops'].items(), key=lambda kv: -kv[1])})
