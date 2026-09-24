import sys, json, collections
sys.argv = ['x']
src = open('il_nb.py', encoding='utf-8').read().replace("if __name__ == '__main__':\n    main()", '')
g = {'__name__': 'nbtest', '__file__': 'il_nb.py'}
exec(compile(src, 'il_nb.py', 'exec'), g)
path = sys.argv[1] if len(sys.argv) > 1 else r'C:/Users/khant/AppData/Local/Temp/claude/c--Users-khant-OneDrive-Documents-ChatGPT-2027-kaggriculture-review-kaggriculture/ff5ea093-34b7-40a1-974d-dfce88715b1d/scratchpad/one.bin'
import shutil, os, tempfile
p = os.path.join(tempfile.gettempdir(), '111810488.json'); shutil.copy(path, p)
rows = g['extract_file'](p)
print('rows', len(rows))
r = json.loads(rows[20]); print(r['team'], r['d'], r['w'], r['D'])
X = g['tile_inputs'](r['c'], r['n'], r['r'], r['G']); print('tile input dim', len(X[0]), 'global dim', len(r['G']))
