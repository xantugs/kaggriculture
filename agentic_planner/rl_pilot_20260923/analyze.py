"""Paired, seed-clustered analysis of the untouched pilot test."""
from pathlib import Path
import json
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
slug = sys.argv[1] if len(sys.argv)>1 else 'kaggriculture-codex-rl-pilot-0923'
folder = HERE/'outputs'/slug
evaluations = json.loads((folder/'evaluations.json').read_text())
initial = next(e for e in evaluations if e['label']=='test_initial')
selected = next(e for e in evaluations if e['label']=='test_selected')
old = {(r['seed'],r['seat'],r['start']):r for r in initial['rows']}
assert len(old)==len(initial['rows'])
results=[]
for start in sorted({r['start'] for r in selected['rows']}):
    rows=[r for r in selected['rows'] if r['start']==start]
    seeds=sorted({r['seed'] for r in rows})
    assert all(sum(r['seed']==s for r in rows)==2 for s in seeds)
    delta=np.asarray([np.mean([r['delta'] for r in rows if r['seed']==s]) for s in seeds])
    improvement=np.asarray([np.mean([r['policy_margin']-old[(s,r['seat'],start)]['policy_margin'] for r in rows if r['seed']==s]) for s in seeds])
    rng=np.random.default_rng(20260923)
    indexes=rng.integers(len(seeds),size=(10000,len(seeds)))
    ci=np.quantile(delta[indexes].mean(1),[.025,.975]).tolist()
    ici=np.quantile(improvement[indexes].mean(1),[.025,.975]).tolist()
    results.append(dict(start=start,independent_seeds=len(seeds),games=len(rows),
        wins=sum(r['policy_margin']>0 for r in rows),draws=sum(r['policy_margin']==0 for r in rows),
        mean_delta_vs_incumbent=float(delta.mean()),seed_bootstrap_95pct=ci,
        mean_improvement_vs_initial=float(improvement.mean()),improvement_seed_bootstrap_95pct=ici,
        worst_margin=min(r['policy_margin'] for r in rows)))
out=dict(results=results,uncertainty='Percentile bootstrap resamples whole seeds, keeping both seats together. Small pilot, not leaderboard evidence.')
(folder/'analysis.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
