"""Layer ablation on the pinned strong-team worlds: bypass one named chassis layer at a time from day 6.
usage: exp_ablate.py out.jsonl [S]"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pinmulti

SKIP_NEVER = {'_SHOP_PARENT', '_V9_OPENING_PARENT', '_SQ_PARENT', '_WF_PARENT', '_EXPERIMENT_PARENT'}

if __name__ == '__main__':
    out = sys.argv[1]
    S = int(sys.argv[2]) if len(sys.argv) > 2 else 144
    chain = pinmulti.layer_chain(os.path.join(HERE, 'fr2.py'))
    variants = [('default', 'fr2.py', {})]
    for n in chain:
        if n not in SKIP_NEVER:
            variants.append(('skip' + n[:-7], 'fr2.py', {'__skip__': [n]}))
    games = pinmulti.load_games()
    rs = pinmulti.run(games, S, variants, out, chunk=8)
    pinmulti.summary(rs)
