"""Pinned strong-team gate: v13f vs v15a (SR 14, R51 crops 1-4-6/1-4-4) and v15b (+ GLUTH_H 8).
usage: exp_v15.py out.jsonl S"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import pinmulti
if __name__ == '__main__':
    out, S = sys.argv[1], int(sys.argv[2])
    C = '../arena/cand/'
    variants = [('v13f', C + 'omw_v13f.py', {}), ('v15a', C + 'omw_v15a.py', {}), ('v15b', C + 'omw_v15b.py', {})]
    games = pinmulti.load_games(pinmulti.GAME_FILES + ['recent_loss.json'])
    print('games', len(games), flush=True)
    rs = pinmulti.run(games, S, variants, out, chunk=3)
    pinmulti.summary(rs)
