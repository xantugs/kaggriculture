"""Stream the openmine day files and keep the detail rows (d<=16) with the labour-relevant fields -> labour/rows.pkl
usage (from kg/): ../.venv/Scripts/python.exe gold/top10/research/openmine/labour/compact.py"""
import json, os, pickle
HERE = os.path.dirname(os.path.abspath(__file__)); OM = os.path.dirname(HERE)
KEEP = ('gid', 'date', 'seat', 'team', 'opp', 'role', 'd', 'm0', 'm23', 'mend', 'mmin', 'mmin_h', 'hires', 'wage', 'hire_h',
        'hands', 'hands_h', 'ops', 'fail', 'move', 'pas', 'noact', 'herd', 'crops', 'units', 'struct', 'weeds', 'free',
        'quads', 'shops', 'shed', 'seeds', 'sell', 'buy_prod', 'buy_seed', 'buy_animal', 'land', 'hv', 'q', 'fills', 'riv')
out = {}
for fn, tag in (('elite_days.jsonl', 'rec'), ('ours_T7_days.jsonl', 'ours'), ('ours_T7_opp_days.jsonl', 'rep')):
    rows = []
    with open(os.path.join(OM, fn), encoding='utf-8') as fh:
        for line in fh:
            r = json.loads(line)
            if r['d'] > 16: continue
            rows.append({k: r.get(k) for k in KEEP})
    out[tag] = rows
    print(fn, len(rows), flush=True)
with open(os.path.join(HERE, 'rows.pkl'), 'wb') as fh:
    pickle.dump(out, fh)
