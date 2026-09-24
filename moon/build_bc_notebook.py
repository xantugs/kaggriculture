"""Assemble the behaviour-cloning Kaggle script. usage: build_bc_notebook.py out.py teachers(|-sep) [max_games] [epochs] [hidden] [wins_only] [selfplay_games] [selfplay_min_step]"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
out = sys.argv[1]
teachers = [t for t in sys.argv[2].split('|') if t]
max_games = int(sys.argv[3]) if len(sys.argv) > 3 else 1200
epochs = int(sys.argv[4]) if len(sys.argv) > 4 else 6
hidden = int(sys.argv[5]) if len(sys.argv) > 5 else 64
wins_only = int(sys.argv[6]) if len(sys.argv) > 6 else 0
selfplay = int(sys.argv[7]) if len(sys.argv) > 7 else 0
sp_min = int(sys.argv[8]) if len(sys.argv) > 8 else 0
import json, zlib, base64
v12_blob = base64.b85encode(zlib.compress(open(os.path.join(HERE, '..', 'arena', 'cand', 'omw_v12.py'), 'rb').read(), 9)).decode() if selfplay else ''
head = '''# Kaggriculture behaviour cloning of top teams: per-unit commands and market orders.
import subprocess, sys, os, json
import importlib.metadata as _md
try:
    _v = _md.version('kaggle-environments')
except Exception:
    _v = None
print('preinstalled kaggle-environments', _v, flush=True)
if _v != '1.32.7':
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '--force-reinstall', '--no-deps', 'kaggle-environments==1.32.7'], check=False)
TEACHERS = %r
MAX_GAMES = %d
EPOCHS = %d
HIDDEN = %d
WINS_ONLY = %d
SELFPLAY = %d
SP_MIN_STEP = %d
if SELFPLAY:
    import zlib as _z, base64 as _b
    open('/kaggle/working/v12.py', 'wb').write(_z.decompress(_b.b85decode(%r)))
''' % (teachers, max_games, epochs, hidden, wins_only, selfplay, sp_min, v12_blob)
feat = open(os.path.join(HERE, 'feat.py'), encoding='utf-8').read().split('"""', 2)[2]
core = (open(os.path.join(HERE, 'bc_codec.py'), encoding='utf-8').read().split('"""', 2)[2] + '\n'
        + open(os.path.join(HERE, 'bc_core.py'), encoding='utf-8').read().split('"""', 2)[2])
lean_src = open(os.path.join(HERE, '..', 'arena', 'lean.py'), encoding='utf-8').read().split('"""', 2)[2].split('if __name__ == "__main__":')[0]
body = open(os.path.join(HERE, 'bc_body.py'), encoding='utf-8').read()
src = head + '\n# ---- feat ----\n' + feat + '\n# ---- bc core ----\n' + core + '\n# ---- lean runner ----\n' + lean_src + body
open(out, 'w', encoding='utf-8').write(src)
compile(src, out, 'exec')
print('built', out, len(src))
