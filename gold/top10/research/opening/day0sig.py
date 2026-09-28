"""day0sig.py: day-0/1 purchase signatures per team from compact game files (gz jsonl or json list).
usage: day0sig.py file [file...] [--teams] [--opp offhand]  (with --opp, profile the opponents of that team)"""
import sys, json, gzip, collections
args = [a for a in sys.argv[1:] if not a.startswith('--')]
opp = None
if '--opp' in sys.argv:
    opp = sys.argv[sys.argv.index('--opp') + 1]
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
            if opp is not None and (opp != names[1 - s]):
                continue
            team = names[s]
            acts = d['acts']
            c = collections.Counter()
            for st in range(1, 4):   # actions at steps 0..2
                a = acts[st][s] if st < len(acts) and isinstance(acts[st][s], dict) else {}
                for o in a.get('market', []) or []:
                    if not isinstance(o, list) or not o: continue
                    if o[0] == 'BUY_ANIMAL': c[o[1][0]] += int(o[2])
                    elif o[0] == 'BUY_SEED': c[o[1][0].lower()] += int(o[2])
                    elif o[0] == 'HIRE': c['h'] += 1
                    elif o[0] == 'BUY_LAND': c['L'] += 1
            key = 'C%dS%dG%d m%d w%d s%d h%d' % (c['C'], c['S'], c['G'], c['m'], c['w'], c['s'], c['h'])
            sig[team][key] += 1; nseat[team] += 1
for team, cnt in sorted(sig.items(), key=lambda kv: -nseat[kv[0]]):
    tot = nseat[team]
    print('%-26s n %3d  ' % (team[:26], tot) + '  '.join('%s %d%%' % (k, 100 * v // tot) for k, v in cnt.most_common(3)))
