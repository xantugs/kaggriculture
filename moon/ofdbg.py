import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
import oracle_fert
fn = 'g2800/112495873.json'
path = os.path.join(HERE, '..', 'arena', 'cand', 'omw_ad_a2.py')
import lean
orig_play = lean.play
def play(*a, **k):
    r = orig_play(*a, **k)
    print({x: (v if not isinstance(v, (list, dict)) or len(str(v)) < 300 else str(v)[:300]) for x, v in r.items()})
    return r
lean.play = play
gid, out = oracle_fert.job((fn, path, 96, 5, 28, {'WHEAT', 'CARROT', 'STRAWBERRY'}, [0, 4], 200, 30, 'best'))
print(out)
