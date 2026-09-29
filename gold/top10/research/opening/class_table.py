"""class_table.py : FWt vs T8fcWt (and p1e = c2tr controller on herd-first) by rival class, opponent-stable seats only on the
elite gates; reacting panels for chassis (public copies), herd-poor (herd panel) and herd-first (v01-drip)."""
import json, os, sys, statistics as st, collections
sys.stdout.reconfigure(encoding='utf-8')
O = 'gold/top10/research/opening/'
def rows(f): return [x for x in (json.loads(l) for l in open(O + f, encoding='utf-8') if l.startswith('{')) if x.get('m') is not None] if os.path.exists(O + f) else []
def ek(f): return {(x['gid'], x['seat']): x for x in rows(f)}
def them(r): return r['us'] - r['m']
def line(tag, A, B, ks, la='FW', lb='T8'):
    if not ks: print('%-34s no data' % tag); return
    aw = sum(A[k]['m'] > 0 for k in ks); bw = sum(B[k]['m'] > 0 for k in ks)
    ao = sum(1 for k in ks if A[k]['m'] > 0 and B[k]['m'] <= 0); bo = sum(1 for k in ks if B[k]['m'] > 0 and A[k]['m'] <= 0)
    d = [A[k]['m'] - B[k]['m'] for k in ks]
    print('%-34s n %3d  %s wins %3d  %s wins %3d  %s-only %2d  %s-only %2d  margin %s-%s %+6.0f +- %4.0f' % (tag, len(ks), la, aw, lb, bw, la, ao, lb, bo, la, lb, st.mean(d), st.pstdev(d) / len(d) ** 0.5))
# ---- elite
fw = {**ek('fg_FWt_goldg.jsonl'), **ek('fg_FWt_top10g.jsonl')}
c2 = {**ek('fg_c2tr_goldg.jsonl'), **ek('fg_c2tr_top10g.jsonl')}
t8hf = ek('r4_T8fcWt_hf60.jsonl')
cls = {k: (c2[k].get('tel') or {}).get('gc_route') for k in c2}
t8 = {}
for k in c2:
    if cls[k] == 'herdfirst':
        if k in t8hf: t8[k] = t8hf[k]
    else:
        t8[k] = c2[k]
ks = [k for k in fw if k in t8]
stable = [k for k in ks if abs(them(fw[k]) - them(t8[k])) <= 0.2 * max(1, them(t8[k]))]
print('ELITE seats paired FWt/T8fcWt: %d, opponent-stable %d' % (len(ks), len(stable)))
by = collections.defaultdict(list)
for k in stable: by[cls.get(k)].append(k)
for c in ('chassis', 'C2S3', 'herdpoor', 'herdfirst', 'majkel', 'other'):
    line('elite %s' % c, fw, t8, by.get(c, []))
teams = collections.defaultdict(list)
for k in stable: teams[(cls.get(k), str(fw[k].get('team')))].append(k)
for (c, t), kk in sorted(teams.items()):
    line('   %s %s' % (c, t[:18]), fw, t8, kk)
# ---- p1e (c2tr) vs T8fcWt and vs FWt on herd-first seats
hf = [k for k in c2 if cls[k] == 'herdfirst' and k in t8hf and k in fw]
hf_st = [k for k in hf if abs(them(c2[k]) - them(t8hf[k])) <= 0.2 * max(1, them(t8hf[k])) and abs(them(c2[k]) - them(fw[k])) <= 0.2 * max(1, them(fw[k]))]
line('HERD-FIRST stable: p1e vs T8fcWt', c2, t8hf, hf_st, 'p1e', 'T8')
line('HERD-FIRST stable: p1e vs FWt', c2, fw, hf_st, 'p1e', 'FW')
print('   discordant seats (p1e / FWt / T8fcWt win flags):')
for k in hf_st:
    f = (c2[k]['m'] > 0, fw[k]['m'] > 0, t8hf[k]['m'] > 0)
    if len(set(f)) > 1:
        print('      %s %-15s p1e %d FWt %d T8 %d | margins %+.0f / %+.0f / %+.0f | rival step1 %s' % (k, str(c2[k].get('team'))[:15], f[0], f[1], f[2], c2[k]['m'], fw[k]['m'], t8hf[k]['m'], (c2[k].get('tel') or {}).get('gc_route_obs')))
# ---- reacting
def sk(f): return {(x['seed'], x['seat']): x for x in rows(f)}
for opp, fa, fb in (('omw', 'ft_omw.jsonl', 'r4_T8fcWt_omw.jsonl'), ('pub', 'ft_pub.jsonl', 'r4_T8fcWt_pub.jsonl'), ('sms', 'ft_sms.jsonl', 'r4_T8fcWt_sms.jsonl'), ('v01-drip (herd-first)', 'r3_FWt_drip.jsonl', 'r4_T8fcWt_drip.jsonl')):
    A = sk(fa); B = sk(fb); line('reacting chassis %s' % opp if 'drip' not in opp else 'reacting %s' % opp, A, B, sorted(set(A) & set(B)))
A = {(r['opp'], r['seed'], r['seat']): r for r in rows('hp_FWt.jsonl')}; B = {(r['opp'], r['seed'], r['seat']): r for r in rows('hp_T8fcWt.jsonl')}
line('reacting herd-poor panel (12 agents)', A, B, sorted(set(A) & set(B)))
