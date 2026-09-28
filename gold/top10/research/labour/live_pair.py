"""Paired live-gate comparison (pinned4 rows keyed by gid), split by opponent group (games.csv opp_group), with ledger deltas.
usage: live_pair.py base.jsonl cand.jsonl"""
import sys, json, csv, statistics as st, collections
B = {r['gid']: r for r in map(json.loads, open(sys.argv[1], encoding='utf-8'))}
C = {r['gid']: r for r in map(json.loads, open(sys.argv[2], encoding='utf-8'))}
grp = {}
for row in csv.DictReader(open('gold/top10/gates/live0926/games.csv', encoding='utf-8-sig')):
    grp[int(row['episode_id'])] = row.get('opp_group', '?')
ks = [k for k in C if k in B and C[k]['m'] is not None and B[k]['m'] is not None]
def line(name, sel):
    if not sel: return
    d = [C[k]['m'] - B[k]['m'] for k in sel]; n = len(d)
    se = st.pstdev(d) / n ** 0.5 if n > 1 else 0
    wb = sum(B[k]['m'] > 0 for k in sel); wc = sum(C[k]['m'] > 0 for k in sel)
    up = sum(B[k]['m'] <= 0 < C[k]['m'] for k in sel); dn = sum(C[k]['m'] <= 0 < B[k]['m'] for k in sel)
    print(f"{name:14s} n {n:3d} {st.mean(d):+7.0f} +- {se:4.0f}  wins {wb:3d} -> {wc:3d} (+{up}/-{dn})  changed {sum(1 for x in d if x)}")
line('ALL', ks)
by = collections.defaultdict(list)
for k in ks: by[grp.get(k, '?')].append(k)
for g, sel in sorted(by.items()): line(g, sel)
led = collections.Counter(); ledt = collections.Counter()
for k in ks:
    for p, v in C[k]['led_us'].items(): led[p] += v
    for p, v in B[k]['led_us'].items(): led[p] -= v
    for p, v in C[k]['led_them'].items(): ledt[p] += v
    for p, v in B[k]['led_them'].items(): ledt[p] -= v
n = len(ks)
print('ledger d us  :', ' '.join(f"{p[:5]} {v/n:+.0f}" for p, v in sorted(led.items(), key=lambda kv: kv[1])))
print('ledger d them:', ' '.join(f"{p[:5]} {v/n:+.0f}" for p, v in sorted(ledt.items(), key=lambda kv: kv[1])))
flips = [(k, B[k]['opp'], B[k]['m'], C[k]['m']) for k in ks if (B[k]['m'] > 0) != (C[k]['m'] > 0)]
for f in flips: print('  flip', f)
