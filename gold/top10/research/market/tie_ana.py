"""Tie windows vs the market programme's decision log (tie_probe.py rows).
For premium products on controller days (t >= 384), windows where both sides first sell at the same post-drain step t
(t = 4w+1, a lockstep tie): our shed stock at t-1 (the pre-drain step), whether the programme ran at t-1, the rival
forecast it had for step t, and the elite's actual units at t. Then the pre-drain tie-break prize re-priced exactly,
(a) perfect foresight, units capped by our shed stock at t-1, and (b) only where the forecast for t was >= k units.
usage: tie_ana.py probe_rows.jsonl"""
import sys, json, collections
sys.path.insert(0, __file__.rsplit('/', 1)[0] if '/' in __file__ else '.')
from reprice import events
from race import window, reprice_ordered

PREM = ("STRAWBERRY", "MILK", "WOOL")


def main():
    rows = [json.loads(l) for l in open(sys.argv[1], encoding='utf-8')]
    rows = [r for r in rows if r.get('m') is not None]
    n = len(rows)
    st = collections.Counter(); acc = collections.defaultdict(float)
    fc_hist = collections.Counter()
    for r in rows:
        log = {(x[0], x[1]): x for x in r.get('dplog', [])}
        ev = events(r)
        for p in PREM:
            evp = ev.get(p, {})
            wins = collections.defaultdict(lambda: [dict(), dict()])
            for t, es in evp.items():
                for sd, op, k, d in es:
                    if op == 'S' and d > k and t >= 384:
                        wins[window(t)][sd][t] = wins[window(t)][sd].get(t, 0) + k
            ties = []
            for w, (a, b) in wins.items():
                if a and b and min(a) == min(b) and min(a) % 4 == 1:
                    t = min(a); ours = a[t]; theirs = b[t]
                    lg = log.get((t - 1, p))
                    stock = lg[2] if lg else 0
                    ran = lg is not None and lg[3] is not None
                    fc = lg[5] if lg else 0.0
                    st['ties'] += 1; st['tie_units'] += ours; st['el_units'] += theirs
                    st['stock_ok'] += 1 if stock >= ours else 0
                    st['stock_units'] += min(stock, ours)
                    st['ran'] += 1 if ran else 0
                    st['fc3'] += 1 if fc >= 3 else 0
                    st['fc1'] += 1 if fc >= 1 else 0
                    fc_hist[min(9, int(fc))] += 1
                    ties.append((t, min(stock, ours), fc, theirs))
            if not ties: continue
            a0, b0 = reprice_ordered(evp, p, r['shops'])
            for lab, sel in (('perfect', lambda fc, th: True), ('fc>=1', lambda fc, th: fc >= 1), ('fc>=2', lambda fc, th: fc >= 2),
                             ('fc>=3', lambda fc, th: fc >= 3), ('el>=3', lambda fc, th: th >= 3)):
                out = {t: [list(e) for e in es] for t, es in evp.items()}
                mv = 0
                for t, k, fc, th in ties:
                    if k <= 0 or not sel(fc, th): continue
                    left = k; keep = []
                    for e in out[t]:
                        if e[0] == 0 and e[1] == 'S' and left > 0:
                            take = min(left, e[2]); left -= take
                            if e[2] - take > 0: keep.append([e[0], e[1], e[2] - take, e[3]])
                        else:
                            keep.append(e)
                    out[t] = keep
                    out.setdefault(t - 1, []).insert(0, [0, 'S', k - left, -1]); mv += k - left
                a, b = reprice_ordered(out, p, r['shops'])
                acc[(lab, p)] += (a - b) - (a0 - b0); acc[(lab, p, 'u')] += mv
                acc[(lab, p, 'us')] += a - a0; acc[(lab, p, 'el')] += b - b0
    print(f"{n} seats, premium tie windows on days 16-29 (post-drain step t, both first sell at t): {st['ties']/n:.1f} a seat,")
    print(f"  our units {st['tie_units']/n:.1f}, elite units {st['el_units']/n:.1f} a seat; our shed at t-1 covered the tied lot in "
          f"{100*st['stock_ok']/max(1,st['ties']):.0f}% ({st['stock_units']/n:.1f} units a seat);")
    print(f"  the programme ran at t-1 in {100*st['ran']/max(1,st['ties']):.0f}%; its rival forecast for t was >= 1 in "
          f"{100*st['fc1']/max(1,st['ties']):.0f}%, >= 3 in {100*st['fc3']/max(1,st['ties']):.0f}%; forecast histogram {dict(sorted(fc_hist.items()))}")
    print("pre-drain tie-break prize (our shed-covered tied units sold at t-1, ahead), margin per seat [us/elite], units")
    for lab in ('perfect', 'fc>=1', 'fc>=2', 'fc>=3', 'el>=3'):
        tot = sum(acc[(lab, p)] for p in PREM) / n
        print(f"  {lab:8s} {tot:+6.0f}  " + "  ".join(f"{p[:5]} {acc[(lab,p)]/n:+5.0f} [{acc[(lab,p,'us')]/n:+.0f}/{acc[(lab,p,'el')]/n:+.0f}] ({acc[(lab,p,'u')]/n:.1f}u)" for p in PREM))


if __name__ == '__main__':
    main()
