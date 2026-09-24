"""v12 + rival-type switch. usage: build_cm.py out.py 'LAYER1,LAYER2' [t143] [t359]
LAYER names without _PARENT, e.g. V9_RACE,R36_SALE,V92_P"""
import sys, os, re
here = os.path.dirname(os.path.abspath(__file__))
base = open(os.environ.get('CM_BASE') or os.path.join(here, '..', 'arena', 'cand', 'omw_v12.py'), encoding='utf-8').read()
chain = re.findall(r"^(_[A-Za-z0-9_]*PARENT) *= *agent\s*$", base, flags=re.M)
skip = []
for name in sys.argv[2].split(','):
    p = '_%s_PARENT' % name
    k = chain.index(p)
    skip.append((p, chain[k + 1]))
t143 = float(sys.argv[3]) if len(sys.argv) > 3 else 0.9
t359 = float(sys.argv[4]) if len(sys.argv) > 4 else 0.8
layer = open(os.path.join(here, 'cm_layer.py'), encoding='utf-8').read().replace('__CM_SKIP__', repr(skip)).replace('__CM_THRESH__', repr({143: t143, 359: t359}))
open(sys.argv[1], 'w', encoding='utf-8').write(base.rstrip() + '\n' + layer)
print('built', sys.argv[1], skip, t143, t359)
