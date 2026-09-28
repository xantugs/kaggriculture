"""Forecast-free pre-drain selling (tie_probe.py rows): on controller days (t >= t0), every sale of ours of a premium product
at a post-drain step t (t = 4w+1) moves to the pre-drain step t-1 (ahead of any rival lot at t), capped by our shed
stock at t-1 from the programme's log. Variants: only when the rival sold that product at a post-drain step in the last
`days` days (a cheap signal), by hour class. Exact re-pricing, both schedules fixed.
usage: blanket.py probe_rows.jsonl [t0]"""
import sys, json, collections
sys.path.insert(0, __file__.rsplit('/', 1)[0] if '/' in __file__ else '.')
from reprice import events
from race import reprice_ordered

PREM = ("STRAWBERRY", "MILK", "WOOL")


def shift(evp, stock, t0, rule, rival_post):
    out = {t: [list(e) for e in es] for t, es in evp.items()}
    mv = 0
    for t in sorted(evp):
        if t < t0 or t % 4 != 1: continue
        if not rule(t, rival_post): continue
        k = sum(e[2] for e in out[t] if e[0] == 0 and e[1] == 'S')
        k = min(k, stock.get(t - 1, 0))
        if k <= 0: continue
        left = k; keep = []
        for e in out[t]:
            if e[0] == 0 and e[1] == 'S' and left > 0:
                take = min(left, e[2]); left -= take
                if e[2] - take > 0: keep.append([e[0], e[1], e[2] - take, e[3]])
            else:
                keep.append(e)
        out[t] = keep
        out.setdefault(t - 1, []).insert(0, [0, 'S', k, -1]); mv += k
    return out, mv


def main():
    rows = [json.loads(l) for l in open(sys.argv[1], encoding='utf-8')]
    rows = [r for r in rows if r.get('m') is not None]
    t0 = int(sys.argv[2]) if len(sys.argv) > 2 else 384
    n = len(rows)
    rules = {
        'all': lambda t, rp: True,
        'rival_post_2d': lambda t, rp: any(t - 48 <= s < t for s in rp),
        'rival_post_1d': lambda t, rp: any(t - 24 <= s < t for s in rp),
        'h21_only': lambda t, rp: t % 24 == 21,
        'h17_21': lambda t, rp: t % 24 in (17, 21),
        'not_h1': lambda t, rp: t % 24 != 1,
    }
    acc = collections.defaultdict(float)
    flips = collections.Counter()
    for r in rows:
        stock = collections.defaultdict(dict)
        for step, p, nn, dec, fc0, fc1 in r.get('dplog', []):
            stock[p][step] = nn
        ev = events(r)
        dm = collections.Counter()
        for p in PREM:
            evp = ev.get(p, {})
            if not evp: continue
            rp = sorted({t for t, es in evp.items() for sd, op, k, d in es if sd == 1 and op == 'S' and t % 4 == 1 and d > k})
            a0, b0 = reprice_ordered(evp, p, r['shops'])
            for lab, rule in rules.items():
                e2, mv = shift(evp, stock[p], t0, rule, rp)
                a, b = reprice_ordered(e2, p, r['shops'])
                acc[(lab, p)] += (a - b) - (a0 - b0); acc[(lab, p, 'u')] += mv
                acc[(lab, p, 'us')] += a - a0; acc[(lab, p, 'el')] += b - b0
                dm[lab] += (a - b) - (a0 - b0)
        for lab in rules:
            if r['m'] <= 0 < r['m'] + dm[lab]: flips[(lab, '+')] += 1
            if r['m'] > 0 >= r['m'] + dm[lab]: flips[(lab, '-')] += 1
    print(f"{n} seats, t0 = {t0}: our post-drain premium sales moved one step earlier (capped by shed stock), margin per seat")
    for lab in rules:
        tot = sum(acc[(lab, p)] for p in PREM) / n
        print(f"  {lab:14s} {tot:+6.0f}  static flips +{flips[(lab,'+')]}/-{flips[(lab,'-')]}  " + "  ".join(
            f"{p[:5]} {acc[(lab,p)]/n:+5.0f} [{acc[(lab,p,'us')]/n:+.0f}/{acc[(lab,p,'el')]/n:+.0f}] ({acc[(lab,p,'u')]/n:.1f}u)" for p in PREM))


if __name__ == '__main__':
    main()
