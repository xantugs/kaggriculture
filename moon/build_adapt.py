"""Build base + ADAPT layer with a divergent profile.
usage: build_adapt.py base.py out.py 'LAYER1,LAYER2' '{"_GLOBAL": value, ...}' [t143] [t359]"""
import sys, re, json
base = open(sys.argv[1], encoding='utf-8').read()
chain = re.findall(r"^(_[A-Za-z0-9_]*PARENT) *= *agent\s*$", base, flags=re.M)
skip = [x for x in sys.argv[3].split(',') if x]
for name in skip:
    assert '_%s_PARENT' % name in chain, name
sets = json.loads(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4] else {}
t143 = float(sys.argv[5]) if len(sys.argv) > 5 else 0.9
t359 = float(sys.argv[6]) if len(sys.argv) > 6 else 0.8
layer = open('adapt_layer.py', encoding='utf-8').read()
cfg = dict(thresh={143: t143, 359: t359}, skip=skip, set=sets, chain=chain)
layer = layer.replace("_AD_CFG = dict(thresh={143: 0.9, 359: 0.8}, skip=[], set={})", '_AD_CFG = %r' % cfg, 1)
for k in sets:
    assert re.search(r'^%s\s*=' % re.escape(k), base, flags=re.M), ('unknown global', k)
src = base.rstrip() + '\n' + layer
compile(src, sys.argv[2], 'exec')
open(sys.argv[2], 'w', encoding='utf-8', newline='\n').write(src)
print('built', sys.argv[2], 'skip', skip, 'set', sets)
