"""rivalclass.py: classify each live rival by its step-0/1 orders and split a paired live comparison by class.
usage: rivalclass.py cand_rows.jsonl [corpus.json]"""
import sys, os, json, glob, collections
HERE = os.path.dirname(os.path.abspath(__file__))
KG = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
COST = {'COW': 400, 'SHEEP': 500, 'GOOSE': 300}
SEED = {'WHEAT': 10, 'CARROT': 20, 'TOMATO': 50, 'STRAWBERRY': 100, 'MELON': 80}
def spend(a):
    an = se = h = 0
    for o in (a.get('market', []) if isinstance(a, dict) else []) or []:
        if not isinstance(o, list) or not o: continue
        if o[0] == 'BUY_ANIMAL': an += COST.get(o[1], 0) * int(o[2])
        elif o[0] == 'BUY_SEED': se += SEED.get(o[1], 0) * int(o[2])
        elif o[0] == 'HIRE': h += 1
    return an, se, h
def classify(acts, s):
    a0 = spend(acts[1][s] if len(acts) > 1 else {}); a1 = spend(acts[2][s] if len(acts) > 2 else {})
    if a0[2] == 0 and a0[0] in (400, 1900) and a0[1] == 0:
        return 'C2S3'
    if a0[2] == 0 and a0[0] == 0 and a0[1] <= 10 and a1[0] == 1800 and a1[2] >= 4:
        return 'chassis'
    if a0[0] >= 2000 and a0[2] >= 3:
        return 'herdfirst'
    if a0[0] + a1[0] >= 2000:
        return 'herd-ish'
    return 'other'
if __name__ == '__main__':
    corpus = sys.argv[2] if len(sys.argv) > 2 else os.path.join(KG, 'gold', 'top10', 'gates', 'lv0928hi.json')
    cls = {}; oppn = {}
    for d in json.load(open(corpus, encoding='utf-8')):
        names = d['info']['TeamNames']
        if 'offhand' not in names: continue
        s = 1 - names.index('offhand')
        cls[d['id']] = classify(d['acts'], s); oppn[d['id']] = names[s]
    A = {r['gid']: r for r in (json.loads(l) for l in open(sys.argv[1], encoding='utf-8') if l.strip().startswith('{')) if r.get('m') is not None}
    B = {}
    for f in glob.glob(os.path.join(KG, 'gold', 'top10', 'gates', 'kout', 'kagg-lv0928-*', 'rows_lv*.jsonl')):
        for r in map(json.loads, open(f, encoding='utf-8')):
            if r.get('cand') == 'T8': B[r['gid']] = r
    by = collections.defaultdict(list)
    for g in A:
        if g in B: by[cls.get(g, '?')].append(g)
    print('corpus classes:', dict(collections.Counter(cls.values())))
    for c, kk in sorted(by.items(), key=lambda kv: -len(kv[1])):
        n = len(kk); d = [A[g]['m'] - B[g]['m'] for g in kk]
        col = sum(1 for g in kk if A[g]['them'] < 0.75 * B[g]['them'])
        kt = [g for g in kk if A[g]['them'] >= 0.75 * B[g]['them']]
        dt = [A[g]['m'] - B[g]['m'] for g in kt]
        print('%-10s n %3d  delta %+6.0f  wins %2d -> %2d  | no-collapse n %3d delta %+6.0f wins %2d -> %2d  (us %+.0f them %+.0f)' % (
            c, n, sum(d) / n, sum(B[g]['m'] > 0 for g in kk), sum(A[g]['m'] > 0 for g in kk), len(kt), sum(dt) / max(1, len(kt)),
            sum(B[g]['m'] > 0 for g in kt), sum(A[g]['m'] > 0 for g in kt), sum(A[g]['us'] - B[g]['us'] for g in kt) / max(1, len(kt)), sum(A[g]['them'] - B[g]['them'] for g in kt) / max(1, len(kt))))
