"""Pre-drain tie-break: in windows where both sides first sell at the same step t (a lockstep tie), move our units sold
at t to step t-1 (the step before the drain when t = 4w+1), ahead of the elite. Margin change per seat by phase and
product, exact re-pricing with both schedules fixed. Also: the same move only when the tie step is a post-drain step.
usage: pretie.py rows.jsonl[,more] [team]"""
import sys, collections
sys.path.insert(0, __file__.rsplit('/', 1)[0] if '/' in __file__ else '.')
from ana_fills import P, load, PH
from reprice import events
from race import window, reprice_ordered


def pretie(ev_p, t_lo, t_hi, post_only):
    wins = collections.defaultdict(lambda: [set(), set()])
    for t, es in ev_p.items():
        for sd, op, n, d in es:
            if op == 'S' and d > n: wins[window(t)][sd].add(t)
    out = {t: [list(e) for e in es] for t, es in ev_p.items()}
    moved = 0
    for w, (a, b) in wins.items():
        if not a or not b: continue
        fa, fb = min(a), min(b)
        if fa != fb or not (t_lo <= fa < t_hi): continue
        if post_only and fa % 4 != 1: continue
        k = 0; keep = []
        for e in out[fa]:
            if e[0] == 0 and e[1] == 'S': k += e[2]
            else: keep.append(e)
        out[fa] = keep
        out.setdefault(fa - 1, []).insert(0, [0, 'S', k, -1])
        moved += k
    return out, moved


rows = list(load(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
n = len(rows)
acc = collections.defaultdict(float)
for r in rows:
    ev = events(r)
    for p in ("STRAWBERRY", "MILK", "WOOL", "MELON", "TOMATO", "EGG", "FERTILIZER", "WHEAT", "CARROT"):
        evp = ev.get(p, {})
        if not evp: continue
        a0, b0 = reprice_ordered(evp, p, r['shops'])
        for ph, (lo, hi) in enumerate([(0, 288), (288, 384), (384, 576), (576, 720)]):
            for po in (False, True):
                e2, mv = pretie(evp, lo, hi, po)
                if not mv: continue
                a, b = reprice_ordered(e2, p, r['shops'])
                acc[(p, ph, po)] += (a - b) - (a0 - b0); acc[(p, ph, po, 'u')] += mv
                acc[(p, ph, po, 'us')] += a - a0; acc[(p, ph, po, 'el')] += b - b0
print(f"{n} seats. tie windows: our tied units one step earlier (all ties | post-drain ties only): margin per seat (units) [us/el]")
for p in P:
    print(f"  {p:10s} " + "  ".join(f"{PH[ph]} {acc[(p,ph,False)]/n:+5.0f}({acc[(p,ph,False,'u')]/n:4.1f}) | {acc[(p,ph,True)]/n:+5.0f}({acc[(p,ph,True,'u')]/n:4.1f}) [{acc[(p,ph,True,'us')]/n:+.0f}/{acc[(p,ph,True,'el')]/n:+.0f}]" for ph in range(4)))
for po in (False, True):
    print(f"  total {'post' if po else 'all '}: " + "  ".join(f"{PH[ph]} {sum(acc[(p, ph, po)] for p in P)/n:+.0f}" for ph in range(4)))
