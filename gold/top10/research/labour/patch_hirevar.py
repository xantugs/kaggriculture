"""Research-only counterfactual builds of lean sf8's hire search (measurement probes, not submissions).
usage: patch_hirevar.py in.py out.py VARIANT
  capN     hard cap of N hands on non-final days (sf8: 15)
  wtK      hands above K priced at full wage: score = -pen - 0.6*cost - 0.4*max(0, cost - cum(K))
  ovfV     end-of-day overflow priced at V dollars a unit in the hire search (sf8: 100)
Variants combine with '+', e.g. wt11+ovf40."""
import sys
src = open(sys.argv[1], encoding='utf-8').read()
FIB = [1, 1]
while len(FIB) < 30:
    FIB.append(FIB[-1] + FIB[-2])
CUM = [sum(FIB[:n]) for n in range(30)]
for var in sys.argv[3].split('+'):
    if var.startswith('cap'):
        n = int(var[3:])
        a = "        hi = GC_P['max_hands_final'] if final else 15\n"
        assert src.count(a) == 1
        src = src.replace(a, "        hi = GC_P['max_hands_final'] if final else %d\n" % n)
    elif var.startswith('wt'):
        k = int(var[2:])
        a = "            score = -pen - 0.6 * cost\n"
        assert src.count(a) == 1
        src = src.replace(a, "            score = -pen - 0.6 * cost - 0.4 * max(0, cost - %d)\n" % CUM[k])
    elif var.startswith('ovf'):
        v = float(var[3:])
        a = "                pen += ovf * 100.0 + popped\n"
        assert src.count(a) == 1
        src = src.replace(a, "                pen += ovf * %.1f + popped\n" % v)
    else:
        raise SystemExit('unknown variant ' + var)
open(sys.argv[2], 'w', encoding='utf-8').write(src)
print('ok', sys.argv[3])
