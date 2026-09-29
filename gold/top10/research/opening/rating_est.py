"""rating_est.py : both final tapes vs plain T8 on identical games, with a rating estimate per gate.
Rating conversion: delta = s * (logit(win rate cand) - logit(win rate T8)) on the same games, s = 70 (fitted on our ladder
games, 140 games with both ratings >= 2000) and s = 174 (chess Elo). Head to head: delta = s * logit(score vs T8)."""
import json, os, math, statistics as st, collections, sys
sys.stdout.reconfigure(encoding='utf-8')
O = 'gold/top10/research/opening/'
def rows(f):
    if not os.path.exists(O + f): return []
    return [json.loads(l) for l in open(O + f, encoding='utf-8') if l.startswith('{') and json.loads(l).get('m') is not None]
def by(f, key, cand_sub=None):
    d = {}
    for r in rows(f):
        if cand_sub is not None and cand_sub not in str(r.get('cand', '')): continue
        d[key(r)] = r['m']
    return d
lg = lambda p: math.log(p / (1 - p))
def clamp(p, n): return min(max(p, 0.5 / n), 1 - 0.5 / n)
def line(name, base, cand):
    ks = sorted(set(base) & set(cand))
    if not ks: return '%-22s  (no pairs)' % name
    n = len(ks); w0 = sum(base[k] > 0 for k in ks); w1 = sum(cand[k] > 0 for k in ks)
    d = [cand[k] - base[k] for k in ks]
    dl = lg(clamp(w1 / n, n)) - lg(clamp(w0 / n, n))
    return '%-22s n %3d  wins T8 %3d -> %3d   margin %+6.0f +- %4.0f   rating %+4.0f (s70) %+4.0f (s174)' % (name, n, w0, w1, st.mean(d), st.pstdev(d) / n ** 0.5, 70 * dl, 174 * dl)
seatkey = lambda r: (r['seed'], r['seat']); gidkey = lambda r: r['gid']; elkey = lambda r: (r.get('gid'), r.get('seat'))
CANDS = [
    ('A. wool tape = v29 + wool forecast (FW)', 'cmp_FW_T8.jsonl', ('x_FW_omw.jsonl', 'x_FW_pub.jsonl', 'x_FW_sms.jsonl'),
     ('cf_FWS_pin249.jsonl', 'full_v29fc_FW'), ('cf_FWS_live191.jsonl', 'full_v29fc_FW'), 'x_FW_goldg.jsonl', 'x_FW_top10g.jsonl'),
    ('B. T8 + wool forecast (T8fcW)', 'cmp_T8W_T8.jsonl', ('cmp_T8W_omw_v15a.jsonl', 'cmp_T8W_pub_metav4v13.jsonl', 'cmp_T8W_sms.jsonl'),
     ('cmp_T8W_pin249.jsonl', 'full_T8fcW'), ('cmp_T8W_live191.jsonl', 'full_T8fcW'), 'cmp_T8W_goldg.jsonl', 'cmp_T8W_top10g.jsonl'),
    ('(rejected) A + day-16 handover (FWS)', 'cmp_FWS_T8.jsonl', ('cf_FWS_omw.jsonl', 'cf_FWS_pub.jsonl', 'cf_FWS_sms.jsonl'),
     ('cf_FWS_pin249.jsonl', 'full_FWS'), ('cf_FWS_live191.jsonl', 'full_FWS'), 'cf_FWS_goldg.jsonl', 'cf_FWS_top10g.jsonl'),
    ('(rejected) B + day-16 handover (T8fcWS)', 'cmp_T8S_T8.jsonl', ('cmp_T8S_omw_v15a.jsonl', 'cmp_T8S_pub_metav4v13.jsonl', 'cmp_T8S_sms.jsonl'),
     ('cmp_T8S_pin249.jsonl', 'full_T8fcWS'), ('cmp_T8S_live191.jsonl', 'full_T8fcWS'), 'cmp_T8S_goldg.jsonl', 'cmp_T8S_top10g.jsonl'),
]
for tag, h2h, pub, pin, live, gg, tg in CANDS:
    print('== ' + tag)
    r = rows(h2h); m = [x['m'] for x in r]
    if m:
        sc = (sum(x > 0 for x in m) + 0.5 * sum(x == 0 for x in m)) / len(m)
        seeds = collections.defaultdict(list)
        for x in r: seeds[x['seed']].append(x['m'])
        sm = [st.mean(v) for v in seeds.values()]
        print('%-22s n %3d  %d-%d vs T8 (score %.2f)  margin %+6.0f +- %4.0f   rating %+4.0f (s70) %+4.0f (s174)' % ('head to head', len(m), sum(x > 0 for x in m), sum(x < 0 for x in m), sc, st.mean(m), st.pstdev(sm) / len(sm) ** 0.5, 70 * lg(clamp(sc, len(m))), 174 * lg(clamp(sc, len(m)))))
    for f, ref, nm in ((pub[0], 'cmp_T8_omw_v15a.jsonl', 'public omw'), (pub[1], 'cmp_T8_pub_metav4v13.jsonl', 'public pub'), (pub[2], 'cmp_T8_sms.jsonl', 'public smallershock')):
        print(line(nm, by(ref, seatkey), by(f, seatkey)))
    print(line('pin249 (day 12)', by('fin_pin249_T8_T8fc.jsonl', gidkey, 'main_ctl_T8'), by(pin[0], gidkey, pin[1])))
    print(line('live191 (day 12)', by('fin_live191_T8_T8fc.jsonl', gidkey, 'main_ctl_T8'), by(live[0], gidkey, live[1])))
    print(line('goldg (gold-zone elites)', by('cmp_T8_goldg.jsonl', elkey), by(gg, elkey)))
    print(line('top10g (top-10 elites)', by('cmp_T8_top10g.jsonl', elkey), by(tg, elkey)))
