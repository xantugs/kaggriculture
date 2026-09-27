"""Build <base> + SES layer inserted before the GOLD controller section.
usage: build_ses.py out_name [json cfg overrides] [base=adapt]   (writes arena/cand/<out_name>.py)"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__)); C = os.path.join(HERE, '..', 'arena', 'cand')
out = sys.argv[1]; ov = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
base = sys.argv[3] if len(sys.argv) > 3 else 'adapt'
lines = open(os.path.join(C, base + '.py'), encoding='utf-8').read().split('\n')
gold = next(i for i, l in enumerate(lines) if l.startswith('# GOLD controller'))
cut = gold - 1 if lines[gold - 1].startswith('# ====') else gold
layer = open(os.path.join(HERE, 'ses_layer.py'), encoding='utf-8').read()
if ov:
    layer = layer.replace("_SES_REPORT = dict(", "_SES_CFG.update(%r)\n_SES_REPORT = dict(" % ov, 1)
src = '\n'.join(lines[:cut]).rstrip() + '\n' + layer.rstrip() + '\n\n\n' + '\n'.join(lines[cut:])
compile(src, out, 'exec')
open(os.path.join(C, out + '.py'), 'w', encoding='utf-8', newline='\n').write(src)
print('built', out, len(src), ov)
