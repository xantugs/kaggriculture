import sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import pinmulti
if __name__ == '__main__':
    out, S = sys.argv[1], int(sys.argv[2]); C = os.path.join(HERE, '..', 'arena', 'cand')
    variants = [('base', os.path.join(C, 'omw_v15b.py'), {})] + [(c, os.path.join(C, c + '.py'), {}) for c in sys.argv[3].split(',')]
    pinmulti.run(pinmulti.load_games(['strong2800.json']), S, variants, out, chunk=len(variants))
