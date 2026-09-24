"""Build a candidate: chassis (v12) + moon planner layer, with optional parameter overrides.
usage: build.py out.py [json-overrides]   (overrides may include "start" and "il_model": path to il_model.json)"""
import sys, json, os, zlib, base64
here = os.path.dirname(os.path.abspath(__file__))
base = open(os.environ.get('MOON_BASE') or os.path.join(here, '..', 'arena', 'cand', 'omw_v12.py'), encoding='utf-8').read()
layer = open(os.path.join(here, 'moon.py'), encoding='utf-8').read()
ov = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
prelude = ''
model_path = ov.pop('il_model', None)
if model_path:
    src = open(os.path.join(here, 'feat.py'), encoding='utf-8').read() + '\n\n' + open(os.path.join(here, 'il_infer.py'), encoding='utf-8').read()
    blob = base64.b85encode(zlib.compress(open(model_path, 'rb').read(), 9)).decode()
    prelude = '\n# ---- imitation planner model (executed in its own namespace by moon) ----\n_IL_SRC = %r\n_IL_MODEL_BLOB = %r\n' % (src, blob)
    ov.setdefault('il', True)
start = ov.pop('start', 144)
layer = layer.replace('_MOON = Moon()', 'MOON_P.update(%r)\nMOON_START = %r\n_MOON = Moon()' % (ov, start), 1)
open(sys.argv[1], 'w', encoding='utf-8').write(base.rstrip() + '\n\n' + prelude + '\n\n' + layer)
print('built', sys.argv[1], len(base) + len(prelude) + len(layer))
