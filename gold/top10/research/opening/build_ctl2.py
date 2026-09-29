"""build_ctl2.py NAME ROUTE_JSON PATCH [OPEN_OVERRIDES_JSON] : controller on cfg_p1e with a given step-1 route, the forecast patch
PATCH appended (research/opening/<PATCH>), and mkt_dp_prods += TOMATO when the patch times tomatoes."""
import sys, os, json, subprocess, ast
HERE = os.path.dirname(os.path.abspath(__file__))
KG = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
name, route, patch_name = sys.argv[1], json.loads(sys.argv[2]), sys.argv[3]
over = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}
patch = open(os.path.join(HERE, patch_name), encoding='utf-8').read()
over['route'] = route
extra = {"care_eve_fix": True}
if "'TOMATO')" in patch:
    extra["mkt_dp_prods"] = ["STRAWBERRY", "MILK", "WOOL", "TOMATO"]
subprocess.run([sys.executable, os.path.join(HERE, 'mk.py'), name, os.path.join(HERE, 'cfg_p1e.json'), json.dumps(over), json.dumps(extra)], cwd=KG, check=True, capture_output=True)
p = os.path.join(KG, 'gold', 'top10', 'cands', 'full_OP_%s.py' % name)
src = open(p, encoding='utf-8').read().replace('\r\n', '\n').rstrip('\n') + '\n\n' + patch
ast.parse(src); open(p, 'w', encoding='utf-8').write(src)
print('built', os.path.basename(p), 'extra', extra)
