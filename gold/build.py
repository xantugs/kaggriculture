"""Build a candidate: base chassis + gold controller with parameter overrides.
usage: build.py out.py '{"start": 240}' [base.py]"""
import sys, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
out = sys.argv[1]
over = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
base = sys.argv[3] if len(sys.argv) > 3 else os.path.join(HERE, 'base_v15a_adapt.py')
src = open(base, encoding='utf-8').read()
ctl = open(os.path.join(HERE, 'ctl.py'), encoding='utf-8').read()
if over:
    ctl = ctl.replace('_GC_CROPS = {', 'GC_P.update(%r)\n_GC_CROPS = {' % (over,), 1)
open(out, 'w', encoding='utf-8').write(src.rstrip('\n') + '\n\n' + ctl)
print('built', out, os.path.getsize(out), 'bytes', over)
