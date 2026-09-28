"""Paired comparison of a candidate's Kaggle rows against base rows from earlier kernels (runs are bit-identical).
usage: kcmp.py base_label cand_label kout_dir[,kout_dir...]
Base rows are looked up in every gates/kout/*/rows_<gate>.jsonl with cand == base_label."""
import sys, os, json, glob, math, collections
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
K = os.path.join(ROOT, 'gold', 'top10', 'gates', 'kout')
base, cand, dirs = sys.argv[1], sys.argv[2], sys.argv[3].split(',')


def key(r):
    return (r.get('gid'), r.get('seat'), r.get('seed'), r.get('opp'))


rows = collections.defaultdict(dict)
for d in dirs:
    for f in glob.glob(os.path.join(K, d, 'rows_*.jsonl')):
        g = os.path.basename(f)[5:-6]
        for l in open(f, encoding='utf-8'):
            r = json.loads(l)
            if r.get('cand') == cand and r.get('m') is not None:
                rows[g][key(r)] = r['m']
tot = []
for g in sorted(rows):
    b = {}
    for f in glob.glob(os.path.join(K, '*', 'rows_%s.jsonl' % g)):
        for l in open(f, encoding='utf-8'):
            r = json.loads(l)
            if r.get('cand') == base and r.get('m') is not None:
                b[key(r)] = r['m']
    ks = [k for k in rows[g] if k in b]
    if not ks:
        print('%-22s no base rows' % g); continue
    dd = [rows[g][k] - b[k] for k in ks]; n = len(dd); m = sum(dd) / n
    se = math.sqrt(sum((x - m) ** 2 for x in dd) / max(1, n - 1) / n)
    up = sum(1 for k in ks if b[k] <= 0 < rows[g][k]); dn = sum(1 for k in ks if rows[g][k] <= 0 < b[k])
    print('%-22s n %4d  %+7.0f +- %4.0f  wins %4d -> %4d (+%d/-%d)  unchanged %d' % (g, n, m, se, sum(b[k] > 0 for k in ks), sum(rows[g][k] > 0 for k in ks), up, dn, sum(1 for x in dd if abs(x) < 0.5)))
