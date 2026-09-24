"""Build v15b + SX layer. usage: build_sx.py out.py [json cfg overrides]"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
base = open(os.path.join(HERE, '..', 'arena', 'cand', 'omw_v15b.py'), encoding='utf-8').read()
layer = open(os.path.join(HERE, 'sx_layer.py'), encoding='utf-8').read()
ov = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
if ov:
    layer = layer.replace("_SX_REPORT = dict(", "_SX_CFG.update(%r)\n_SX_REPORT = dict(" % ov, 1)
if 'import collections' not in base:
    layer = 'import collections\n' + layer
src = base.rstrip() + '\n' + layer
compile(src, sys.argv[1], 'exec')
open(sys.argv[1], 'w', encoding='utf-8', newline='\n').write(src)
print('built', sys.argv[1], len(src), ov)
