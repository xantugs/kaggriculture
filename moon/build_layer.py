"""Append a layer file to a base agent, with optional CFG overrides. usage: build_layer.py base.py layer.py out.py [CFGNAME json]"""
import sys, json
base = open(sys.argv[1], encoding='utf-8').read(); layer = open(sys.argv[2], encoding='utf-8').read()
if len(sys.argv) > 5:
    name, ov = sys.argv[4], json.loads(sys.argv[5])
    marker = name + ' = dict('
    i = layer.index(marker); j = i + len(marker) - 1; depth = 0
    while True:                      # find the closing bracket of the (possibly multi-line) dict(...)
        ch = layer[j]
        if ch in '([{':
            depth += 1
        elif ch in ')]}':
            depth -= 1
            if depth == 0:
                break
        j += 1
    j = layer.index('\n', j)
    layer = layer[:j + 1] + '%s.update(%r)\n' % (name, ov) + layer[j + 1:]
src = base.rstrip() + '\n' + layer
compile(src, sys.argv[3], 'exec')
open(sys.argv[3], 'w', encoding='utf-8', newline='\n').write(src)
print('built', sys.argv[3])
