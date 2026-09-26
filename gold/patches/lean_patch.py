"""Apply the sells-first changes to the lean m5 file with the chosen options hardcoded.
usage: lean_patch.py lean_in.py out.py '{"sort": true, "slots": true, "slots1": false, "div_sort": false, "order": []}'"""
import sys, json
src = open(sys.argv[1], encoding='utf-8').read()
opt = json.loads(sys.argv[3])
helper = '''_SF_SORT = %r
_SF_ORDER = %r


def _gc_sells_first(orders, inv=None, due=None):
    """Our SELL orders ahead of hires and purchases (the engine runs both farms' lists index by index: a lot at a lower
    index than the rival's sells first). A SELL stays behind a purchase of the same item listed before it. With the
    town's book, the SELLs go rival-due first, then by the price drop each lot causes."""
    orders = list(orders or [])
    if len(orders) > 10:
        return _gc_sells_first(orders[:10], inv, due) + orders[10:]
    front, rest, bought = [], [], set()
    for o in orders:
        if isinstance(o, list) and len(o) >= 2 and o[0] == 'BUY_PRODUCT':
            bought.add(o[1])
        if isinstance(o, list) and len(o) >= 2 and o[0] == 'SELL' and o[1] not in bought:
            front.append(o)
        else:
            rest.append(o)
    if _SF_ORDER and inv is not None and len(front) > 1:
        rank = {p: i for i, p in enumerate(_SF_ORDER)}
        return sorted(front, key=lambda o: rank.get(o[1], 99)) + rest
    if _SF_SORT and inv is not None and len(front) > 1:
        def impact(o):
            try:
                p = o[1]; n = min(100, int(o[2]) if len(o) > 2 else 1)
                if n <= 0 or p not in _GC_MKT:
                    return 0.0
                i0 = int(inv[p])
                return float(n) * (_gc_price(p, i0) - _gc_price(p, i0 + n))
            except Exception:
                return 0.0
        due = due or set()
        front = sorted(front, key=lambda o: (0 if o[1] in due else 1, -impact(o)))
    return front + rest


''' % (bool(opt.get('sort')), list(opt.get('order') or []))
a = 'def _gc_fib(n):\n'
assert src.count(a) == 1; src = src.replace(a, helper + a, 1)
a = '''    def _market(self, obs, shed, carried, hour, day):
        step = int(obs['step'])
'''
assert src.count(a) == 1
src = src.replace(a, '''    def _market(self, obs, shed, carried, hour, day):
        return _gc_sells_first(self._market0(obs, shed, carried, hour, day), obs['market']['inventory'], set(getattr(self, '_due', set()) or set()))

    def _market0(self, obs, shed, carried, hour, day):
        step = int(obs['step'])
''', 1)
if opt.get('slots'):
    a = '''        if hour == 0:
            fixed = list(self.orders0)
            h0 = max(0, min(self.hires_planned, 10 - len(fixed)))
            self.hires_left = self.hires_planned - h0
            orders = fixed + [['HIRE']] * h0
            have = {o[1] for o in fixed if o and o[0] == 'SELL'}
            orders += [o for o in prem if o[1] not in have and o[1] in self._due]
            return orders[:10]
'''
    assert src.count(a) == 1
    src = src.replace(a, '''        if hour == 0:
            fixed = list(self.orders0)
            have = {o[1] for o in fixed if o and o[0] == 'SELL'}
            due = [o for o in prem if o[1] not in have and o[1] in self._due]
            h0 = max(0, min(self.hires_planned, 10 - len(fixed) - len(due)))
            self.hires_left = self.hires_planned - h0
            orders = fixed + [['HIRE']] * h0 + due
            return orders[:10]
''', 1)
if opt.get('slots1'):
    a = '''            h1 = min(self.hires_left, 10 - len(self.orders1))
'''
    assert src.count(a) == 1
    src = src.replace(a, '''            ps = [o for o in prem if o and o[0] == 'SELL']
            h1 = max(0, min(self.hires_left, 10 - len(self.orders1) - len(ps)))
''', 1)
a = '''        if step >= 24 * GC_P['chassis_floor_from']:
            try:
                action = _gc_chassis_floor(observation, action)
'''
assert src.count(a) == 1
if opt.get('div_sort'):
    chassis = '''        if isinstance(action, dict) and action.get('market'):
            try:
                action = dict(action)
                if _AD_STATE.get('off'):
                    action['market'] = _gc_sells_first(action['market'], observation['market']['inventory'])
                else:
                    action['market'] = _gc_sells_first(action['market'])
            except Exception:
                pass
'''
else:
    chassis = '''        if isinstance(action, dict) and action.get('market'):
            try:
                action = dict(action); action['market'] = _gc_sells_first(action['market'])
            except Exception:
                pass
'''
src = src.replace(a, chassis + a, 1)
if opt.get('d29'):
    a = "            if p in GC_P['mkt_dp_prods'] and (not last) and (day <= 28) and (day >= 0):\n"
    assert src.count(a) == 1
    src = src.replace(a, "            if p in GC_P['mkt_dp_prods'] and (day >= 0) and ((not last and day <= 28) or (day == 29 and step < 716)):\n", 1)
if 'final_sell0' in opt:
    a = "        if final and 3 > 0:\n            sell0 = sell0[:max(3, 1 if need_room > 0 else 0)]\n"
    assert src.count(a) == 1
    v = int(opt['final_sell0'])
    src = src.replace(a, "        if final and %d > 0:\n            sell0 = sell0[:max(%d, 1 if need_room > 0 else 0)]\n" % (v, v), 1)
if 'final_cap' in opt:
    a = "            fc = None if d28r else 19\n"
    assert src.count(a) == 1
    src = src.replace(a, "            fc = None if d28r else %d\n" % int(opt['final_cap']), 1)
if opt.get('div29'):
    # day-29 settings back to GC_P lookups, switched on the divergent path only (div_over)
    a = "'melon_last': 19, 'melon_age': 10}, 'max_sell0': 0"
    assert src.count(a) == 1
    src = src.replace(a, "'melon_last': 19, 'melon_age': 10, 'mkt_dp_d29': True, 'final_sell0': 0, 'final_cap': 21}, 'max_sell0': 0", 1)
    a = "_GC_CROPS = {"
    assert src.count(a) == 1
    src = src.replace(a, "GC_P.update({'mkt_dp_d29': False, 'final_sell0': 3, 'final_cap': 19})\n" + a, 1)
    a = "        if final and 3 > 0:\n            sell0 = sell0[:max(3, 1 if need_room > 0 else 0)]\n"
    assert src.count(a) == 1
    src = src.replace(a, "        if final and GC_P['final_sell0'] > 0:\n            sell0 = sell0[:max(GC_P['final_sell0'], 1 if need_room > 0 else 0)]\n", 1)
    a = "            fc = None if d28r else 19\n"
    assert src.count(a) == 1
    src = src.replace(a, "            fc = None if d28r else GC_P['final_cap']\n", 1)
    a = "            if p in GC_P['mkt_dp_prods'] and (not last) and (day <= 28) and (day >= 0):\n"
    assert src.count(a) == 1
    src = src.replace(a, "            if p in GC_P['mkt_dp_prods'] and (day >= 0) and ((not last and day <= 28) or (GC_P['mkt_dp_d29'] and day == 29 and step < 716)):\n", 1)
open(sys.argv[2], 'w', encoding='utf-8').write(src)
print('patched', sys.argv[2], opt)
