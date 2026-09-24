"""Replay v14's ladder losses from step S with several versions in our seat (opponent's recorded moves)."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import pinmulti
if __name__ == '__main__':
    out, S = sys.argv[1], int(sys.argv[2])
    C = os.path.join(HERE, '..', 'arena', 'cand')
    variants = [(v, os.path.join(C, 'omw_%s.py' % v), {}) for v in ('v15a', 'v13f', 'v15b', 'v12')]
    games = pinmulti.load_games(['v14_losses.json'])
    print('games', len(games), flush=True)
    rs = pinmulti.run(games, S, variants, out, chunk=4)
    import collections
    by = collections.defaultdict(dict)
    for r in rs: by[r['gid']][r['label']] = (r['m'], r['rec'], r['rec_ok'])
    for g, d in by.items():
        print(g, 'recorded', d['v15a'][1], 'rec_ok', d['v15a'][2], ' '.join(f"{k} {v[0]:+.0f}" for k, v in d.items()))
