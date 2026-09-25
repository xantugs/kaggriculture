"""Implied ladder rating of each pinned variant from its wins against the opponents' game-time ratings.
P(win) = sigma(delta / 65) (fit on 613 live games, both >= 2300). The recorded live result of the same games is the anchor.
usage: implied.py pin.jsonl eps1.json[,eps2.json...]"""
import sys, json, math, collections

S = 65.0


def sig(x):
    return 1 / (1 + math.exp(-x / S))


def perf(games):
    W = sum(w for _, w in games); lo, hi = 1000.0, 4000.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if sum(sig(mid - r) for r, _ in games) < W:
            lo = mid
        else:
            hi = mid
    R = (lo + hi) / 2
    return R, S / math.sqrt(sum(sig(R - r) * (1 - sig(R - r)) for r, _ in games)), W


if __name__ == '__main__':
    eps = {}
    for f in sys.argv[2].split(','):
        for e in json.load(open(f, encoding='utf-8')):
            eps[e['id']] = e
    R = collections.defaultdict(dict)
    for r in map(json.loads, open(sys.argv[1], encoding='utf-8')):
        R[r['gid']][r['label']] = r
    live, data, ours = [], collections.defaultdict(list), []
    for gid, v in R.items():
        e = eps.get(gid)
        if not e or None in e['score']:
            continue
        p = e['teams'].index('offhand'); ro = e['score'][1 - p]
        live.append((ro, next(iter(v.values()))['rec'] > 0)); ours.append(e['score'][p])
        for lab, r in v.items():
            data[lab].append((ro, r['m'] > 0))
    n = len(live)
    print(f'games {n}  opp mean {sum(r for r, _ in live) / n:.0f}  our live rating mean {sum(ours) / n:.0f}')
    Rl = perf(live)
    print(f'{"recorded":10s} {Rl[2]:3d}/{n} wins -> {Rl[0]:.0f} ± {Rl[1]:.0f}')
    for lab, g in sorted(data.items(), key=lambda kv: -perf(kv[1])[0]):
        x = perf(g)
        print(f'{lab:10s} {x[2]:3d}/{n} wins -> {x[0]:.0f} ± {x[1]:.0f}  (vs recorded {x[0] - Rl[0]:+.0f})')
