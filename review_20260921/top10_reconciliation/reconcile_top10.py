"""Per-game reconciliation of top-10 agents vs their opponents (from econ_top1.jsonl, produced by econ.py replaying
kgdigest_top1.json.gz exactly with kaggle-environments 1.32.7). Every line is (top agent - opponent); costs are
entered with a minus sign, so the lines of each game sum exactly to its final-cash margin."""
import json, statistics as st
TOP10 = ["DSM","Majkel1337","THIRD FARM CLUB","Vadim Vasilenko","ymg_aq","Unknown Mother-Goose","SpaTaro","Otter Vibe","KawattaTaido","Kaggledew Valley 🏆"]
items = ["WHEAT","CARROT","TOMATO","STRAWBERRY","MELON","EGG","MILK","WOOL","FERTILIZER"]
recs = []
for r in (json.loads(l) for l in open('econ_top1.jsonl')):
    ts = [i for i, nm in enumerate(r['names']) if nm in TOP10]
    if len(ts) != 1 or not r['ok']: continue
    t, o = ts[0], 1 - ts[0]
    rec = {'id': r['id'], 'top': r['names'][t], 'margin': r['rewards'][t] - r['rewards'][o],
           'opp_wheat_bought': r['buys'][o].get('BUY_PRODUCT:WHEAT', [0, 0])[1]}
    for it in items: rec['rev_' + it] = r['sales'][t].get(it, [0, 0])[1] - r['sales'][o].get(it, [0, 0])[1]
    for p, sign in ((t, -1), (o, 1)):
        for k, v in r['buys'][p].items(): rec['cost_' + k] = rec.get('cost_' + k, 0) + sign * v[1]
        rec['cost_HIRE'] = rec.get('cost_HIRE', 0) + sign * r['hires'][p][1]
        rec['cost_LAND'] = rec.get('cost_LAND', 0) + sign * r['land'][p][1]
    lines = sum(v for k, v in rec.items() if k.startswith(('rev_', 'cost_')))
    assert abs(lines - rec['margin']) <= 1, (rec['id'], lines, rec['margin'])
    recs.append(rec)
clean = [x for x in recs if x['opp_wheat_bought'] <= 30000]
keys = sorted({k for x in clean for k in x if k.startswith(('rev_', 'cost_'))})
print(f"games {len(recs)}, excluding {len(recs) - len(clean)} opponents with >$30k wheat round-trips -> n={len(clean)}")
print(f"mean margin {st.mean(x['margin'] for x in clean):.0f}, median {st.median(x['margin'] for x in clean):.0f}")
means = {k: st.mean(x.get(k, 0) for x in clean) for k in keys}
for k in sorted(keys, key=lambda k: -abs(means[k])): print(f"  {k:32s} {means[k]:8.0f}")
print(f"  {'sum of lines (= mean margin)':32s} {sum(means.values()):8.0f}")
