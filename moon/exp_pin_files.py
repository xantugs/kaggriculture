"""Split gate on per-game files: base v15b vs candidate agent files from step S. usage: exp_pin_files.py out.jsonl S cand1,cand2 (names under arena/cand, no .py)"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import pinmulti
if __name__ == '__main__':
    out, S = sys.argv[1], int(sys.argv[2]); C = os.path.join(HERE, '..', 'arena', 'cand')
    variants = [('base', os.path.join(C, 'omw_v15b.py'), {})] + [(c, os.path.join(C, c + '.py'), {}) for c in sys.argv[3].split(',')]
    games = [(f, 0) for f in json.load(open(os.path.join(HERE, 'g2800_list.json')))]
    pinmulti.run(games, S, variants, out, chunk=len(variants))
