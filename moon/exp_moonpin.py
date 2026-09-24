"""Pinned strong-opponent gate (games vs 2800+ teams): v15b vs moon candidates from step S. usage: exp_moonpin.py out.jsonl S cand1[,cand2]"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import pinmulti, tune
if __name__ == '__main__':
    out, S = sys.argv[1], int(sys.argv[2])
    C = os.path.join(HERE, '..', 'arena', 'cand')
    variants = [('base', os.path.join(C, 'omw_v15b.py'), {})] + [(c, os.path.join(C, c + '.py'), {}) for c in sys.argv[3].split(',')]
    games = pinmulti.load_games(['strong2800.json'])
    print('games', len(games), flush=True)
    pinmulti.run(games, S, variants, out, chunk=len(variants))
    tune.summarize(out)
