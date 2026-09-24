"""Pinned gate for candidate files on all strong-team games incl. the recent losses. usage: exp_cm.py out.jsonl cand1 cand2 ..."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import pinmulti
if __name__ == '__main__':
    out = sys.argv[1]
    variants = [('default', '../arena/cand/omw_v12.py', {})] + [(os.path.basename(c)[:-3], c, {}) for c in sys.argv[2:]]
    games = pinmulti.load_games(pinmulti.GAME_FILES + ['recent_loss.json'])
    rs = pinmulti.run(games, 144, variants, out, chunk=len(variants))
    pinmulti.summary(rs)
