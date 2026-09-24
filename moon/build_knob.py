"""Knob-ified copy of v13f: the inline thresholds v13 tuned become module globals (`_K_*`), so the pinned
harness can override them per variant like any other layer constant. Defaults keep v13's values.
usage: build_knob.py [src] [out]"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
C = os.path.join(HERE, '..', 'arena', 'cand')
src_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(C, 'omw_v13f.py')
out_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(C, 'omw_v13k.py')
src = open(src_path, encoding='utf-8', newline='').read().replace('\r\n', '\n')
REPS = [("farm['money'] < 14969", "farm['money'] < _K_V219_CASH"),
        ("new_gross-1.761*fertilizer", "new_gross-_K_R51_FERT*fertilizer"),
        ("if value<1.252*cost+71.3 or farm['money']<total_cost+cost+3000", "if value<_K_R68_A*cost+_K_R68_B or farm['money']<total_cost+cost+_K_R68_RES"),
        ("if hour not in (1,2,3) or not 12<=day<=28:return action", "if hour not in _K_R51_HOURS or not _K_R51_D0<=day<=_K_R51_D1:return action"),
        ("if day in (12,18) or any(p.get('committed')", "if day in _K_R51_SKIP or any(p.get('committed')"),
        ("if q<3 or len(action.get('market',[]))+2+i>10", "if q<_K_R51_QMIN or len(action.get('market',[]))+2+i>10")]
DEFAULTS = ("_K_V219_CASH = 14969\n_K_R51_FERT = 1.761\n_K_R68_A = 1.252\n_K_R68_B = 71.3\n_K_R68_RES = 3000\n"
            "_K_R51_HOURS = (1, 2, 3)\n_K_R51_D0 = 12\n_K_R51_D1 = 28\n_K_R51_SKIP = (12, 18)\n_K_R51_QMIN = 3\n")
for a, b in REPS:
    assert src.count(a) == 1, (a, src.count(a))
    src = src.replace(a, b)
lines = src.split('\n')
k = max(i for i, l in enumerate(lines) if l.startswith('from __future__')) + 1
src = '\n'.join(lines[:k]) + '\n' + DEFAULTS + '\n'.join(lines[k:])
compile(src, out_path, 'exec')
open(out_path, 'w', encoding='utf-8', newline='\n').write(src)
print('wrote', out_path, len(src))
