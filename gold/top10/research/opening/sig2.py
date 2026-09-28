"""sig2.py: per-team spend at steps 0 and 1 (what a rival can see at step 1 and 2): animals$, seeds$, hires, land.
usage: sig2.py file [file...] [--opp TEAM] [--self TEAM]"""
import sys, json, gzip, collections
args = []; opp = None; me = None
it = iter(sys.argv[1:])
for a in it:
    if a == '--opp': opp = next(it)
    elif a == '--self': me = next(it)
    else: args.append(a)
FIB = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]
COST = {'COW': 400, 'SHEEP': 500, 'GOOSE': 300}
SEED = {'WHEAT': 10, 'CARROT': 20, 'TOMATO': 50, 'STRAWBERRY': 100, 'MELON': 80}
def games(f):
    if f.endswith('.gz'):
        for l in gzip.open(f, 'rt', encoding='utf-8'):
            if l.strip(): yield json.loads(l)
    elif f.endswith('.jsonl'):
        for l in open(f, encoding='utf-8'):
            if l.strip(): yield json.loads(l)
    else:
        for d in json.load(open(f, encoding='utf-8')): yield d
sig = collections.defaultdict(collections.Counter); nseat = collections.Counter()
for f in args:
    for d in games(f):
        names = d['info']['TeamNames']
        for s in (0, 1):
            if opp is not None and opp != names[1 - s]: continue
            if me is not None and me != names[s]: continue
            team = names[s]; acts = d['acts']
            parts = []
            for st in (1, 2):   # orders issued at step 0 and step 1
                a = acts[st][s] if st < len(acts) and isinstance(acts[st][s], dict) else {}
                an = se = h = L = 0
                for o in a.get('market', []) or []:
                    if not isinstance(o, list) or not o: continue
                    if o[0] == 'BUY_ANIMAL': an += COST.get(o[1], 0) * int(o[2])
                    elif o[0] == 'BUY_SEED': se += SEED.get(o[1], 0) * int(o[2])
                    elif o[0] == 'HIRE': h += 1
                    elif o[0] == 'BUY_LAND': L += 1
                parts.append('a%d s%d h%d' % (an, se, h) + (' L' if L else ''))
            key = 's0[%s] s1[%s]' % tuple(parts)
            sig[team][key] += 1; nseat[team] += 1
for team, cnt in sorted(sig.items(), key=lambda kv: -nseat[kv[0]]):
    tot = nseat[team]
    print('%-26s n %3d  ' % (team[:26], tot) + '  '.join('%s %d%%' % (k, 100 * v // tot) for k, v in cnt.most_common(3)))
