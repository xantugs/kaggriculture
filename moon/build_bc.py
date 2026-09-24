"""v12 + behaviour-cloned policy. usage: build_bc.py out.py model.npz [start_step]"""
import sys, os, zlib, base64
here = os.path.dirname(os.path.abspath(__file__))
base = open(os.path.join(here, '..', 'arena', 'cand', 'omw_v12.py'), encoding='utf-8').read()
src = '\n\n'.join(open(os.path.join(here, f), encoding='utf-8').read() for f in ('feat.py', 'bc_codec.py', 'bc_core.py'))
w = base64.b85encode(zlib.compress(open(sys.argv[2], 'rb').read(), 9)).decode()
start = int(sys.argv[3]) if len(sys.argv) > 3 else 0
layer = open(os.path.join(here, 'bc_layer.py'), encoding='utf-8').read()
layer = layer.replace('__BC_SRC__', repr(src)).replace('__BC_W__', repr(w)).replace('__BC_START__', str(start))
out = base.rstrip() + '\n' + layer
open(sys.argv[1], 'w', encoding='utf-8').write(out)
compile(out, sys.argv[1], 'exec')
print('built', sys.argv[1], len(out))
