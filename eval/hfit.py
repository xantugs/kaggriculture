"""hfit.py ROWS REFS[,REFS] [BASE_NAME] : paired comparison of every variant file in ROWS against the baseline file (default
CGt_final.py) on the same seats, per rating band and per end date (29 Sep = train, 30 Sep = holdout): wins, discordant pairs
(+/-), mean margin delta, sign-test p-value. Also splits by the handover the baseline reached (tel gc_days from the baseline
rows: 10 = copies/480, 14 = divergent/384, 18 = rich/288) so the handover variants can be read per class."""
import sys, os, json, collections, math
sys.stdout.reconfigure(encoding='utf-8')
rows_path, refs_path = sys.argv[1], sys.argv[2]
base_name = sys.argv[3] if len(sys.argv) > 3 else 'CGt_final.py'
refs = {}
for rp in refs_path.split(','):
    for l in open(rp, encoding='utf-8'):
        r = json.loads(l); k = (r['gid'], r['seat'])
        if k not in refs or refs[k].get('rating') is None:
            refs[k] = dict(band=r.get('band'), rating=r.get('rating'), end=(r.get('end') or '')[:10], team=r.get('team'))
M = collections.defaultdict(dict); TEL = {}
for l in open(rows_path, encoding='utf-8'):
    x = json.loads(l)
    if x.get('m') is None: continue
    f = os.path.basename(x['file']); k = (x['gid'], x['seat'])
    M[f][k] = x['m']
    if f == base_name and x.get('tel'): TEL[k] = x['tel']
# baseline tel for the lad seats comes from the CGt gate run if the rows lack it
for p in ('gold/top10/research/nmloop/lad_TAPE.jsonl', 'gold/top10/research/nmloop/f29_TAPE.jsonl'):
    if os.path.exists(p):
        for l in open(p, encoding='utf-8'):
            x = json.loads(l); k = (x['gid'], x['seat'])
            if k not in TEL and x.get('tel'): TEL[k] = x['tel']
base = M.get(base_name, {})
print('baseline %s: %d seats scored; variants: %s' % (base_name, len(base), ', '.join(f for f in sorted(M) if f != base_name)))


def sign_p(up, dn):
    n = up + dn
    if n == 0: return 1.0
    k = max(up, dn)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k, n + 1)) / 2 ** n)


def block(label, keys):
    keys = [k for k in keys if k in base]
    if len(keys) < 5: return
    print('\n== %s (n=%d) baseline wins %d (%.0f%%), mean %+.0f' % (label, len(keys), sum(base[k] > 0 for k in keys), 100 * sum(base[k] > 0 for k in keys) / len(keys), sum(base[k] for k in keys) / len(keys)))
    print('   %-16s %5s %5s %6s %6s %8s %6s' % ('variant', 'n', 'wins', '+flip', '-flip', 'dMargin', 'p'))
    for f in sorted(M):
        if f == base_name: continue
        ks = [k for k in keys if k in M[f]]
        if len(ks) < 5: continue
        up = sum(1 for k in ks if M[f][k] > 0 >= base[k]); dn = sum(1 for k in ks if base[k] > 0 >= M[f][k])
        print('   %-16s %5d %5d %6d %6d %+8.0f %6.3f' % (f[:16], len(ks), sum(M[f][k] > 0 for k in ks), up, dn, sum(M[f][k] - base[k] for k in ks) / len(ks), sign_p(up, dn)))


allk = list(base)
block('ALL', allk)
for b in sorted({refs[k]['band'] for k in allk if k in refs and refs[k].get('band') is not None}):
    ks = [k for k in allk if k in refs and refs[k]['band'] == b]
    block('band %d' % b, ks)
    block('band %d, 29 Sep (train)' % b, [k for k in ks if refs[k]['end'] == '2026-09-29'])
    block('band %d, 30 Sep (holdout)' % b, [k for k in ks if refs[k]['end'] == '2026-09-30'])
for gd, name in ((10, 'baseline handover 480 (copies)'), (14, 'baseline handover 384 (divergent)'), (18, 'baseline handover 288 (rich)')):
    block(name, [k for k in allk if (TEL.get(k) or {}).get('gc_days') == gd])
