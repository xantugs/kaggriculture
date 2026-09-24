"""Diff a mirror opponent's actions against ours in recorded games where both farms match at day 15.
Counts, from day D on, unit commands and market orders that differ, grouped by (ours -> theirs) kind.
usage: diffmirror.py games.json [D=15]"""
import sys, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
from classify import sig, sim


def kind(a):
    if not a:
        return 'PASS'
    op = a[0]
    if op in ('NORTH', 'SOUTH', 'EAST', 'WEST'):
        return 'MOVE'
    if op in ('PLANT', 'PICKUP', 'PLACE'):
        return op + ':' + str(a[1]) if len(a) > 1 else op
    return op


def main():
    f = sys.argv[1]; D = int(sys.argv[2]) if len(sys.argv) > 2 else 15
    import lean, pinned
    games = json.load(open(os.path.join(HERE, f), encoding='utf-8'))
    tot_units = collections.Counter(); tot_mkt = collections.Counter(); plant_days = collections.Counter(); n = 0
    per_game = []
    for d in games:
        names = d['info']['TeamNames']; P = names.index('offhand'); O = 1 - P
        snap = {}
        def w(obs, cfg=None):
            if obs['step'] == 359:
                snap['s'] = sim(sig(obs['farms'][P]), sig(obs['farms'][O]))
            return pinned._tape(d['acts'], 0)(obs, cfg)
        lean.play(None, None, d['info']['seed'], agent_objs=[w, pinned._tape(d['acts'], 1)], max_steps=360)
        if snap.get('s', 0) < 0.97:
            continue
        n += 1
        diffs = 0
        for t in range(D * 24, 719):
            a = d['acts'][t + 1][P] if t + 1 < len(d['acts']) else None
            b = d['acts'][t + 1][O] if t + 1 < len(d['acts']) else None
            if not isinstance(a, dict) or not isinstance(b, dict):
                continue
            ua = [a.get('farmer')] + list(a.get('hands') or []); ub = [b.get('farmer')] + list(b.get('hands') or [])
            for i in range(max(len(ua), len(ub))):
                x = kind(ua[i]) if i < len(ua) else 'NONE'; y = kind(ub[i]) if i < len(ub) else 'NONE'
                if x != y:
                    tot_units[(x, y)] += 1; diffs += 1
                if y.startswith('PLANT:') and x != y:
                    plant_days[(t // 24, y)] += 1
            ma = collections.Counter((o[0], o[1] if len(o) > 1 else '') for o in (a.get('market') or []) if o)
            mb = collections.Counter((o[0], o[1] if len(o) > 1 else '') for o in (b.get('market') or []) if o)
            for k in set(ma) | set(mb):
                if ma[k] != mb[k]:
                    tot_mkt[(k, 'them_more' if mb[k] > ma[k] else 'us_more')] += 1
        per_game.append((names[O], d['rewards'][P] - d['rewards'][O], diffs))
    print(n, 'games identical at day 15')
    for g in per_game: print('  ', g)
    print('unit command differences (ours -> theirs), top:')
    for k, v in tot_units.most_common(25): print(f"   {k[0]:>16s} -> {k[1]:<16s} {v / max(1, n):7.1f}/game")
    print('their extra plantings by day:')
    for k, v in sorted(plant_days.items()): print('   day', k[0], k[1], round(v / max(1, n), 1))
    print('market order differences:')
    for k, v in tot_mkt.most_common(20): print('  ', k, round(v / max(1, n), 1))


if __name__ == '__main__':
    main()
