"""Summary vs T8 on goldg/top10g: opening-winner subset / others / all, with and without elite-collapse games.
usage: summ.py tag_goldg [tag_top10g]"""
import sys, os, json, math, collections
HERE = os.path.dirname(os.path.abspath(__file__))
KG = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..', '..'))
OW = {'Boey', 'Fourth Quadrant', '吃白饭的大肥鱼', 'Yizhou', 'THIRD FARM CLUB'}
base = {}
for g in ('goldg', 'top10g'):
    for l in open(os.path.join(KG, 'gold/top10/gates/kout/kagg-gate-r14c/rows_%s.jsonl' % g), encoding='utf-8'):
        r = json.loads(l); base[(r['gid'], r['seat'])] = r
new = {}
for t in sys.argv[1:]:
    for l in open(os.path.join(HERE, 'out', t + '_gate.jsonl'), encoding='utf-8'):
        r = json.loads(l); new[(r['gid'], r['seat'])] = r
keys = [k for k in new if k in base and new[k]['m'] is not None]
def coll(k): return new[k]['tape'] < 0.6 * new[k]['rec_tape'] or base[k]['tape'] < 0.6 * base[k]['rec_tape']
def stat(ks, label):
    if not ks: return
    d = [new[k]['m'] - base[k]['m'] for k in ks]; n = len(d); mu = sum(d) / n
    se = math.sqrt(sum((x - mu) ** 2 for x in d) / max(1, n - 1) / n) if n > 1 else 0
    du = sum(new[k]['us'] - base[k]['us'] for k in ks) / n; de = sum(new[k]['tape'] - base[k]['tape'] for k in ks) / n
    print('%-28s n=%3d dm %+7.0f +- %5.0f  wins %3d -> %3d  dus %+6.0f  delite %+6.0f' % (label, n, mu, se, sum(base[k]['m'] > 0 for k in ks), sum(new[k]['m'] > 0 for k in ks), du, de))
ow = [k for k in keys if new[k]['team'] in OW]; ot = [k for k in keys if new[k]['team'] not in OW]
stat(ow, 'opening winners'); stat([k for k in ow if not coll(k)], '  (no collapse)')
stat(ot, 'others'); stat([k for k in ot if not coll(k)], '  (no collapse)')
stat(keys, 'all'); stat([k for k in keys if not coll(k)], '  (no collapse)')
print('collapses:', sum(coll(k) for k in keys))
