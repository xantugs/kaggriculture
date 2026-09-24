"""Build a v9 variant: optional string patches on the chassis + optional extra layers (inserted before the day-28
pre-emption).  usage: build_var.py out.py '{"patches": [[old, new], ...], "layers": [[file, placeholder, cfg], ...]}'"""
import sys, json
out = sys.argv[1]; spec = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
src = open('pub/omw.py', encoding='utf-8').read()
for old, new in spec.get('patches', []):
    assert src.count(old) == 1, old
    src = src.replace(old, new)
v9 = open('layers/v9_layer.py', encoding='utf-8').read()
for old, new in spec.get('v9patches', []):
    assert v9.count(old) == 1, old
    v9 = v9.replace(old, new)
marker = '# ---- pre-empt the day-28 evening sale'
i = v9.index(marker)
extra = ''
for f, ph, cfg in spec.get('layers', []):
    extra += open(f, encoding='utf-8').read().replace(ph, repr(cfg)) + '\n'
tail = ''
for f, ph, cfg in spec.get('tail', []):
    tail += '\n' + open(f, encoding='utf-8').read().replace(ph, repr(cfg)) + '\n'
open(out, 'w', encoding='utf-8').write(src + v9[:i] + extra + v9[i:] + tail)
print(out)
