"""build_ctl.py NAME '{overrides}' : controller variant on cfg_p1e with the wool forecast patch appended, in two forms:
full_OP_<NAME>r.py (routed like PFc: tape vs C2S3 and chassis) and full_OP_<NAME>p.py (pure controller, route null)."""
import sys, os, json, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
KG = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
PY = sys.executable
name, over = sys.argv[1], json.loads(sys.argv[2])
patch = open(os.path.join(HERE, 'patch_phase_linear_wool.py'), encoding='utf-8').read()
for suffix, route in (('r', {"tape": ["C2S3", "chassis"], "fine": True, "chassis_min": 2550}), ('p', {"tape": [], "fine": True, "chassis_min": 2550})):
    o = dict(over); o['route'] = route
    nm = name + suffix
    subprocess.run([PY, os.path.join(HERE, 'mk.py'), nm, os.path.join(HERE, 'cfg_p1e.json'), json.dumps(o), json.dumps({"care_eve_fix": True})],
                   cwd=KG, check=True, capture_output=True)
    p = os.path.join(KG, 'gold', 'top10', 'cands', 'full_OP_%s.py' % nm)
    src = open(p, encoding='utf-8').read().replace('\r\n', '\n')
    open(p, 'w', encoding='utf-8').write(src.rstrip('\n') + '\n\n' + patch)
    import ast; ast.parse(open(p, encoding='utf-8').read())
    print('built', os.path.basename(p))
