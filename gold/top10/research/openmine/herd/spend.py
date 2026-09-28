"""Day-by-day spend/income composition for days 0-9 per team (mean $ per seat), streamed from elite_days / ours_T7_days
(needs buy_seed by crop which compact.jsonl drops)."""
import json, os, collections
from lib import HERE, SHORT
OM = os.path.dirname(HERE)
acc = collections.defaultdict(lambda: collections.defaultdict(float))
cnt = collections.Counter()
for fn, role in (('elite_days.jsonl', 'rec'), ('ours_T7_days.jsonl', 'ours')):
    with open(os.path.join(OM, fn), encoding='utf-8') as f:
        for l in f:
            r = json.loads(l)
            if r['d'] > 9:
                continue
            if role == 'rec' and r['date'] < '2026-09-23':
                continue
            t = SHORT[r['team']] if role == 'rec' else 'T7'
            if r['d'] == 0:
                cnt[t] += 1
            A = acc[(t, r['d'])]
            for k, (n, usd) in r['buy_animal'].items():
                A['an'] += usd
            for k, (n, usd) in r['buy_seed'].items():
                A['sd:' + k] += usd
            for k, (n, usd) in r['buy_prod'].items():
                A['bp:' + k] += usd
            for k, (n, usd) in r['sell'].items():
                A['s:' + k] += usd
            A['wage'] += r['wage']
            A['land'] += sum(x['price'] for x in r['land'])
            A['m0'] += r['m0']
            A['mend'] += r['mend']
for t in ['Boey', 'FQ', 'CBF', 'Yiz', 'TFC', 'T7']:
    n = cnt[t]
    print('=====', t, n)
    for d in range(10):
        A = acc[(t, d)]
        seeds = ' '.join('%s %d' % (k[3:6], v / n) for k, v in sorted(A.items()) if k.startswith('sd:') and v / n >= 5)
        sells = ' '.join('%s %d' % (k[2:6], v / n) for k, v in sorted(A.items()) if k.startswith('s:') and v / n >= 5)
        bps = ' '.join('%s %d' % (k[3:7], v / n) for k, v in sorted(A.items()) if k.startswith('bp:') and v / n >= 5)
        print(' d%d m0 %5.0f | animals %5.0f seeds[%s] bp[%s] wage %3.0f land %4.0f | sells[%s] | mend %5.0f' % (
            d, A['m0'] / n, A['an'] / n, seeds, bps, A['wage'] / n, A['land'] / n, sells, A['mend'] / n))
