"""Summarize recorded elite-game economics and production timing; no policy changes."""
import ast
import collections
import gzip
import json
from pathlib import Path
import statistics as st

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'review_20260921/top10_reconciliation'
tree = ast.parse((DATA / 'reconcile_top10.py').read_text(encoding='utf-8'))
TOP = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
           and any(isinstance(t, ast.Name) and t.id == 'TOP10' for t in n.targets))
records = [json.loads(l) for l in (DATA / 'econ_top1.jsonl').read_text(encoding='utf-8').splitlines()]
digests = {r['id']: r for r in json.loads(gzip.decompress((ROOT / 'replays/kgdigest_top1.json.gz').read_bytes()))}
goods = ('WHEAT','CARROT','TOMATO','STRAWBERRY','MELON','EGG','MILK','WOOL','FERTILIZER')
rows = []
for r in records:
    seats = [i for i, n in enumerate(r['names']) if n in TOP]
    if len(seats) != 1 or not r['ok']: continue
    t, o = seats[0], 1-seats[0]
    lines = {}
    for g in goods:
        lines['revenue_'+g] = r['sales'][t].get(g,[0,0])[1] - r['sales'][o].get(g,[0,0])[1]
    for k in set(r['buys'][0]) | set(r['buys'][1]):
        lines['cost_'+k] = r['buys'][o].get(k,[0,0])[1] - r['buys'][t].get(k,[0,0])[1]
    for key in ('hires','land'):
        lines['cost_'+key] = r[key][o][1] - r[key][t][1]
    margin = r['rewards'][t] - r['rewards'][o]
    assert abs(sum(lines.values())-margin) <= 1
    d = digests[r['id']]
    commands = [collections.Counter(), collections.Counter()]
    tomato_plant_days = collections.Counter()
    for k, step in enumerate(d['acts'][1:]):
        for p in (0,1):
            a = step[p] or {}
            for act in [a.get('farmer'), *a.get('hands',[])]:
                if not act: continue
                op = act[0]
                commands[p]['MOVE' if op in ('NORTH','SOUTH','EAST','WEST') else op] += 1
                if p == t and act[:2] == ['PLANT','TOMATO']: tomato_plant_days[k//24] += 1
    rows.append({'id':r['id'],'top':r['names'][t],'opponent':r['names'][o], 'margin':margin,
                 'clean':r['buys'][o].get('BUY_PRODUCT:WHEAT',[0,0])[1] <= 30000,
                 'lines':lines,'tomato_plant_request_days':dict(tomato_plant_days),
                 'sales':[r['sales'][p] for p in (t,o)],'buys':[r['buys'][p] for p in (t,o)],
                 'commands':[dict(commands[p]) for p in (t,o)],
                 'hires':[r['hires'][p] for p in (t,o)], 'land':[r['land'][p] for p in (t,o)],
                 'comp':{day:[v[p] for p in (t,o)] for day,v in r['comp'].items()}})

def summarize(rs):
    keys = sorted({k for r in rs for k in r['lines']})
    sales = {}
    for g in goods:
        sales[g] = [{
            'mean_units':round(st.mean(r['sales'][p].get(g,[0,0])[0] for r in rs),2),
            'mean_revenue':round(st.mean(r['sales'][p].get(g,[0,0])[1] for r in rs),2),
            'pooled_price':round(sum(r['sales'][p].get(g,[0,0])[1] for r in rs)/max(1,sum(r['sales'][p].get(g,[0,0])[0] for r in rs)),2)
        } for p in (0,1)]
    daily = {}
    for day in (0,3,6,9,12,15,18,21,24,27):
        daily[day] = [{g:round(st.mean(r['comp'][str(day)][p][0].get(g,0) for r in rs),2)
                       for g in ('TOMATO','STRAWBERRY','WHEAT','CARROT','MELON','COW','SHEEP','GOOSE')}
                      for p in (0,1)]
    return {'n':len(rs),'wins':sum(r['margin']>0 for r in rs),
            'mean_margin':round(st.mean(r['margin'] for r in rs),2),
            'median_margin':st.median(r['margin'] for r in rs),
            'mean_lines':{k:round(st.mean(r['lines'].get(k,0) for r in rs),2) for k in keys},
            'sales':sales,'daily_farms':daily,
            'mean_commands':{op:[round(st.mean(r['commands'][p].get(op,0) for r in rs),2) for p in (0,1)]
                             for op in ('MOVE','PASS','WATER','HARVEST','FEED','CARE','COLLECT_FERTILIZER','FERTILIZE','PLANT','DROP')},
            'mean_hires':[round(st.mean(r['hires'][p][0] for r in rs),2) for p in (0,1)],
            'mean_hire_cost':[round(st.mean(r['hires'][p][1] for r in rs),2) for p in (0,1)]}

clean = [r for r in rows if r['clean']]
plant_hist = collections.Counter()
for r in clean: plant_hist.update({int(k):v for k,v in r['tomato_plant_request_days'].items()})
result = {'all':summarize(rows),'excluding_large_wheat_buyers':summarize(clean),
          'tomato_plant_request_days_clean':dict(sorted(plant_hist.items())),
          'by_team':{name:{'n':len(rs),'mean_margin':round(st.mean(r['margin'] for r in rs),1),
                          'tomato_units':round(st.mean(r['sales'][0].get('TOMATO',[0,0])[0] for r in rs),1),
                          'plant_days':[r['tomato_plant_request_days'] for r in rs]}
                     for name in sorted({r['top'] for r in clean}) if (rs:=[r for r in clean if r['top']==name])},
          'games':rows}
out = Path(__file__).with_name('elite_structure.json')
out.write_text(json.dumps(result,indent=2),encoding='utf-8')
compact = dict(result)
compact.pop('games')
compact['all'] = {k:v for k,v in compact['all'].items() if k in ('n','wins','mean_margin','median_margin')}
print(json.dumps(compact,indent=2))
