"""Tick-defer priced on recorded fill paths (exact re-pricing, both schedules fixed): our sales at a pre-drain step t
(t = 0 mod 4, the town drains right after that market) move to t+1 (post-drain), in lockstep with any elite lot at t+1
(it keeps its index 0). Split by phase and product; variants exclude hour 0 (the night-drop sale at the midnight tick)
or restrict to premium goods.
usage: tickdefer.py rows.jsonl[,more]"""
import sys, collections
sys.path.insert(0, __file__.rsplit('/', 1)[0] if '/' in __file__ else '.')
from ana_fills import load, P, PH
from reprice import events, reprice


def defer(ev_p, lo, hi, skip_h0):
    out = {t: [list(e) for e in es] for t, es in ev_p.items()}
    mv = 0
    for t in sorted(ev_p):
        if not (lo <= t < hi) or t % 4 != 0 or t >= 716: continue
        if skip_h0 and t % 24 == 0: continue
        ours = [e for e in out[t] if e[0] == 0 and e[1] == 'S']
        if not ours: continue
        out[t] = [e for e in out[t] if not (e[0] == 0 and e[1] == 'S')]
        k = sum(e[2] for e in ours)
        out.setdefault(t + 1, []).append([0, 'S', k, 1]); mv += k
    return out, mv


def main():
    rows = list(load(sys.argv[1])); n = len(rows)
    acc = collections.defaultdict(float); fl = collections.Counter()
    PHS = [(0, 288), (288, 384), (384, 576), (576, 720)]
    for r in rows:
        ev = events(r)
        dm = collections.Counter()
        for p in P:
            evp = ev.get(p, {})
            if not evp: continue
            a0, b0, _, _ = reprice(evp, p, r['shops'])
            for ph, (lo, hi) in enumerate(PHS):
                for sk in (False, True):
                    e2, mv = defer(evp, lo, hi, sk)
                    if not mv: continue
                    a, b, _, _ = reprice(e2, p, r['shops'])
                    acc[(p, ph, sk)] += (a - b) - (a0 - b0); acc[(p, ph, sk, 'u')] += mv
                    acc[(p, ph, sk, 'us')] += a - a0; acc[(p, ph, sk, 'el')] += b - b0
                    if ph <= 1: dm[sk] += (a - b) - (a0 - b0)
        for sk in (False, True):
            if r['m'] <= 0 < r['m'] + dm[sk]: fl[(sk, '+')] += 1
            if r['m'] > 0 >= r['m'] + dm[sk]: fl[(sk, '-')] += 1
    print(f"{n} seats. our pre-drain sales deferred one step (all | hour 0 excluded): margin per seat (units) [us/elite, hour 0 excluded]")
    for p in P:
        print(f"  {p:10s} " + "  ".join(f"{PH[ph]} {acc[(p,ph,False)]/n:+5.0f}({acc[(p,ph,False,'u')]/n:4.1f}) | {acc[(p,ph,True)]/n:+5.0f}({acc[(p,ph,True,'u')]/n:4.1f}) [{acc[(p,ph,True,'us')]/n:+.0f}/{acc[(p,ph,True,'el')]/n:+.0f}]" for ph in range(4)))
    for sk in (False, True):
        print(f"  total {'no h0' if sk else 'all  '}: " + "  ".join(f"{PH[ph]} {sum(acc[(p, ph, sk)] for p in P)/n:+.0f}" for ph in range(4))
              + f"   days 0-15 static flips +{fl[(sk,'+')]}/-{fl[(sk,'-')]}")
    prem = ("STRAWBERRY", "MILK", "WOOL", "MELON")
    for sk in (False, True):
        print(f"  premium only {'no h0' if sk else 'all  '}: " + "  ".join(f"{PH[ph]} {sum(acc[(p, ph, sk)] for p in prem)/n:+.0f}" for ph in range(4)))


if __name__ == '__main__':
    main()
