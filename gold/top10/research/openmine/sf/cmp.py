"""Day-by-day farm comparison: ours vs the repaired elite in the same games (sf/out/<tag>_days.jsonl).
usage: cmp.py tag [team] [gid]"""
import sys, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__))
tag = sys.argv[1]; team = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != 'all' else None
gid = int(sys.argv[3]) if len(sys.argv) > 3 else None
rows = collections.defaultdict(dict)
for l in open(os.path.join(HERE, 'out', tag + '_days.jsonl'), encoding='utf-8'):
    r = json.loads(l)
    if gid and r['gid'] != gid: continue
    t = r['opp'] if r['role'] == 'ours' else r['team']
    if team and t != team: continue
    rows[(r['gid'], r['role'])][r['d']] = r
games = sorted(set(g for g, _ in rows))
print(tag, team, 'games', len(games))
def agg(role, d, f):
    xs = [f(rows[(g, role)][d]) for g in games if d in rows.get((g, role), {})]
    xs = [x for x in xs if x is not None]
    return sum(xs) / max(1, len(xs))
def land_day(role, q):
    out = []
    for g in games:
        for d, r in rows[(g, role)].items():
            for e in r['land']:
                if e['q'] == q: out.append(d + e['h'] / 24)
    return (sum(out) / len(out), len(out)) if out else (None, 0)
for role in ('ours', 'elite_rep'):
    print(role, 'land', {q: land_day(role, q) for q in ('NE', 'SW', 'SE')})
hdr = 'd  | m0 ours/el      | hires   | C o/e    S o/e    G o/e   | STR o/e    WHE o/e    MEL o/e   TOM o/e  | sells$ o/e       | anim$ o/e     seed$ o/e'
print(hdr)
for d in range(0, 18):
    def f(role, fn): return agg(role, d, fn)
    herd = lambda k: (lambda r: (r.get('herd') or {}).get(k, 0))
    crop = lambda k: (lambda r: (r.get('crops') or {}).get(k, 0))
    sells = lambda r: sum(v[1] for v in r['sell'].values())
    an = lambda r: sum(v[1] for v in r['buy_animal'].values())
    sd = lambda r: sum(v[1] for v in r['buy_seed'].values())
    print('%2d | %6.0f %6.0f | %4.1f %4.1f | %4.1f %4.1f  %4.1f %4.1f  %4.1f %4.1f | %5.1f %5.1f  %5.1f %5.1f  %4.1f %4.1f  %4.1f %4.1f | %6.0f %6.0f | %5.0f %5.0f  %5.0f %5.0f' % (
        d, f('ours', lambda r: r['m0']), f('elite_rep', lambda r: r['m0']), f('ours', lambda r: r['hires']), f('elite_rep', lambda r: r['hires']),
        f('ours', herd('COW')), f('elite_rep', herd('COW')), f('ours', herd('SHEEP')), f('elite_rep', herd('SHEEP')), f('ours', herd('GOOSE')), f('elite_rep', herd('GOOSE')),
        f('ours', crop('STRAWBERRY')), f('elite_rep', crop('STRAWBERRY')), f('ours', crop('WHEAT')), f('elite_rep', crop('WHEAT')),
        f('ours', crop('MELON')), f('elite_rep', crop('MELON')), f('ours', crop('TOMATO')), f('elite_rep', crop('TOMATO')),
        f('ours', sells), f('elite_rep', sells), f('ours', an), f('elite_rep', an), f('ours', sd), f('elite_rep', sd)))
# revenue by product days 0-16 (from day rows)
for role in ('ours', 'elite_rep'):
    c = collections.Counter()
    for g in games:
        for d, r in rows[(g, role)].items():
            if d > 16: continue
            for it, (n, v) in r['sell'].items(): c[it] += v / len(games)
    print(role, 'sells d0-16:', ' '.join('%s %.0f' % (k[:5], v) for k, v in c.most_common()))
