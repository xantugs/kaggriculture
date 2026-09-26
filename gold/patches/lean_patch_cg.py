"""Add the day-0 cash guard (cash_guard_min 5) to a lean build: lean_patch_cg.py in.py out.py"""
import sys
src = open(sys.argv[1], encoding='utf-8').read()
helper = '''def _gc_cash_guard(obs, action):
    me = int(obs['player']); farm = obs['farms'][me]
    cash = float(farm['money']); nh = int(farm.get('hires_today', 0) or 0)
    px = obs['market']['prices']; floor = 5.0
    out = []; trimmed = 0
    for o in action.get('market') or []:
        if not isinstance(o, list) or not o:
            out.append(o); continue
        op = o[0]
        if op == 'HIRE':
            cash -= _gc_fib(nh); nh += 1
        elif op == 'BUY_ANIMAL' and len(o) >= 3:
            cash -= _GC_ANIM.get(o[1], {}).get('cost', 0) * int(o[2])
        elif op == 'BUY_PRODUCT' and len(o) >= 3:
            cash -= (float(px.get(o[1], 0)) + 1.0) * int(o[2])
        elif op == 'BUY_SEED' and len(o) >= 3 and o[1] in _GC_CROPS:
            unit = float(_GC_CROPS[o[1]]['seed']); n = int(o[2])
            k = n
            while k > 0 and cash - unit * k < floor:
                k -= 1
            if k < n:
                trimmed += n - k
                if k <= 0:
                    continue
                o = [o[0], o[1], k]
            cash -= unit * k
        out.append(o)
    if trimmed:
        _GC_REPORT['gc_cash_guard'] = _GC_REPORT.get('gc_cash_guard', 0) + trimmed
        action = dict(action); action['market'] = out
    return action


'''
a = 'def _gc_sells_first('
assert src.count(a) == 1
src = src.replace(a, helper + a, 1)
b = "        if step >= 24 * GC_P['chassis_floor_from']:\n"
assert src.count(b) == 1
call = ("        if step < 24 and isinstance(action, dict) and action.get('market'):\n"
        "            try:\n"
        "                action = _gc_cash_guard(observation, action)\n"
        "            except Exception:\n"
        "                pass\n")
src = src.replace(b, call + b, 1)
open(sys.argv[2], 'w', encoding='utf-8').write(src)
print('patched', sys.argv[2])
