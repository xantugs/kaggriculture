"""Elite tomato plantings per day from the recorded actions, by tomato demand known at the time.
usage: tom_elite.py gate (goldg|top10g) [out.json]"""
import sys, json, gzip, collections
g = sys.argv[1]
G = 'gold/top10/gates/'
refs = [json.loads(l) for l in open(G + g + '_refs.jsonl', encoding='utf-8')]
base = {(r['gid'], r['seat']): r for r in map(json.loads, open(G + g + '_sf8.jsonl', encoding='utf-8'))}
want = {r['gid'] for r in refs}
games = {}
with gzip.open(G + g + '_games.jsonl.gz', 'rt', encoding='utf-8') as f:
    for l in f:
        d = json.loads(l)
        if d['id'] in want:
            games[d['id']] = d['acts']
TS = ('PIZZA_SHOP', 'FARMERS_MARKET')
def tdem(shops, day):
    k = min(8, day // 3)
    return sum(6 for s in shops[:k] if s in TS)
out = []
for r in refs:
    acts = games[r['gid']]; s = r['seat']
    pl = collections.Counter(); seeds = collections.Counter(); sells = collections.Counter()
    for t in range(1, 720):
        a = acts[t][s] if acts[t] else None
        if not a: continue
        day = (t - 1) // 24
        for u in [a.get('farmer')] + (a.get('hands') or []):
            if u and u[0] == 'PLANT' and len(u) > 1 and u[1] == 'TOMATO': pl[day] += 1
        for o in a.get('market') or []:
            if isinstance(o, list) and len(o) >= 3 and o[1] == 'TOMATO':
                if o[0] == 'BUY_SEED': seeds[day] += int(o[2])
                elif o[0] == 'SELL': sells[day] += int(o[2])
    b = base.get((r['gid'], s), {})
    out.append(dict(gid=r['gid'], seat=s, team=r['team'], shops=r['shops'], pl={d: pl[d] for d in pl}, seeds=dict(seeds), sells=dict(sells),
                    dem12=tdem(r['shops'], 12), dem18=tdem(r['shops'], 18), dem24=tdem(r['shops'], 24), dem9=tdem(r['shops'], 9),
                    tom_el=(b.get('led_elite') or {}).get('TOMATO', 0), tom_us=(b.get('led_us') or {}).get('TOMATO', 0), m=b.get('m')))
if len(sys.argv) > 2:
    json.dump(out, open(sys.argv[2], 'w'))
n = len(out)
print(g, n, 'seats')
cum = lambda o, d: sum(v for k, v in o['pl'].items() if int(k) <= d)
print('mean elite tomato plantings per day:', ' '.join('%d:%.1f' % (d, sum(o['pl'].get(d, 0) for o in out) / n) for d in range(30) if sum(o['pl'].get(d, 0) for o in out)))
for key in ('dem9', 'dem12', 'dem18'):
    print('--- by', key)
    by = collections.defaultdict(list)
    for o in out: by[o[key]].append(o)
    for k in sorted(by):
        xs = by[k]; m = len(xs)
        print('  dem %2d n %3d  cum by d8 %.1f d12 %.1f d16 %.1f d18 %.1f d20 %.1f all %.1f | tomato $ elite %6.0f us %6.0f gap %+6.0f | m %+6.0f win %.0f%%' % (
            k, m, *[sum(cum(o, d) for o in xs) / m for d in (8, 12, 16, 18, 20, 29)],
            sum(o['tom_el'] for o in xs) / m, sum(o['tom_us'] for o in xs) / m, sum(o['tom_us'] - o['tom_el'] for o in xs) / m,
            sum(o['m'] or 0 for o in xs) / m, 100 * sum((o['m'] or 0) > 0 for o in xs) / m))
print('--- by team')
by = collections.defaultdict(list)
for o in out: by[o['team']].append(o)
for k in sorted(by, key=lambda k: -len(by[k])):
    xs = by[k]; m = len(xs)
    print('  %-22s n %3d  cum d12 %.1f d16 %.1f d18 %.1f d20 %.1f all %.1f | tom $ elite %6.0f us %6.0f | m %+6.0f' % (
        k[:22], m, *[sum(cum(o, d) for o in xs) / m for d in (12, 16, 18, 20, 29)],
        sum(o['tom_el'] for o in xs) / m, sum(o['tom_us'] for o in xs) / m, sum(o['m'] or 0 for o in xs) / m))
