"""Units harvested / sold (and avg price) / lost to shed overflow / left in shed at end, per product, seat 0."""
import sys, collections, copy; import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'arena'))
import lean, decouple
from kaggle_environments.envs.kaggriculture import kaggriculture as K
decouple.install(0)
A = lean.load(sys.argv[1]); B = lean.load('../arena/cand/omw_v15b.py'); seed = int(sys.argv[2]); D0 = int(sys.argv[3]) if len(sys.argv) > 3 else 15
harv = collections.Counter(); cost = collections.Counter(); sold = collections.Counter(); rev = collections.Counter(); FARM0 = [None]; STEP = [0]; PRIV0 = [None]
oa, oc, opm, oeod = K._apply_unit_action, K._commit_unit, K._process_market, K._end_of_day
def hook(farm, private, actor, command, *a, **k):
    if farm is FARM0[0] and command and command[0] in ('HARVEST', 'COLLECT_FERTILIZER') and STEP[0] >= D0 * 24:
        before = dict(private['inventories'][actor]); r = oa(farm, private, actor, command, *a, **k)
        for it, q in private['inventories'][actor].items(): harv[it] += max(0, q - before.get(it, 0))
        return r
    return oa(farm, private, actor, command, *a, **k)
def commit(op, item, price, farm, private, market, cap=100):
    ok = oc(op, item, price, farm, private, market, cap)
    if ok and op == 'SELL' and farm is FARM0[0] and STEP[0] >= D0 * 24: sold[item] += 1; rev[item] += price
    elif ok and farm is FARM0[0] and STEP[0] >= D0 * 24: cost[op + ':' + str(item)] += price
    return ok
def pm(state, env):
    FARM0[0] = state[0].observation.farms[0]; STEP[0] = state[0].observation.step; PRIV0[0] = state[0].observation.private
    return opm(state, env)
oh = K._do_hire
def hire(farm, private, bs, mult=1):
    m0 = farm['money']; oh(farm, private, bs, mult)
    if farm is FARM0[0] and STEP[0] >= D0 * 24: cost['HIRE'] += m0 - farm['money']
K._do_hire = hire
odrop = K._drop_inventories_to_shed
lost = collections.Counter(); lostday = collections.Counter()
def drop(private, cap):
    if private is PRIV0[0] and STEP[0] >= D0 * 24:
        before = collections.Counter(private['shed'])
        for inv in private['inventories']:
            before.update(inv)
        odrop(private, cap)
        after = collections.Counter(private['shed'])
        for it in before:
            if before[it] > after[it]: lost[it] += before[it] - after[it]; lostday[STEP[0] // 24] += before[it] - after[it]
        return
    return odrop(private, cap)
K._drop_inventories_to_shed = drop
K._apply_unit_action, K._commit_unit, K._process_market = hook, commit, pm
r = lean.play(None, None, seed, agent_objs=[A, B])
print(r['r'])
for it in sorted(set(harv) | set(sold)):
    print(f"  {it:11s} harvested {harv[it]:4d}  sold {sold[it]:4d} @ {rev[it] / max(1, sold[it]):6.1f}  revenue {rev[it]:7d}")
print('  revenue', sum(rev.values()), ' costs', {k: v for k, v in sorted(cost.items(), key=lambda kv: -kv[1])[:8]}, 'total cost', sum(cost.values()))
print('  lost to shed overflow at night:', dict(lost))
print('  lost by day:', dict(lostday))
