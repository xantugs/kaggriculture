"""usage: livecmp.py base.jsonl new.jsonl -- paired live-gate comparison by game, split by opponent group and rating."""
import json, math, sys, csv, collections, os
SP = os.environ.get('SP', '/tmp/claude-0/-home-user-kaggriculture/166c82bf-ec8d-5801-898c-9c9362e32053/scratchpad')
meta = {r['episode_id']: r for r in csv.DictReader(open(SP + '/live0926/games.csv', encoding='utf-8-sig'))}
def load(f):
    return {r['gid']: r for r in map(json.loads, open(f)) if r['m'] is not None}
a, b = load(sys.argv[1]), load(sys.argv[2])
ks = [k for k in b if k in a]
def grp(k):
    m = meta[str(k)]; g = m['opp_group']
    t = 'copy' if g.startswith('copy (identical') else 'annex' if 'annex' in g else 'own'
    return t, ('2600+' if float(m['opp_rating_before']) >= 2600 else '<2600')
def stat(keys, label):
    if not keys: return
    d = [b[k]['m'] - a[k]['m'] for k in keys]
    md = sum(d) / len(d); se = math.sqrt(sum((x - md) ** 2 for x in d) / max(1, len(d) - 1) / len(d)) if len(d) > 1 else 0
    wa = sum(a[k]['m'] > 0 for k in keys); wb = sum(b[k]['m'] > 0 for k in keys)
    fu = sum(1 for k in keys if a[k]['m'] <= 0 < b[k]['m']); fd = sum(1 for k in keys if b[k]['m'] <= 0 < a[k]['m'])
    print('%-16s n %3d %+6.0f +- %4.0f  wins %3d -> %3d (+%d/-%d) changed %d' % (label, len(d), md, se, wa, wb, fu, fd, sum(1 for x in d if x)))
stat(ks, 'all')
by = collections.defaultdict(list)
for k in ks: by[grp(k)].append(k)
for g in sorted(by): stat(by[g], '%s %s' % g)
stat([k for k in ks if grp(k)[1] == '2600+'], 'ALL 2600+')
