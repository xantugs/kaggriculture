"""temporal.py trim N | report : ChatGPT's last moonshot, "what did the top teams change between 25-26 Sep and 27-28 Sep".
trim N   : keep at most N games per (team, batch) in games/index.jsonl (old = 25-26 Sep, new = 27-28 Sep), writing index.jsonl
           (the full index is kept as index_full.jsonl) so `extract_t.py elite` replays a balanced sample.
report   : from elite_days.jsonl / elite_seats.jsonl, per team and batch: the team's own final money and its rival's, and at
           days 3/6/9/12/15/20/25/29 cash, land quadrants, hands, herd, crop tiles and cumulative sales by product; then the
           new - old delta per team and, per metric, how many teams moved the same way (the common-change test)."""
import json, os, sys, collections, statistics as st, random
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__)); G = os.path.join(HERE, 'games')
TEAMS = ['Unknown Mother-Goose', 'Vadim Vasilenko', 'DECEM', 'DSM', 'Boey', 'Victor @ Tufa Labs', 'Majkel1337', 'Azat Akhtyamov', 'Fourth Quadrant', 'Anton Tikhonov']
batch = lambda date: 'old' if date <= '2026-09-26' else 'new'
DAYS = (3, 6, 9, 12, 15, 20, 25, 29)

if sys.argv[1] == 'trim':
    n = int(sys.argv[2])
    full = os.path.join(G, 'index_full.jsonl')
    if not os.path.exists(full): os.replace(os.path.join(G, 'index.jsonl'), full)
    idx = [json.loads(l) for l in open(full, encoding='utf-8') if l.strip()]
    random.seed(7); random.shuffle(idx)
    cnt = collections.Counter(); keep = []
    for r in idx:
        want = [s for s in r['seats'] if r['names'][s] in TEAMS and cnt[(r['names'][s], batch(r['date']))] < n]
        if want:
            for s in want: cnt[(r['names'][s], batch(r['date']))] += 1
            keep.append(r)
    keep.sort(key=lambda r: (r['date'], r['gid']))
    with open(os.path.join(G, 'index.jsonl'), 'w', encoding='utf-8') as fh:
        for r in keep: fh.write(json.dumps(r, ensure_ascii=False) + '\n')
    print(len(keep), 'games kept;', dict(sorted(cnt.items())))
    sys.exit()

seats = [json.loads(l) for l in open(os.path.join(HERE, 'elite_seats.jsonl'), encoding='utf-8') if l.strip()]
days = collections.defaultdict(dict)
for l in open(os.path.join(HERE, 'elite_days.jsonl'), encoding='utf-8'):
    r = json.loads(l); days[(r['gid'], r['seat'])][r['d']] = r
ok = [s for s in seats if s['rec_ok'] and s['team'] in TEAMS]
by = collections.defaultdict(list)
for s in ok: by[(s['team'], batch(s['date']))].append(s)


def feats(s):
    D = days[(s['gid'], s['seat'])]; f = {'final': s['rew'][0], 'rival_final': s['rew'][1], 'margin': s['rew'][0] - s['rew'][1]}
    cum_sell = collections.Counter(); cum_anim = collections.Counter(); cum_land = 0
    for d in range(30):
        r = D.get(d)
        if r is None: continue
        for k, v in (r.get('sell') or {}).items(): cum_sell[k] += v[1]
        for k, v in (r.get('buy_animal') or {}).items(): cum_anim[k] += v[0]
        cum_land += len(r.get('land') or [])
        if d in DAYS:
            f['cash@%d' % d] = r.get('m0')
            f['quads@%d' % d] = len(r.get('quads') or [])
            f['hands@%d' % d] = r.get('hands')
            for k in ('COW', 'SHEEP', 'GOOSE', 'CHICKEN'):
                f['herd_%s@%d' % (k, d)] = (r.get('herd') or {}).get(k, 0)
            for k in ('WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'MELON'):
                f['crop_%s@%d' % (k, d)] = (r.get('crops') or {}).get(k, 0)
            for k in ('WHEAT', 'EGG', 'MILK', 'WOOL', 'STRAWBERRY', 'CARROT', 'TOMATO', 'MELON', 'FERTILIZER'):
                f['sold_%s@%d' % (k, d)] = cum_sell.get(k, 0)
            f['animals_bought@%d' % d] = sum(cum_anim.values())
    return f


F = {k: [feats(s) for s in v] for k, v in by.items()}
teams = [t for t in TEAMS if (t, 'old') in F and (t, 'new') in F]
print('seats per team (old/new):', {t: (len(F[(t, 'old')]), len(F[(t, 'new')])) for t in teams})
mean = lambda L, k: st.mean([x[k] for x in L if x.get(k) is not None]) if any(x.get(k) is not None for x in L) else float('nan')
print('\nFINAL MONEY own / rival (old -> new):')
for t in teams:
    o, n = F[(t, 'old')], F[(t, 'new')]
    print('   %-22s own %6.0f -> %6.0f (%+6.0f) | rival %6.0f -> %6.0f | win%% %3.0f -> %3.0f' % (
        t[:22], mean(o, 'final'), mean(n, 'final'), mean(n, 'final') - mean(o, 'final'), mean(o, 'rival_final'), mean(n, 'rival_final'),
        100 * sum(x['margin'] > 0 for x in o) / len(o), 100 * sum(x['margin'] > 0 for x in n) / len(n)))
keys = sorted({k for L in F.values() for x in L for k in x if '@' in k}, key=lambda k: (k.split('@')[0], int(k.split('@')[1])))
print('\nCOMMON CHANGES (new - old per team; metrics where >= 6 of %d teams moved the same way by a meaningful amount):' % len(teams))
rows = []
for k in keys:
    ds = [mean(F[(t, 'new')], k) - mean(F[(t, 'old')], k) for t in teams]
    base = st.mean(abs(mean(F[(t, 'old')], k)) for t in teams) or 1.0
    thr = 0.1 * base if not k.startswith(('herd', 'crop', 'quads', 'hands')) else 0.5
    up = sum(1 for d in ds if d > thr); dn = sum(1 for d in ds if d < -thr)
    rows.append((max(up, dn), k, up, dn, ds, base))
for m, k, up, dn, ds, base in sorted(rows, key=lambda r: (-r[0], r[1])):
    if m >= 6:
        print('   %-22s up %2d down %2d | old mean %8.1f | per-team deltas: %s' % (k, up, dn, base, ' '.join('%+.1f' % d for d in ds)))
print('\nteam order for deltas:', teams)
