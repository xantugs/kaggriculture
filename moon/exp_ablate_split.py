"""Layer ablation by opponent type: v15b with each chassis layer bypassed, on per-game files of games vs 2800+ teams.
usage: exp_ablate_split.py out.jsonl S [base_file] [layers(comma)|all]"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import pinmulti
if __name__ == '__main__':
    out, S = sys.argv[1], int(sys.argv[2])
    base = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] != '-' else os.path.join(HERE, '..', 'arena', 'cand', 'omw_v15b.py')
    chain = pinmulti.layer_chain(base)
    layers = chain[1:] if len(sys.argv) < 5 or sys.argv[4] == 'all' else ['_%s_PARENT' % x for x in sys.argv[4].split(',')]
    variants = [('base', base, {})] + [('skip' + l[:-7], base, {'__skip__': [l]}) for l in layers]
    games = [(f, 0) for f in json.load(open(os.path.join(HERE, 'g2800_list.json')))]
    print('games', len(games), 'variants', len(variants), flush=True)
    pinmulti.run(games, S, variants, out, chunk=12)
