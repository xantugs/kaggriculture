"""h23 pre-drop feasibility and value in copy games (copy_probe.py rows).
A snapshot at step s (hour 20..23, after that step's unit actions) lists each unit carrying premium goods and its walking
distance k to the nearest shed-access tile. The unit can DROP by step 23 if k <= 22 - s (walk k steps, drop at s+k+1),
so its goods can be sold at hour 23, one step ahead of the rival's hour-0 lot in the same drain window.
Reported per game (days 6-21): premium units carried into the night drop (us / copy), those whose unit was within reach
of the shed at some evening snapshot, and the re-priced margin of selling the reachable units at hour 23 at index 0
instead of in their hour-0 lot (both schedules otherwise fixed).
usage: h23_ana.py copy_probe_rows.jsonl"""
import sys, json, csv, collections
sys.path.insert(0, __file__.rsplit('/', 1)[0] if '/' in __file__ else '.')
from copy_ties import events_pin, AB
from race import reprice_ordered

PREM = ("MILK", "WOOL", "STRAWBERRY", "MELON")


def main():
    rows = [json.loads(l) for l in open(sys.argv[1], encoding='utf-8') if l.strip()]
    rows = [r for r in rows if r.get('m') is not None]
    town = {int(r['episode_id']): [AB[w] for w in r['town'].split()] for r in csv.DictReader(open('gold/top10/gates/live0926/games.csv', encoding='utf-8-sig'))}
    n = len(rows)
    acc = collections.defaultdict(float)
    for r in rows:
        shops = town[r['gid']]
        night = collections.defaultdict(lambda: [collections.Counter(), collections.Counter()])
        for step, side, c in r['night']:
            for k, v in c.items(): night[step // 24][side][k] += v
        reach = collections.defaultdict(collections.Counter)   # day -> product -> units reachable (ours)
        best = {}
        for row in r['snap']:
            s = row[0]; day = s // 24; h = s % 24
            ours = row[1][0]
            for u, dist, c in ours:
                if dist <= 22 - h:
                    key = (day, u)
                    best[key] = c   # latest snapshot wins (goods only grow through the evening)
        for (day, u), c in best.items():
            for k, v in c.items():
                if k in PREM: reach[day][k] += v
        ev = events_pin(r['fills'])
        for p in PREM:
            evp = ev.get(p, {})
            a0, b0 = reprice_ordered(evp, p, shops) if evp else (0, 0)
            out = {t: [list(e) for e in es] for t, es in evp.items()}
            moved = 0
            for day in range(6, 22):
                car = night[day][0][p]; acc[(p, 'night_us')] += car; acc[(p, 'night_copy')] += night[day][1][p]
                k = min(reach[day][p], car)
                acc[(p, 'reach')] += k
                t0 = (day + 1) * 24
                # our hour-0 lot of p the next morning: move up to k units of it to step t0 - 1 (hour 23), index 0
                left = k
                for e in out.get(t0, []):
                    if e[0] == 0 and e[1] == 'S' and left > 0:
                        take = min(left, e[2]); e[2] -= take; left -= take
                if t0 in out:
                    out[t0] = [e for e in out[t0] if e[2] > 0]
                mv = k - left
                if mv > 0:
                    out.setdefault(t0 - 1, []).insert(0, [0, 'S', mv, -1]); moved += mv
            if moved:
                a1, b1 = reprice_ordered(out, p, shops)
                acc[(p, 'dm')] += (a1 - b1) - (a0 - b0); acc[(p, 'moved')] += moved
                acc[(p, 'us')] += a1 - a0; acc[(p, 'el')] += b1 - b0
    print(f"{n} copy games, days 6-21, per game: premium units carried into the night drop (us / copy), reachable by an h23 drop,")
    print("units of our next hour-0 lot moved to hour 23, and the margin of selling them there first [us / copy]")
    for p in PREM:
        print(f"  {p:10s} night {acc[(p,'night_us')]/n:5.1f} / {acc[(p,'night_copy')]/n:5.1f}   reachable {acc[(p,'reach')]/n:5.1f}   moved {acc[(p,'moved')]/n:5.1f}"
              f"   margin {acc[(p,'dm')]/n:+6.0f} [{acc[(p,'us')]/n:+.0f} / {acc[(p,'el')]/n:+.0f}]")
    print(f"  total margin {sum(acc[(p,'dm')] for p in PREM)/n:+.0f} a game")


if __name__ == '__main__':
    main()
