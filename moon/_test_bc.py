import sys, json, shutil, os, tempfile
src = open('bc_nb.py', encoding='utf-8').read().replace("if __name__ == '__main__':\n    main()", '')
g = {'__name__': 'bctest'}
try:
    exec(compile(src, 'bc_nb.py', 'exec'), g)
except ModuleNotFoundError as e:
    print('local import limit:', e)
p = os.path.join(tempfile.gettempdir(), '111810488.json')
print('header teams', g['header_teams'](p) if 'header_teams' in g else None)
