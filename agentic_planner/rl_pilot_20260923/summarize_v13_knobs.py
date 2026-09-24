"""Combine fresh closed-loop chunks and report paired improvements over base."""
from pathlib import Path
import json
import math
import statistics

HERE=Path(__file__).resolve().parent
paths=sorted(HERE.glob('v13_fresh_closed_loop_[0-9].json'))
rows=[row for path in paths for row in json.loads(path.read_text())]
by_key={(r['seed'],r['seat'],r['label']):r for r in rows}
labels=sorted({r['label'] for r in rows})

def stats(values):
    n=len(values)
    mean=statistics.mean(values)
    sd=statistics.stdev(values) if n>1 else 0.0
    return {'n':n,'mean':mean,'median':statistics.median(values),
            'se':sd/math.sqrt(n) if n else 0.0,'min':min(values),'max':max(values)}

report=[]
for label in labels:
    xs=[r for r in rows if r['label']==label]
    margins=[r['margin'] for r in xs]
    deltas=[]
    flips_up=flips_down=0
    for r in xs:
        base=by_key[(r['seed'],r['seat'],'base')]
        d=r['margin']-base['margin']
        deltas.append(d)
        flips_up += base['margin']<=0 and r['margin']>0
        flips_down += base['margin']>0 and r['margin']<=0
    report.append({'label':label,'margin':stats(margins),'paired_delta':stats(deltas),
                   'wins':sum(x>0 for x in margins),'draws':sum(x==0 for x in margins),
                   'win_flips_up':flips_up,'win_flips_down':flips_down})

out={'files':[p.name for p in paths],'rows':len(rows),'report':report}
(HERE/'v13_fresh_closed_loop_summary.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
