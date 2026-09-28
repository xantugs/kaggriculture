"""Cash lead vs stock-adjusted lead at the end of day 28 (held + ripe-on-tile units valued at the day-28 closing quote,
scaled by a price-impact factor), and how each predicts the final result. usage: stock_lead.py daylog.jsonl [...]"""
import sys, json, statistics as st
rows = [json.loads(l) for p in sys.argv[1:] for l in open(p, encoding='utf-8')]
rows = [x for x in rows if x['m'] is not None and len(x['days_us']) >= 29 and x['days_us'][28].get('px')]
def stock(x, who, f):
    D = x['days_' + who][28]; px = x['days_us'][28]['px']
    v = 0.0
    for src in ('held', 'ripe_post'):
        for k, u in (D.get(src) or {}).items():
            p = px.get(k) or px.get({'COW': 'MILK', 'SHEEP': 'WOOL', 'GOOSE': 'EGG'}.get(k, ''), 0)
            v += u * p * f
    return v
for f in (0.0, 0.6, 0.8):
    ok = 0; led_lost = 0; tr_won = 0; err = []
    for x in rows:
        lead = x['days_us'][28]['money'] - x['days_elite'][28]['money'] + stock(x, 'us', f) - stock(x, 'elite', f)
        ok += (lead > 0) == (x['m'] > 0)
        led_lost += lead > 0 and x['m'] < 0; tr_won += lead < 0 and x['m'] > 0
        err.append(x['m'] - lead)
    print(f"stock factor {f}: sign agrees {ok}/{len(rows)}  led&lost {led_lost}  trailed&won {tr_won}  final - projected: mean {st.mean(err):+.0f} sd {st.pstdev(err):.0f}")
