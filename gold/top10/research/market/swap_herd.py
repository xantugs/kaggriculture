"""Sheep -> goose swap priced on recorded fill paths (exact re-pricing, both schedules fixed, margin = us - elite).
k sheep the tape places on day D become geese placed the same day: the sheep's wool schedule (cared: 6 units at D+6, then
4 every 3 days) is removed from our wool sales (from our first lots on or after each production day), the goose's eggs
(4 at D+4, then 2 a day) are sold at hour 1 of each day; feed and fertilizer are the same for both; +$200 cash a swap.
Towns are split by yarn stores among the shops known on day D (shop i unlocks at the end of day 3i+2).
usage: swap_herd.py rows.jsonl[,more] [D] [k]"""
import sys, collections
sys.path.insert(0, __file__.rsplit('/', 1)[0] if '/' in __file__ else '.')
from ana_fills import load
from reprice import events, reprice
from herd_val import sched


def remove_ours(ev_p, units_by_day):
    out = {t: [list(e) for e in es] for t, es in ev_p.items()}
    miss = 0
    for d in sorted(units_by_day):
        left = units_by_day[d]
        for t in sorted(out):
            if left <= 0: break
            if t < d * 24: continue
            for e in out[t]:
                if e[0] == 0 and e[1] == 'S' and e[2] > 0 and left > 0:
                    take = min(left, e[2]); e[2] -= take; left -= take
            out[t] = [e for e in out[t] if e[2] > 0]
        miss += left
    return out, miss


def main():
    rows = list(load(sys.argv[1]))
    D = int(sys.argv[2]) if len(sys.argv) > 2 else 9
    k = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    known = max(0, min(8, (D + 1) // 3))
    acc = collections.defaultdict(float); cnt = collections.Counter(); fl = collections.Counter()
    for r in rows:
        y = sum(1 for s in r['shops'][:known] if s == 'YARN_STORE')
        g = f"yarn{min(y, 1)}{'+' if y >= 1 else ''}"
        eggs = sum(1 for s in r['shops'][:known] if s in ('BAKERY', 'BRUNCH_SPOT'))
        ev = events(r)
        w0 = reprice(ev.get('WOOL', {}), 'WOOL', r['shops']); e0 = reprice(ev.get('EGG', {}), 'EGG', r['shops'])
        ws = {d: u * k for d, u in sched('SHEEP', D).items()}
        w2, miss = remove_ours(ev.get('WOOL', {}), ws)
        e2 = {t: [list(x) for x in es] for t, es in ev.get('EGG', {}).items()}
        for d, u in sched('GOOSE', D).items():
            e2.setdefault(d * 24 + 1, []).insert(0, [0, 'S', u * k, 0])
        w1 = reprice(w2, 'WOOL', r['shops']); e1 = reprice(e2, 'EGG', r['shops'])
        dw = (w1[0] - w1[1]) - (w0[0] - w0[1]); de = (e1[0] - e1[1]) - (e0[0] - e0[1])
        dm = dw + de + 200 * k
        for key in (g, 'all', f"eggshops{min(eggs, 1)}{'+' if eggs else ''}"):
            acc[(key, 'dm')] += dm; acc[(key, 'dw')] += dw; acc[(key, 'de')] += de; cnt[key] += 1
            acc[(key, 'wus')] += w1[0] - w0[0]; acc[(key, 'wel')] += w1[1] - w0[1]; acc[(key, 'miss')] += miss
            if r['m'] <= 0 < r['m'] + dm: fl[(key, '+')] += 1
            if r['m'] > 0 >= r['m'] + dm: fl[(key, '-')] += 1
    print(f"swap {k} sheep -> {k} geese placed on day {D} (shops known: {known}); margin change per seat, static")
    for key in sorted(cnt):
        n = cnt[key]
        print(f"  {key:10s} n={n:3d}  dmargin {acc[(key,'dm')]/n:+6.0f}  = wool {acc[(key,'dw')]/n:+6.0f} (us {acc[(key,'wus')]/n:+.0f}, elite {acc[(key,'wel')]/n:+.0f})"
              f" + eggs {acc[(key,'de')]/n:+6.0f} + cash {200*k:+d}   unmatched wool units {acc[(key,'miss')]/n:.1f}   static flips +{fl[(key,'+')]}/-{fl[(key,'-')]}")


if __name__ == '__main__':
    main()
