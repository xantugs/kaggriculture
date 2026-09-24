"""Pinned strong-team gate: v12 vs v13f (other session's tuned v12) and single-change ablations.
usage: exp_v13.py out.jsonl S"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import pinmulti
if __name__ == '__main__':
    out, S = sys.argv[1], int(sys.argv[2])
    C = '../arena/cand/'
    variants = [('v12', C + 'omw_v12.py', {}), ('v13f', C + 'omw_v13f.py', {})] + \
               [(k, C + 'abl_%s.py' % k, {}) for k in ('tomcash', 'inw3', 'infert', 'inval', 'carrot', 'herd', 'gluth')]
    games = pinmulti.load_games(pinmulti.GAME_FILES + ['recent_loss.json'])
    print('games', len(games), flush=True)
    rs = pinmulti.run(games, S, variants, out, chunk=3)
    pinmulti.summary(rs)
