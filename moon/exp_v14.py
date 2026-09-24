"""Pinned strong-team gate: v13f vs v14a (GLUTH_H 8, SR_MARGIN 14) and v14b (+ HD2_CARE 0.6).
usage: exp_v14.py out.jsonl S"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import pinmulti
if __name__ == '__main__':
    out, S = sys.argv[1], int(sys.argv[2])
    C = '../arena/cand/'
    variants = [('v13f', C + 'omw_v13f.py', {}), ('v14a', C + 'omw_v14a.py', {}), ('v14b', C + 'omw_v14b.py', {})]
    games = pinmulti.load_games(pinmulti.GAME_FILES + ['recent_loss.json'])
    print('games', len(games), flush=True)
    rs = pinmulti.run(games, S, variants, out, chunk=3)
    pinmulti.summary(rs)
