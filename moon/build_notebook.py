"""Assemble the single-file Kaggle training script: engine install, feat.py, extraction, training.
usage: build_notebook.py out.py [max_games] [epochs] [hidden] [min_day]"""
import sys, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
out = sys.argv[1]
max_games = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
epochs = int(sys.argv[3]) if len(sys.argv) > 3 else 30
hidden = int(sys.argv[4]) if len(sys.argv) > 4 else 64
min_day = int(sys.argv[5]) if len(sys.argv) > 5 else 6
teams = sys.argv[6] if len(sys.argv) > 6 else ''
rows_src = sys.argv[7] if len(sys.argv) > 7 else ''

head = '''# Kaggriculture imitation planner: extract tile-job labels from top-tier episodes, train a per-tile network.
import subprocess, sys, os, json
import importlib.metadata as _md
try:
    _v = _md.version('kaggle-environments')
except Exception:
    _v = None
print('preinstalled kaggle-environments', _v, flush=True)
if _v != '1.32.7':
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '--force-reinstall', '--no-deps', 'kaggle-environments==1.32.7'], check=False)
print('now', _md.version('kaggle-environments'), flush=True)
MAX_GAMES = %d
EPOCHS = %d
HIDDEN = %d
MIN_DAY = %d
TEAMS = %r
ROWS_SRC = %r
''' % (max_games, epochs, hidden, min_day, [t for t in teams.split('|') if t], rows_src)

feat = open(os.path.join(HERE, 'feat.py'), encoding='utf-8').read()
feat = feat.split('"""', 2)[2]  # drop module docstring

ex = open(os.path.join(HERE, 'extract.py'), encoding='utf-8').read()
ex = ex.split('"""', 2)[2]
ex = ex.split("if __name__ == '__main__':")[0]
ex = ex.replace("sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))\nimport feat\n", '')
ex = ex.replace('feat.', '')
# the notebook has no local lean harness: use kaggle_environments directly through a minimal runner
lean_src = open(os.path.join(HERE, '..', 'arena', 'lean.py'), encoding='utf-8').read()
lean_src = lean_src.split('"""', 2)[2].split('if __name__ == "__main__":')[0]
ex = ex.replace('    import lean\n', '')
ex = ex.replace('lean.play(', 'play(')

body = open(os.path.join(HERE, 'il_body.py'), encoding='utf-8').read()
src = head + '\n# ---- feat.py ----\n' + feat + '\n# ---- lean runner ----\n' + lean_src + '\n# ---- extraction ----\n' + ex + body
open(out, 'w', encoding='utf-8').write(src)
compile(src, out, 'exec')
print('built', out, len(src), 'chars')
