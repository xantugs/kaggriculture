"""Ties against copies (pinned4 PIN_FILLS rows, S = 0): per product and hour, the lockstep ties (both farms first sell a
product in a drain window at the same step), the units involved and the margin prize of winning each tie outright
(our lot at that step settles entirely first), exact re-pricing with both schedules fixed. Also: windows the copy
entered strictly earlier than us (the prize of matching its step) and revenue validation of the re-pricer.
usage: copy_ties.py rows.jsonl [games.csv]"""
import sys, json, csv, collections
sys.path.insert(0, __file__.rsplit('/', 1)[0] if '/' in __file__ else '.')
from ana_fills import P
from reprice import reprice
from race import window, reprice_ordered

AB = {'Pet': 'PET_CAFE', 'Smo': 'SMOOTHIE_SHOP', 'Bru': 'BRUNCH_SPOT', 'Ice': 'ICE_CREAM_SHOP', 'FM': 'FARMERS_MARKET',
      'Bak': 'BAKERY', 'Yarn': 'YARN_STORE', 'Piz': 'PIZZA_SHOP'}
PH = [(0, 144, 'd0-5'), (144, 288, 'd6-11'), (288, 528, 'd12-21'), (528, 720, 'd22-29')]


def events_pin(fills):
    ev = collections.defaultdict(lambda: collections.defaultdict(list))
    agg = collections.defaultdict(lambda: [0, 0.0])
    for step, op, item, price in fills:
        if op in ('S', 'rS', 'B', 'rB'):
            sd = 0 if op[0] != 'r' else 1
            o = op[-1]
            a = agg[(step, item, sd, o)]; a[0] += 1; a[1] += price
    for (step, item, sd, o), (n, d) in agg.items():
        ev[item][step].append([sd, o, n, d])
    return ev


def main():
    rows = [json.loads(l) for l in open(sys.argv[1], encoding='utf-8')]
    gpath = sys.argv[2] if len(sys.argv) > 2 else 'gold/top10/gates/live0926/games.csv'
    town = {int(r['episode_id']): [AB[w] for w in r['town'].split()] for r in csv.DictReader(open(gpath, encoding='utf-8-sig'))}
    rating = {int(r['episode_id']): float(r['opp_rating_before'] or 0) for r in csv.DictReader(open(gpath, encoding='utf-8-sig'))}
    rows = [r for r in rows if r.get('m') is not None and r.get('fills')]
    n = len(rows)
    err = collections.defaultdict(float); tot = collections.defaultdict(float)
    acc = collections.defaultdict(float); cnt = collections.defaultdict(float)
    per_game = collections.defaultdict(float)
    for r in rows:
        shops = town[r['gid']]
        ev = events_pin(r['fills'])
        for p in P:
            evp = ev.get(p, {})
            if not evp: continue
            a, b, _, _ = reprice(evp, p, shops)
            ra = sum(e[3] * (1 if e[1] == 'S' else -1) for es in evp.values() for e in es if e[0] == 0)
            rb = sum(e[3] * (1 if e[1] == 'S' else -1) for es in evp.values() for e in es if e[0] == 1)
            err[p] += abs(a - ra) + abs(b - rb); tot[p] += abs(ra) + abs(rb)
            a0, b0 = reprice_ordered(evp, p, shops)
            wins = collections.defaultdict(lambda: [dict(), dict()])
            for t, es in evp.items():
                for sd, op, k, d in es:
                    if op == 'S' and d > k: wins[window(t)][sd][t] = wins[window(t)][sd].get(t, 0) + k
            for w, (x, y) in wins.items():
                if not x or not y: continue
                fa, fb = min(x), min(y)
                ph = [lab for lo, hi, lab in PH if lo <= fa < hi][0]
                h = fa % 24
                if fa == fb:
                    kind = 'tie'; tgt = fa; src = [fa]
                elif fb < fa:
                    kind = 'copy_first'; tgt = fb; src = list(x)
                else:
                    continue
                out = {t: [list(e) for e in es] for t, es in evp.items()}
                k = 0
                for t in src:
                    keep = []
                    for e in out[t]:
                        if e[0] == 0 and e[1] == 'S' and e[3] != -1: k += e[2]
                        else: keep.append(e)
                    out[t] = keep
                out.setdefault(tgt, []).insert(0, [0, 'S', k, -1])
                a1, b1 = reprice_ordered(out, p, shops)
                dm = (a1 - b1) - (a0 - b0)
                acc[(kind, ph, p)] += dm; cnt[(kind, ph, p)] += k
                acc[(kind, ph, p, h)] += dm
                if kind == 'tie' and fa < 528: per_game[r['gid']] += dm
    print(f"{n} copy games (full game, S = 0). re-pricer revenue error per game: " + " ".join(f"{p[:4]} {err[p]/n:.0f}/{tot[p]/n:.0f}" for p in P))
    for kind in ('tie', 'copy_first'):
        print(f"\n{kind}: margin prize per game if our lot settled first (units per game)")
        for p in P:
            s = [f"{lab} {acc[(kind, lab, p)]/n:+5.0f} ({cnt[(kind, lab, p)]/n:4.1f}u)" for lo, hi, lab in PH]
            if any(abs(acc[(kind, lab, p)]) / n >= 1 for lo, hi, lab in PH):
                print(f"  {p:10s} " + "  ".join(s))
        print("  total " + "  ".join(f"{lab} {sum(acc[(kind, lab, p)] for p in P)/n:+.0f}" for lo, hi, lab in PH))
        for lo, hi, lab in PH[:3]:
            top = sorted(((acc[(kind, lab, p, h)] / n, p, h) for p in P for h in range(24)), reverse=True)[:6]
            print(f"  {lab} top (product, hour): " + "  ".join(f"{p[:5]}@h{h} {v:+.0f}" for v, p, h in top if v >= 1))
    # close games: does the tie prize (days 0-21) exceed the loss?
    lost = [r for r in rows if r['m'] <= 0]
    print(f"\nlosses {len(lost)}: " + ", ".join(f"{r['gid']} m {r['m']:+.0f} tie prize d0-21 {per_game[r['gid']]:+.0f} opp {rating.get(r['gid'],0):.0f}" for r in sorted(lost, key=lambda r: -r['m'])))


if __name__ == '__main__':
    main()
