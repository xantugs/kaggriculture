from pathlib import Path
import json
import statistics

HERE=Path(__file__).resolve().parent
rows=[]
for path in HERE.glob('hybrid_local_*.json'):
    rows.extend(json.loads(path.read_text()))
assert len(rows)==256,len(rows)
by={(r['seed'],r['seat'],r['start'],r['mode']):r for r in rows}
summary=[]
for start in (672,696):
    for mode in ('incumbent','learned_all','learned_units','learned_market'):
        deltas=[];wins=0
        for seed in range(860000001,860000017):
            for seat in (0,1):
                r=by[seed,seat,start,mode];b=by[seed,seat,start,'incumbent']
                margin=r['reward'][seat]-r['reward'][1-seat]
                baseline=b['reward'][seat]-b['reward'][1-seat]
                deltas.append(margin-baseline);wins+=margin>0
        summary.append(dict(start=start,mode=mode,n=len(deltas),wins=wins,
            mean_delta=statistics.mean(deltas),median_delta=statistics.median(deltas),
            min_delta=min(deltas),max_delta=max(deltas)))
out=dict(summary=summary,rows=rows)
(HERE/'hybrid_results.json').write_text(json.dumps(out,indent=2))
print(json.dumps(summary,indent=2))
