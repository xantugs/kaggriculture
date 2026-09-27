import math as _gc_math
GC_P = dict(div_over={}, animals_must=True, wheat_fert_gain=25.0, wheat_last_plant=25, carrot_first=14, carrot_min_demand=1, wheat_feed_bonus=4.0, straw_last_plant=12, straw_target=33, feed_reserve=1.0, fert_keep=6, fert_carrots=True, carrot_fert_gain=25.0, fert_res_extra=2, drip_room=80, dig_structs=True, feed_tiles_per_animal=0.75, tomato_on=True, tomato_first=12, tomato_last=18, tomato_max_day=12, tomato_step=2, tomato_alt_day=35.0, tomato_labor=60.0, tomato_harvest_min=3, opp_tomato_w=1.0, future_shop_w=1.0, plant_must=True, melon_on=False, melon_last=18, melon_age=11, melon_max_day=10, melon_alt_day=40.0, melon_labor=60.0, carrot_fc_units=3.5, dispatch=True, dispatch_min_value=8.0, fert_cost_w=1.0, ongoing_fert_gain=10.0, max_sell0=3, fert_buy_margin=20.0, trim_hour=10, reserve_release_hour=18, care_min_price=12, harvest_min_price=3, plant_defer=0.3, land_sw_day=11, eod_room=88, prem_w=1.0, deliver_min=6, deliver_prem_w=0.3, ovf_hire=True, order_cap_fix=True, stop_v2=True, shed_any=True, water_first=True, rematch=True, footprint=True, footprint_slack=2, multi_stop=True, late_sell0_day=99, max_hands_final=15, final_flush=True, d28_harvest_all=True, d28_zero_reserve=True, eod_room_d28=96, courier=True, courier_hour=12, courier_min=4, courier_margin=2, courier_max_detour=8, timed=('STRAWBERRY', 'MILK', 'WOOL', 'TOMATO'), rival_min_lot=2, rival_days=2, hold_max=23, hold_room=80, se_plots=16, se_reserve=1500, sell_floor={}, floor_last_day=26, floor_marginal=False, floor_wait_days=1.5, straw_fc=False, straw_fc_last=17, straw_fc_max=30, straw_fc_step=2, straw_labor=90.0, straw_alt_day=35.0, straw_units=2.0, straw_opp_w=1.0, straw_future_w=1.0, se_straw=False, se_straw_margin=2500.0, rich_tom_margin=2500.0, rich_tom_over={}, v219x_sizes=(10, 15, 20, 25), v219x_copy_n=10.0, v219x_opp_w=1.0, v219x_worker_cost=300.0, v219x_margin=1000.0, v219x_margins=None, v219x_units=2.0, v219x_day=18, unit_floor_frac=0.0, unit_floor_items=('WOOL', 'MILK', 'STRAWBERRY', 'MELON', 'TOMATO', 'EGG', 'CARROT', 'WHEAT'), unit_floor_step=716, chassis_floor_from=12, chassis_floor_room=20, herd_on=False, herd_first=12, herd_last=18, herd_kinds=('SHEEP', 'COW', 'GOOSE'), herd_max=12, herd_margin=1500.0, herd_opp_rate=0.8, herd_labor=20.0, herd_fert_w=0.8, herd_tile_cost=250.0, herd_keep_free=6, herd_rich_over={}, mkt_dp_prods=('STRAWBERRY', 'MILK', 'WOOL'), mkt_dp_cap=12, mkt_dp_periods=6, mkt_dp_rival_days=2, s2t_days=(), div2_band=(1000, 1070), late_plan_min=15.0, tick_defer=False, tick_last_day=29, tick_keep_due=True, rich_tom_dem_over={}, rich_car_over={}, rich_over={}, rich_hire_budget=1500.0, race_min=1, race_w=0.3, sanx_mask_adapt=True, arb_target={'WOOL': 150, 'MILK': 120, 'STRAWBERRY': 120})
GC_P.update({'div_over': {'floor_marginal': True, 'tomato_last': 20, 'melon_on': True, 'tick_defer': True, 'herd_first': 16, 'herd_last': 18, 'herd_on': True, 'herd_kinds': ['SHEEP', 'COW'], 'herd_labor': 60.0, 'herd_opp_rate': 1.0, 'herd_margin': 3000.0, 'herd_max': 6, 'unit_floor_frac': 0.0, 'melon_last': 19, 'melon_age': 10}, 'max_sell0': 0, 'sell_floor': {'STRAWBERRY': 30, 'MILK': 25, 'WOOL': 25}, 'rich_over': {'straw_fc': True, 'se_straw': True, 'herd_first': 12, 'herd_last': 18, 'herd_on': True, 'herd_kinds': ['SHEEP', 'COW'], 'herd_labor': 60.0, 'herd_opp_rate': 1.0, 'herd_margin': 3000.0, 'herd_max': 6}, 'v219x_sizes': [10, 15, 20], 'v219x_margins': {'15': 1250, '20': 3500}, 'herd_kinds': ['COW'], 'herd_labor': 60.0, 'herd_opp_rate': 1.0, 'herd_max': 6, 'herd_rich_over': {'herd_on': True, 'herd_kinds': ['COW'], 'herd_labor': 60.0, 'herd_opp_rate': 1.0, 'herd_margin': 3000.0, 'herd_max': 6, 'herd_first': 12, 'herd_last': 18}, 'unit_floor_frac': 0.03, 's2t_days': [8, 11], 'div2_band': [1000, 1070]})
_GC_CROPS = {'WHEAT': dict(seed=10, fy=2, my=4, iv=0, mx=6, on=False), 'CARROT': dict(seed=20, fy=2, my=3, iv=0, mx=4, on=False), 'TOMATO': dict(seed=50, fy=8, my=8, iv=1, mx=4, on=True), 'STRAWBERRY': dict(seed=100, fy=10, my=10, iv=2, mx=4, on=True), 'MELON': dict(seed=80, fy=10, my=12, iv=0, mx=6, on=False)}
_GC_ANIM = {'GOOSE': dict(cost=300, st='COOP', fy=4, iv=1, held=4, prod='EGG'), 'COW': dict(cost=400, st='PASTURE', fy=8, iv=2, held=6, prod='MILK'), 'SHEEP': dict(cost=500, st='PASTURE', fy=6, iv=3, held=6, prod='WOOL')}
_GC_MKT = {'WHEAT': (25, 400, 'sqrt', 0.8, 'log', 0.2), 'CARROT': (35, 450, 'hinge', 1.0, 'sqrt', 0.7), 'TOMATO': (60, 200, 'hinge', 0.4, 'sqrt', 0.6), 'STRAWBERRY': (120, 100, 'sqrt', 0.7, 'linear', 1.6), 'MELON': (250, 300, 'log', 0.2, 'sq', 3.6), 'EGG': (50, 332, 'hinge', 0.4, 'log', 0.2), 'MILK': (160, 122, 'sqrt', 0.6, 'linear', 1.6), 'WOOL': (200, 105, 'log', 0.2, 'sq', 3.2), 'FERTILIZER': (100, 200, 'linear', 0.4, 'linear', 0.4)}
_GC_SHOPS = {'BAKERY': ['EGG', 'WHEAT'], 'PIZZA_SHOP': ['MILK', 'TOMATO', 'WHEAT'], 'BRUNCH_SPOT': ['EGG', 'WHEAT', 'STRAWBERRY'], 'YARN_STORE': ['WOOL'], 'ICE_CREAM_SHOP': ['STRAWBERRY', 'MILK', 'WHEAT'], 'PET_CAFE': ['CARROT'], 'SMOOTHIE_SHOP': ['STRAWBERRY', 'MILK'], 'FARMERS_MARKET': ['WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY']}
_GC_PRODUCTS = ['WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'MELON', 'EGG', 'MILK', 'WOOL', 'FERTILIZER']
_GC_PREMIUM = ('MELON', 'WOOL', 'MILK', 'STRAWBERRY', 'TOMATO')
_GC_ACCESS = [(4, 4), (5, 4), (4, 5), (5, 5)]
_GC_ACCESS_SET = set(_GC_ACCESS)
_GC_REPORT = dict(gc_days=0, gc_errors=0, gc_hires=0, gc_noops=0, gc_unserved=0, gc_plan_ms=0, gc_room_sells=0)

def _gc_shape(f, x, T):
    x = max(0.0, x)
    if f == 'linear':
        return x
    if f == 'sq':
        return x * x
    if f == 'sqrt':
        return _gc_math.sqrt(x)
    if f == 'log':
        return _gc_math.log(1.0 + x)
    if f == 'hinge':
        u = x / T
        return u + 8.0 * max(0.0, u - 1.0) ** 2
    return x

def _gc_price(item, inv):
    base, T, bf, bt, af, at = _GC_MKT[item]
    if inv < 10000:
        amp = bt * base / _gc_shape(bf, T, T)
        p = base + amp * _gc_shape(bf, 10000 - inv, T)
    else:
        amp = at * base / _gc_shape(af, T, T)
        p = base - amp * _gc_shape(af, inv - 10000, T)
    return max(1, int(round(p)))

def _gc_fib(n):
    a, b = (1, 1)
    for _ in range(n):
        a, b = (b, a + b)
    return a

def _gc_quad(x, y):
    return ('N' if y < 5 else 'S') + ('W' if x < 5 else 'E')

def _gc_dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def _gc_near_access(p):
    return min(_GC_ACCESS, key=lambda a: abs(a[0] - p[0]) + abs(a[1] - p[1]))

def _gc_get(d, k, default=None):
    if isinstance(d, dict):
        return d.get(k, default)
    return getattr(d, k, default)
_OPEN_DEFAULT = dict(from_day=0, until=12, hires0=5, melon=12, melon_last=2, wheat0=None, straw_early={5: 4}, straw_d6={0: 16, 6: 20, 12: 23}, straw_slope=(15.0, 0.96), straw_max=38, straw_last=12, early_harvest=(2, 5), land={'NE': 7, 'SW': 9}, anim={'COW': {0: 2, 2: 3, 3: 4, 6: 6, 7: 7, 9: 8}, 'SHEEP': {0: 2, 6: 4, 8: 5, 9: 6}, 'GOOSE': {6: 3, 9: 4}}, sheep_yarn=8, anim_before_straw=False, anim_order=('COW', 'SHEEP', 'GOOSE'), after={'footprint': False}, anim_first_day=True, feed_place=True, wheat_fill=True, wheat_fill_from=0, keep_free=0, cash_keep=140.0, cash_low=1000000000.0, hire_min_budget=20.0, over={'plant_must': False, 'max_hands': 12, 'hire_cost_w': 1.0, 'prem_drop': True, 'prem_drop_max': 6, 'deliver_prem': 800.0, 'hire_compact': True}, feed_buy_hour=14, replan_hours=(5, 9, 13))

def _open_target(table, day):
    out = 0
    for d in sorted((int(k) for k in table)):
        if d <= day:
            out = table[d] if d in table else table[str(d)]
    return out

class _GcVisit:
    __slots__ = ('pos', 'acts', 'wheat', 'fert', 'anim', 'value', 'must', 'gain', 'tag', 'carry')

    def __init__(self, pos, acts, value=0.0, must=False, wheat=0, fert=0, anim=None, gain=None, tag='', carry=0):
        self.pos = pos
        self.acts = acts
        self.value = value
        self.must = must
        self.wheat = wheat
        self.fert = fert
        self.anim = anim
        self.gain = gain or {}
        self.tag = tag
        self.carry = carry

class GoldCtl:

    def __init__(self):
        self.reset()

    def reset(self):
        self.me = None
        self.herd_total = 0
        self.herd_day = None
        self.day_plan = None
        self.queues = {}
        self.routes = []
        self.spawns = []
        self.orders0 = []
        self.orders1 = []
        self.hires_planned = 0
        self.hires_left = 0
        self.reserve = {}
        self.arb = {}
        self._held_now = {}
        self.fp_bonus = 0
        self._straw_path = None
        self.last_hires = 10
        self.rival_sales = {}
        self._mk_prev = None
        self.se_day = None
        self.footprint_n = None
        self.n_animals = 0
        self.final = False
        self.open = None
        if getattr(self, '_open_over', None):
            GC_P.update(self._open_over)
        self._open_over = None

    def _straw_demand(self, shops):
        return sum((6 for sh in shops if sh in ('BRUNCH_SPOT', 'ICE_CREAM_SHOP', 'SMOOTHIE_SHOP', 'FARMERS_MARKET'))) + 1

    def _open_straw_target(self, day, shops):
        op = None
        if day > op['straw_last']:
            return 0
        if day < 6:
            return _open_target(op['straw_early'], day)
        dem = self._straw_demand(shops) - 1
        if day <= 8:
            tab = {int(k): v for k, v in op['straw_d6'].items()}
            t = 0
            for k in sorted(tab):
                if dem >= k:
                    t = tab[k]
        else:
            a, b = op['straw_slope']
            t = int(round(a + b * dem))
        return min(op['straw_max'], t)

    def _open_crops(self, obs, day, free, replant, shops, counts, avail, seeds):
        op = None
        out = {}
        cash = avail
        slots = sorted(free, key=lambda p: _gc_dist(p, (4.5, 4.5))) + sorted(replant, key=lambda p: _gc_dist(p, (4.5, 4.5)))
        want = []
        n_s = max(0, self._open_straw_target(day, shops) - counts.get('STRAWBERRY', 0))
        want.append(('STRAWBERRY', n_s))
        if day <= op['melon_last']:
            want.append(('MELON', max(0, op['melon'] - counts.get('MELON', 0))))
        n_w = 0
        if day == 0 and op['wheat0'] is not None:
            n_w = op['wheat0']
        elif op['wheat_fill'] and day >= op['wheat_fill_from']:
            n_w = len(slots)
        want.append(('WHEAT', n_w))
        held = dict(seeds)
        k = 0
        for crop, n in want:
            price = _GC_CROPS[crop]['seed']
            while n > 0 and k < len(slots) - (op['keep_free'] if crop == 'WHEAT' else 0):
                if held.get(crop, 0) > 0:
                    held[crop] -= 1
                elif cash >= price:
                    cash -= price
                else:
                    break
                out[slots[k]] = crop
                k += 1
                n -= 1
        self.open_spent = avail - cash
        return out

    def _values(self, obs):
        inv = obs['market']['inventory']
        val = {}
        for p in _GC_PRODUCTS:
            val[p] = float(_gc_price(p, inv[p]))
        self.pnow = dict(val)
        return val

    def plan_day(self, obs):
        step = int(obs['step'])
        day = step // 24
        self.day = day
        me = self.me
        farm = obs['farms'][me]
        priv = obs['private']
        shed = {k: int(v) for k, v in dict(priv['shed']).items()}
        seeds = {k: int(v) for k, v in dict(priv['seeds']).items()}
        money = float(farm['money'])
        shops = list(_gc_get(obs['town'], 'unlocked_shops', []) or [])
        tiles = farm['tiles']
        self.tiles_today = tiles
        final = day >= 29
        self.final = final
        val = self._values(obs)
        self.val = val
        quads = list(farm['unlocked_quadrants'])
        orders0 = []
        spend = 0.0
        hire_budget = sum((_gc_fib(k) for k in range(min(self.last_hires + 1, 13))))
        opn = None
        keep = 0.0
        if opn is not None and (not getattr(self, '_open_over', None)):
            self._open_over = {k: GC_P.get(k) for k in opn['over']}
            GC_P.update(opn['over'])
        elif opn is None and getattr(self, '_open_over', None):
            GC_P.update(self._open_over)
            self._open_over = None
            self.footprint_n = None
            GC_P.update(None.get('after', {}) or {})
        if opn is not None:
            if day == opn['from_day']:
                self.last_hires = opn['hires0']
                hire_budget = sum((_gc_fib(k) for k in range(opn['hires0'] + 1)))
            hire_budget = max(hire_budget, opn['hire_min_budget'])
            n_an_k = sum((1 for row in tiles for t in row if isinstance(t, dict) and 'animal' in t)) + sum((int(shed.get(a_, 0)) for a_ in ('COW', 'SHEEP', 'GOOSE')))
            keep = max(opn['cash_keep'], sum((_gc_fib(k) for k in range(min(self.last_hires, 11)))) + n_an_k * (self.pnow.get('WHEAT', 30) + 3) + 40)
            self._open_keep = keep
        new_quads = []
        if opn is not None:
            for q_, price_ in (('NE', 1000), ('SW', 2000), ('SE', 4000)):
                d_ = opn['land'].get(q_)
                if q_ not in quads and (not new_quads) and (d_ is not None) and (day >= int(d_)) and (money - spend - hire_budget - keep >= price_):
                    orders0.append(['BUY_LAND'])
                    spend += price_
                    new_quads.append(q_)
                    break
        elif not final and day <= 16:
            if 'NE' not in quads and money - hire_budget >= 1300:
                orders0.append(['BUY_LAND'])
                spend += 1000
                new_quads.append('NE')
            elif 'NE' in quads and 'SW' not in quads and (day >= GC_P['land_sw_day']) and (money - hire_budget >= 2400):
                orders0.append(['BUY_LAND'])
                spend += 2000
                new_quads.append('SW')
        if GC_P['se_straw'] and (not new_quads) and (not final) and ('NE' in quads) and ('SW' in quads) and ('SE' not in quads) and (day <= GC_P['straw_fc_last']) and (money - hire_budget >= 4000 + GC_P['se_reserve']):
            n_se = min(GC_P['se_plots'], int((money - hire_budget - 4000 - GC_P['se_reserve']) // 100))
            if n_se > 0:
                fert = self.pnow.get('FERTILIZER', 50)
                gain = self._straw_value(obs, day, n_se, shops) - self._straw_value(obs, day, 0, shops)
                life = min(16, 29 - day) + 1
                cost = 4000 + n_se * (100 + 3 * fert + GC_P['straw_labor'])
                if gain - cost > GC_P['se_straw_margin']:
                    orders0.append(['BUY_LAND'])
                    spend += 4000
                    new_quads.append('SE')
                    self.se_day = day
                    self.fp_bonus = getattr(self, 'fp_bonus', 0) + GC_P['se_plots']
        owned = set(quads) | set(new_quads)
        plants = []
        animals = []
        empties = []
        weeds = []
        structs = []
        counts = {}
        for y in range(10):
            for x in range(10):
                t = tiles[y][x]
                if t == 'LOCKED':
                    if _gc_quad(x, y) in owned:
                        empties.append((x, y))
                    continue
                if t is None:
                    empties.append((x, y))
                    continue
                k = t.get('kind')
                if k == 'PLANT':
                    plants.append(((x, y), t))
                    counts[t['crop']] = counts.get(t['crop'], 0) + 1
                elif k == 'WEED':
                    weeds.append((x, y))
                elif 'animal' in t:
                    animals.append(((x, y), t))
                elif k in ('COOP', 'PASTURE'):
                    structs.append(((x, y), k))
        self.n_animals = len(animals)
        visits = []
        replant = []
        for pos, t in plants:
            v = self._plant_visit(pos, t, day, val, final)
            if v is not None:
                visits.append(v)
                if v.tag == 'C' and v.acts and (v.acts[-1][0] == 'HARVEST') or v.tag == 'R' or (v.tag == 'D' and False):
                    replant.append(v)
        for pos, t in animals:
            v = self._animal_visit(pos, t, day, val, final)
            if v is not None:
                visits.append(v)
        herd_new = {}
        if GC_P['herd_on'] and (not final) and (GC_P['herd_first'] <= day <= GC_P['herd_last']) and (getattr(self, 'herd_day', None) != day):
            self.herd_day = day
            se_open = 'SE' not in owned and 'NE' in owned and ('SW' in owned) and (not new_quads)
            spare_tiles = max(0, len(empties) - GC_P['herd_keep_free']) if not new_quads else 0
            try:
                kind, k, hv, need_se = self._herd_plan(obs, day, shops, spare_tiles, se_open, money - spend - hire_budget)
            except Exception as e:
                kind, k, hv = (None, 0, 0.0)
            if kind and hv > GC_P['herd_margin'] and (len(orders0) < 7):
                if need_se:
                    orders0.append(['BUY_LAND'])
                    spend += 4000
                    new_quads.append('SE')
                    owned.add('SE')
                    se_tiles = [(xx, yy) for yy in range(5, 10) for xx in range(5, 10) if tiles[yy][xx] == 'LOCKED']
                    self.herd_tiles = sorted(se_tiles, key=lambda p: _gc_dist(p, (4.5, 4.5)))[:k]
                    for pp in se_tiles:
                        empties.append(pp)
                orders0.append(['BUY_ANIMAL', kind, k])
                spend += k * _GC_ANIM[kind]['cost']
                herd_new[kind] = k
                self.herd_total = getattr(self, 'herd_total', 0) + k
        if opn is not None:
            have = {}
            for _p, t in animals:
                have[t['animal']] = have.get(t['animal'], 0) + 1
            for an in ('COW', 'SHEEP', 'GOOSE'):
                have[an] = have.get(an, 0) + shed.get(an, 0)
            targets = []
            for an, tab in opn['anim'].items():
                t_ = _open_target({int(k): v for k, v in tab.items()}, day)
                if an == 'SHEEP' and day >= 6 and ('YARN_STORE' in shops):
                    t_ = max(t_, opn['sheep_yarn'])
                targets.append((an, t_))
            land_res = 0.0
            if not new_quads:
                for q_, price_ in (('NE', 1000), ('SW', 2000), ('SE', 4000)):
                    d_ = opn['land'].get(q_)
                    if q_ not in quads and d_ is not None and (day >= int(d_)):
                        land_res = price_
                        break
            for an, t_ in sorted(targets, key=lambda x: opn['anim_order'].index(x[0]) if x[0] in opn['anim_order'] else 9):
                n_ = max(0, t_ - have.get(an, 0))
                cost_ = _GC_ANIM[an]['cost']
                straw_due = max(0, self._open_straw_target(day, shops) - counts.get('STRAWBERRY', 0)) * 100
                n_an0 = len(animals) + sum(herd_new.values()) + sum((int(shed.get(a_, 0)) for a_ in ('COW', 'SHEEP', 'GOOSE')))
                feed0 = max(0, n_an0 - int(shed.get('WHEAT', 0))) * (self.pnow.get('WHEAT', 30) + 3)
                budget_ = money - spend - hire_budget - keep - feed0 - land_res - (0 if opn['anim_before_straw'] or (opn['anim_first_day'] and day == 0) else straw_due)
                k_ = min(n_, int(budget_ // cost_)) if cost_ > 0 else 0
                if k_ > 0 and len(orders0) < 7:
                    orders0.append(['BUY_ANIMAL', an, k_])
                    spend += k_ * cost_
                    herd_new[an] = herd_new.get(an, 0) + k_
        free_struct = {'COOP': [p for p, k in structs if k == 'COOP'], 'PASTURE': [p for p, k in structs if k == 'PASTURE']}
        taken = set()
        for an in ('COW', 'SHEEP', 'GOOSE'):
            for _ in range(shed.get(an, 0) + herd_new.get(an, 0)):
                st = _GC_ANIM[an]['st']
                if free_struct[st]:
                    pos = free_struct[st].pop(0)
                    fc = [['FEED'], ['CARE']] if opn is not None and opn['feed_place'] and (day <= 28) else []
                    visits.append(_GcVisit(pos, [['PLACE', an]] + fc, value=300.0, must=True, anim=an, tag='L', wheat=1 if fc else 0))
                else:
                    cand = [p for p in empties if p not in taken]
                    if not cand:
                        break
                    pos = min(cand, key=lambda p: _gc_dist(p, (4.5, 4.5)))
                    taken.add(pos)
                    fc = [['FEED'], ['CARE']] if opn is not None and opn['feed_place'] and (day <= 28) else []
                    visits.append(_GcVisit(pos, [['BUILD_' + st], ['PLACE', an]] + fc, value=300.0, must=True, anim=an, tag='L', wheat=1 if fc else 0))
        if GC_P['dig_structs'] and (not final):
            for st in ('COOP', 'PASTURE'):
                for pos in free_struct[st]:
                    weeds.append(pos)
        need_seeds = {}
        if not final:
            free = [p for p in empties if p not in taken] + list(weeds)
            if opn is not None:
                eh0, eh1 = opn['early_harvest']
                due = max(0, self._open_straw_target(day, shops) - counts.get('STRAWBERRY', 0))
                short = due - len(free) - sum((1 for v in replant))
                if eh0 <= day <= eh1 and short > 0:
                    cand = []
                    for v in visits:
                        if v.tag == 'C' and (not any((a[0] == 'HARVEST' for a in v.acts))):
                            t = tiles[v.pos[1]][v.pos[0]]
                            if isinstance(t, dict) and t.get('crop') == 'WHEAT':
                                age = day - int(t['planted_day'])
                                yu = int(t.get('yield_units', 0))
                                if age >= 2 and yu + 1 >= 2:
                                    cand.append((-age, v, yu))
                    cand.sort(key=lambda x: x[0])
                    for _a, v, yu in cand[:short]:
                        g = 1 if any((a[0] == 'WATER' for a in v.acts)) else 0
                        v.acts = [a for a in v.acts if a[0] != 'HARVEST'] + [['HARVEST']]
                        v.carry = yu + g
                        v.must = True
                        v.value += (yu + g) * val['WHEAT']
                        replant.append(v)
            if GC_P['footprint'] and opn is None:
                n_plants = len(plants)
                if getattr(self, 'footprint_n', None) is None:
                    self.footprint_n = n_plants + len(weeds) + GC_P['footprint_slack']
                room_new = max(0, self.footprint_n + getattr(self, 'fp_bonus', 0) - n_plants)
                if len(free) > room_new:
                    free = sorted(free, key=lambda q: _gc_dist(q, (4.5, 4.5)))[:room_new]
            if opn is not None:
                n_an = len(animals) + sum(herd_new.values()) + sum((int(shed.get(an, 0)) for an in ('COW', 'SHEEP', 'GOOSE')))
                feed_est = max(0, n_an - int(shed.get('WHEAT', 0))) * (self.pnow.get('WHEAT', 30) + 3)
                crop_for = self._open_crops(obs, day, free, [v.pos for v in replant], shops, counts, money - spend - hire_budget - keep - feed_est, seeds)
                n_s_planned = sum((1 for c in crop_for.values() if c == 'STRAWBERRY'))
                straw_left = max(0, self._open_straw_target(day, shops) - counts.get('STRAWBERRY', 0) - n_s_planned)
                land_left = any((q_ not in quads and q_ not in new_quads and (opn['land'].get(q_) is not None) and (day >= int(opn['land'][q_])) for q_ in ('NE', 'SW', 'SE')))
                anim_left = False
                for an, tab in opn['anim'].items():
                    t_ = _open_target({int(k): v for k, v in tab.items()}, day)
                    have_ = sum((1 for _p, t in animals if t['animal'] == an)) + int(shed.get(an, 0)) + herd_new.get(an, 0)
                    if t_ > have_:
                        anim_left = True
                self._open_urgent = bool(land_left or straw_left > 0 or anim_left)
                if self._open_urgent:
                    pass
            else:
                crop_for = self._choose_crops(obs, day, free, [v.pos for v in replant], shops, val, counts)
            for pos in free:
                crop = crop_for.get(pos)
                if not crop:
                    continue
                acts = ([['DIG']] if pos in weeds else []) + [['PLANT', crop], ['WATER']]
                pv_ = self._crop_value(crop, val)
                visits.append(_GcVisit(pos, acts, value=GC_P['plant_defer'] * pv_, tag='P', must=GC_P['plant_must'] and day <= 29))
                need_seeds[crop] = need_seeds.get(crop, 0) + 1
            for v in replant:
                crop = crop_for.get(v.pos)
                if not crop:
                    continue
                if opn is not None and 0.0:
                    continue
                v.acts = v.acts + [['PLANT', crop], ['WATER']]
                pv_ = self._crop_value(crop, val)
                v.value += GC_P['plant_defer'] * pv_
                need_seeds[crop] = need_seeds.get(crop, 0) + 1
            for crop, n in need_seeds.items():
                buy = n - seeds.get(crop, 0)
                if buy > 0:
                    cost = buy * _GC_CROPS[crop]['seed']
                    avail = money - spend - hire_budget
                    if cost > avail:
                        buy = max(0, int(avail // _GC_CROPS[crop]['seed']))
                        cost = buy * _GC_CROPS[crop]['seed']
                    if buy > 0:
                        orders0.append(['BUY_SEED', crop, buy])
                        spend += cost
        wheat_need = sum((v.wheat for v in visits))
        fert_need = sum((v.fert for v in visits))
        wheat_have = shed.get('WHEAT', 0)
        if wheat_need > wheat_have:
            short = wheat_need - wheat_have
            price = _gc_price('WHEAT', obs['market']['inventory']['WHEAT'] - short)
            if opn is not None:
                short = min(short, max(0, int((money - spend - hire_budget) // max(1, price))))
            if short > 0:
                orders0.append(['BUY_PRODUCT', 'WHEAT', short])
                spend += short * price
        fert_have = shed.get('FERTILIZER', 0)
        if fert_need > fert_have:
            fv = sorted([v for v in visits if v.fert], key=lambda v: -v.gain.get('fert', 0.0))
            short = fert_need - fert_have
            fprice = _gc_price('FERTILIZER', obs['market']['inventory']['FERTILIZER'] - short)
            buy = sum((1 for v in fv[:short] if v.gain.get('fert', 0.0) > fprice + GC_P['fert_buy_margin']))
            if buy > 0 and money - spend - hire_budget > buy * fprice + 100:
                orders0.append(['BUY_PRODUCT', 'FERTILIZER', buy])
                spend += buy * fprice
                fert_have += buy
        if fert_need > fert_have:
            fv = sorted([v for v in visits if v.fert], key=lambda v: v.gain.get('fert', 0.0))
            for v in fv[:fert_need - fert_have]:
                v.acts = [a for a in v.acts if a[0] != 'FERTILIZE']
                v.fert = 0
                v.value -= v.gain.get('fert', 0.0)
        visits = [v for v in visits if v.acts]
        buys0 = [o for o in orders0 if o[0] in ('BUY_PRODUCT', 'BUY_ANIMAL')]
        res_w = int(GC_P['feed_reserve'] * len(animals)) + 2
        sell0 = []
        for p in sorted(_GC_PRODUCTS, key=lambda p: -(shed.get(p, 0) * val.get(p, 0))):
            n = int(shed.get(p, 0)) - (res_w if p == 'WHEAT' else GC_P['fert_keep'] if p == 'FERTILIZER' else 0)
            if n > 0:
                sell0.append(['SELL', p, n])
        need_room = sum((int(v) for v in shed.values())) + sum((int(o[2]) for o in buys0)) - 95
        if GC_P['unit_floor_frac'] > 0 and need_room <= 0:
            sell0 = [['SELL', o[1], self._unit_cap(obs, o[1], int(o[2]))] for o in sell0]
            sell0 = [o for o in sell0 if o[2] > 0]
        if final and 3 > 0:
            sell0 = sell0[:max(3, 1 if need_room > 0 else 0)]
        elif not final and day >= GC_P['late_sell0_day'] and (0 > 0):
            sell0 = sell0[:max(0, 1 if need_room > 0 else 0)]
        else:
            sell0 = sell0[:max(GC_P['max_sell0'], 1 if need_room > 0 else 0)]
        self.sell0 = sell0
        self.n0_hires = 10 - len(buys0) - len(sell0)
        import time as _t
        t0 = _t.perf_counter()
        routes, hires, spawns = self._route_and_hire(visits, money - spend, final, day)
        self.hires_planned = hires
        self.last_hires = hires
        self.orders0 = list(self.sell0) + [o for o in orders0 if o[0] in ('BUY_PRODUCT', 'BUY_ANIMAL')]
        self.orders1 = [o for o in orders0 if o[0] not in ('BUY_PRODUCT', 'BUY_ANIMAL')]
        if opn is not None and len(self.orders0) + len(self.orders1) + hires <= 10:
            self.orders0 = self.orders0 + self.orders1
            self.orders1 = []
        self.routes = routes
        self.spawns = spawns
        self.day = day
        if GC_P['stop_v2']:
            self.drop_at = {}
            d28r = None is not None
            if final and True or d28r:
                _ovf, _pv = (0, 0.0)
            else:
                _ovf, _pv = self._plan_stops(routes, spawns)
            if final or d28r:
                for u, r in enumerate(routes):
                    if r and r[-1].tag != 'S':
                        r.append(self._stop_visit(r[-1].pos))
        else:
            self.drop_at, _ovf, _pv = self._plan_drops(routes, spawns)
        if opn is not None and money - spend < opn['cash_low'] and (not final):
            for u, r in enumerate(routes):
                if u in self.drop_at or not r or any((v.tag == 'S' for v in r)):
                    continue
                ai = [k for k, v in enumerate(r) if v.tag == 'A' and v.carry > 0]
                if ai and sum((v.carry for v in r[:ai[-1] + 1])) > 0:
                    k = ai[-1]
                    v = r[k]
                    a = _gc_near_access(v.pos)
                    back = abs(v.pos[0] - a[0]) + abs(v.pos[1] - a[1])
                    if k + 1 < len(r):
                        nx = r[k + 1].pos
                        extra = back + 1 + abs(a[0] - nx[0]) + abs(a[1] - nx[1]) - (abs(v.pos[0] - nx[0]) + abs(v.pos[1] - nx[1]))
                    else:
                        extra = back + 1
                    cap = 23 if u == 0 else 23 if u <= self.n0_hires else 22
                    if self._rcost(spawns[u], r) + extra <= cap:
                        self.drop_at[u] = k
        if final and (not GC_P['stop_v2']):
            for u, r in enumerate(routes):
                if r:
                    self.drop_at[u] = len(r) - 1
        fert_tom = 0
        for pos, t in plants:
            cd = _GC_CROPS[t['crop']]
            age1 = day + 1 - int(t['planted_day'])
            fu = int(t.get('fertilized_until_day', -1))
            if cd['on']:
                k1 = age1 + 1 - cd['fy']
                if k1 >= 0 and k1 % cd['iv'] == 0 and (k1 // cd['iv'] + 1 <= cd['mx']) and (fu < day + 1):
                    fert_tom += 1
            elif t['crop'] in ('WHEAT', 'CARROT') and age1 == (cd['my'] + 1) // 2 and (fu < day + 1):
                fert_tom += 1
        self.fert_tomorrow = fert_tom
        self.reserve = {'WHEAT': int(GC_P['feed_reserve'] * len(animals)) + 2, 'FERTILIZER': max(GC_P['fert_keep'], fert_tom + GC_P['fert_res_extra'])}
        if GC_P['d28_zero_reserve'] and day >= 28:
            self.reserve = {'WHEAT': 0, 'FERTILIZER': 0}
        if opn is not None:
            fert_on = 0
            for pos, t in plants:
                cd = _GC_CROPS[t['crop']]
                age1 = day + 1 - int(t['planted_day'])
                fu = int(t.get('fertilized_until_day', -1))
                if cd['on']:
                    k1 = age1 + 1 - cd['fy']
                    if k1 >= 0 and k1 % cd['iv'] == 0 and (k1 // cd['iv'] + 1 <= cd['mx']) and (fu < day + 1):
                        fert_on += 1
            self.reserve['FERTILIZER'] = fert_on

    def _plant_visit(self, pos, t, day, val, final):
        crop = t['crop']
        cd = _GC_CROPS[crop]
        age = day - int(t['planted_day'])
        cu = int(t['consecutive_unwatered'])
        yu = int(t['yield_units'])
        fu = int(t.get('fertilized_until_day', -1))
        acts = []
        value = 0.0
        must = False
        fert = 0
        gain = {}
        carry = 0
        pv = val[crop]
        if not cd['on']:
            ws = (cd['my'] + 1) // 2
            ready = age >= cd['fy']
            in_window = ws <= age <= cd['my']
            if final:
                if ready and yu > 0:
                    acts = []
                    g = 0
                    if in_window and yu < cd['mx'] and (not t.get('watered_today')):
                        g = min(2 if fu >= day else 1, cd['mx'] - yu)
                        acts.append(['WATER'])
                    acts.append(['HARVEST'])
                    return _GcVisit(pos, acts, value=(yu + g) * pv, must=True, tag='H', carry=yu + g)
                return None
            yu2 = yu
            if in_window and yu < cd['mx']:
                fert_active = fu >= day
                if not fert_active and age == ws and (not (crop == 'CARROT' and (not GC_P['fert_carrots']))):
                    rem_days = cd['my'] - age + 1
                    extra = min(cd['mx'] - yu, 2 * rem_days) - min(cd['mx'] - yu, rem_days)
                    fert_gain = extra * pv - self.pnow.get('FERTILIZER', 50)
                    if fert_gain > (GC_P['carrot_fert_gain'] if crop == 'CARROT' else GC_P['wheat_fert_gain']):
                        acts.append(['FERTILIZE'])
                        fert = 1
                        gain['fert'] = fert_gain
                        value += fert_gain
                        fert_active = True
                g = min(2 if fert_active else 1, cd['mx'] - yu)
                acts.append(['WATER'])
                value += g * pv
                yu2 = yu + g
                if cu >= 1:
                    must = True
                    value += (yu + g) * pv
                if crop == 'MELON' and None is not None:
                    must = True
            elif cu >= 1 and (not (ready and yu > 0 and (age >= cd['my']))):
                acts.append(['WATER'])
                value += max(1, yu) * pv + 30
                must = True
            harvest_now = ready and yu2 > 0 and (age >= cd['my'] or yu2 >= cd['mx'])
            if crop == 'MELON':
                harvest_now = age >= cd['fy'] and yu2 > 0 and (yu2 >= cd['mx'] or age >= cd['my'])
            if day >= 28 and ready and (yu2 > 0) and (GC_P['d28_harvest_all'] or age >= cd['my'] or yu2 >= cd['mx']):
                keep = crop == 'CARROT' and age < cd['my'] and (yu2 < cd['mx'])
                if not keep:
                    harvest_now = True
            if harvest_now:
                acts.append(['HARVEST'])
                value += yu2 * pv
                must = True
                carry = yu2
                gain['prod'] = crop
                gain['pv'] = pv
            if not acts:
                return None
            return _GcVisit(pos, acts, value=value, must=must, fert=fert, gain=gain, tag='C', carry=carry)
        k_next = age + 1 - cd['fy']
        eve = k_next >= 0 and k_next % cd['iv'] == 0 and (k_next // cd['iv'] + 1 <= cd['mx'])
        done = int(t.get('max_lifespan_step', -1)) >= 0
        if final:
            if yu > 0:
                return _GcVisit(pos, [['HARVEST']], value=yu * pv, must=True, tag='H', carry=yu)
            return None
        fert_active = fu >= day
        add = (2 if fert_active else 1) if eve else 0
        if yu > 0:
            over = max(0, yu + add - cd['mx'])
            thr = GC_P['tomato_harvest_min'] if crop == 'TOMATO' else 2
            race = False
            if race:
                thr = min(thr, GC_P['race_min'])
            if over > 0 or done or day >= 28 or (yu >= thr):
                acts.append(['HARVEST'])
                value += over * pv + yu * pv * 0.15 + (yu * pv if done else 0)
                carry = yu
                gain['prod'] = crop
                gain['pv'] = pv
                if race:
                    value += yu * pv * GC_P['race_w']
        if eve:
            if not fert_active:
                covered = sum((1 for dd in range(3) if k_next + dd >= 0 and (k_next + dd) % cd['iv'] == 0 and ((k_next + dd) // cd['iv'] + 1 <= cd['mx'])))
                fert_gain = covered * pv - self.pnow.get('FERTILIZER', 50) * GC_P['fert_cost_w']
                if fert_gain > GC_P['ongoing_fert_gain']:
                    acts.append(['FERTILIZE'])
                    fert = 1
                    gain['fert'] = fert_gain
                    value += fert_gain
                    fert_active = True
            if fert_active:
                acts.append(['WATER'])
                value += pv
                if cu >= 1:
                    must = True
                    value += 4 * pv
            elif cu >= 1:
                acts.append(['WATER'])
                value += 4 * pv
                must = True
        elif cu >= 1 and (not done):
            acts.append(['WATER'])
            value += 4 * pv
            must = True
        if done and day <= 26 and True:
            acts = [a for a in acts if a[0] == 'HARVEST'] + [['DIG']]
            return _GcVisit(pos, acts, value=value + 40.0, must=GC_P['plant_must'], tag='R', carry=carry)
        if done and yu == 0 and (not acts):
            if day <= 26:
                return _GcVisit(pos, [['DIG']], value=40.0, tag='D', must=GC_P['plant_must'])
            return None
        if not acts:
            return None
        if GC_P['water_first']:
            acts = [a for a in acts if a[0] != 'HARVEST'] + [a for a in acts if a[0] == 'HARVEST']
        return _GcVisit(pos, acts, value=value, must=must, fert=fert, gain=gain, tag='O', carry=carry)

    def _animal_visit(self, pos, t, day, val, final):
        a = _GC_ANIM[t['animal']]
        yu = int(t['yield_units'])
        pv = val[a['prod']]
        pend = int(t.get('pending_care_bonus', 0) or 0)
        acts = []
        value = 0.0
        must = False
        wheat = 0
        carry = 0
        if final:
            acts = []
            if yu > 0 and pv >= 2:
                acts.append(['HARVEST'])
            if t.get('fertilizer_available') and self.pnow.get('FERTILIZER', 0) >= 3:
                acts.append(['COLLECT_FERTILIZER'])
            if acts:
                return _GcVisit(pos, acts, value=yu * pv + self.pnow.get('FERTILIZER', 0), must=True, tag='H', carry=yu + 1)
            return None
        placed = int(t.get('placed_day', 0))

        def prod_at(e):
            k = e + 1 - placed - a['fy']
            return k >= 0 and k % a['iv'] == 0
        prod_tonight = prod_at(day)
        e = day + 1
        while e <= 28 and (not prod_at(e)):
            e += 1
        care_useful = e <= 28 and pend + 2 <= a['held']
        care_worth = care_useful and pv >= GC_P['care_min_price']
        unfed = int(t['consecutive_unfed']) >= 1
        wheat_px = self.pnow.get('WHEAT', 40)
        bonus_tonight = prod_tonight and pv * (1 + pend) > wheat_px
        feed = day <= 28 and (unfed or care_worth or bonus_tonight or False)
        if feed:
            acts.append(['FEED'])
            wheat = 1
            if unfed:
                value += 500.0
                must = True
            else:
                value += (pv * (1 + pend) if prod_tonight else 0.0) + 5.0
        if care_worth and feed:
            acts.append(['CARE'])
            value += pv * 0.9
        if yu > 0:
            nxt = 1 + pend if prod_tonight else 0
            over = max(0, yu + nxt - a['held'])
            race = False
            thr = min(3, GC_P['race_min']) if race else 3
            if (over > 0 or yu >= thr or day >= 27) and (pv >= GC_P['harvest_min_price'] or day >= 28):
                acts.append(['HARVEST'])
                value += over * pv + yu * pv * 0.1
                carry += yu
                gain_a = {'prod': a['prod'], 'pv': pv, 'units': yu}
                if race:
                    value += yu * pv * GC_P['race_w']
        if t.get('fertilizer_available'):
            acts.append(['COLLECT_FERTILIZER'])
            value += max(3.0, self.pnow.get('FERTILIZER', 30) * 0.8)
            carry += 1
        if not acts:
            return None
        must = must or (GC_P['animals_must'] and wheat > 0)
        return _GcVisit(pos, acts, value=value, must=must, wheat=wheat, tag='A', carry=carry, gain=locals().get('gain_a'))

    def _crop_value(self, crop, val):
        cd = _GC_CROPS[crop]
        units = {'WHEAT': 5.0, 'CARROT': 3.5, 'TOMATO': 7.0, 'STRAWBERRY': 7.0, 'MELON': 6.0}[crop]
        return units * val[crop] - cd['seed']

    def _herd_value(self, obs, day, kind, k, shops):
        a = _GC_ANIM[kind]
        prod = a['prod']
        inv = float(obs['market']['inventory'][prod])
        drain_now = 1.0 + sum((12.0 if len(_GC_SHOPS.get(sh, [])) == 1 else 6.0 for sh in shops if prod in _GC_SHOPS.get(sh, [])))
        per_unlock = sum((12.0 if len(v) == 1 else 6.0 for v in _GC_SHOPS.values() if prod in v)) / 8.0
        rate = (1.0 + a['iv']) / a['iv']
        ours = 0
        theirs = 0
        for side in (self.me, 1 - self.me):
            for row in obs['farms'][side]['tiles']:
                for t in row:
                    if isinstance(t, dict) and t.get('animal') == kind:
                        if side == self.me:
                            ours += 1
                        else:
                            theirs += 1
        placed = day + 0
        sched = {}
        dd = placed + a['fy']
        if dd <= 29:
            sched[dd] = min(a['held'], a['fy'])
            dd += a['iv']
            while dd <= 29:
                sched[dd] = min(a['held'], 1 + a['iv'])
                dd += a['iv']
        n_shops = len(shops)
        rev = 0.0
        rev_th = 0.0
        for d in range(day, 30):
            unl = min(8, d // 3) - n_shops
            inv -= drain_now + max(0, unl) * per_unlock * GC_P['future_shop_w']
            q_ours = ours * rate + k * sched.get(d, 0)
            q_tot = q_ours + theirs * rate * 1.0
            n = int(round(q_tot))
            if n > 0:
                sm = sum((_gc_price(prod, inv + i) for i in range(n)))
                rev += sm * q_ours / q_tot
                rev_th += sm * (q_tot - q_ours) / q_tot
            inv += q_tot
        return rev - float(0.0) * rev_th

    def _herd_plan(self, obs, day, shops, n_empty, se_open, money, kinds=None):
        pn = getattr(self, 'pnow', None) or {}
        wheat_px = pn.get('WHEAT', 40)
        fert_px = pn.get('FERTILIZER', 30)
        best = (None, 0, 0.0, False)
        days = 30 - (day + 0)
        for kind in kinds or GC_P['herd_kinds']:
            a = _GC_ANIM[kind]
            base = self._herd_value(obs, day, kind, 0, shops)
            for k in range(1, min(6, 6 - getattr(self, 'herd_total', 0)) + 1):
                need_se = k > n_empty
                if need_se and (not se_open):
                    break
                cost = k * (a['cost'] + days * (wheat_px + 60.0 - GC_P['herd_fert_w'] * fert_px))
                cost += min(k, n_empty) * GC_P['herd_tile_cost'] + (4000.0 if need_se else 0.0)
                if cost + 500 > money:
                    break
                v = self._herd_value(obs, day, kind, k, shops) - base - cost
                if v > best[2]:
                    best = (kind, k, v, need_se)
        return best

    def _tomato_value(self, obs, day, n, shops):
        inv = float(obs['market']['inventory']['TOMATO'])
        k_now = sum((1 for s in shops if s in ('PIZZA_SHOP', 'FARMERS_MARKET')))
        n_shops = len(shops)
        opp = obs['farms'][1 - self.me]
        opp_sup = {}
        for row in opp['tiles']:
            for t in row:
                if isinstance(t, dict) and t.get('crop') == 'TOMATO':
                    pd = int(t['planted_day'])
                    for age, u in ((9, 4), (11, 4)):
                        d = pd + age
                        if d >= day:
                            opp_sup[d] = opp_sup.get(d, 0) + u * GC_P['opp_tomato_w']
        mine = {}
        for row in obs['farms'][self.me]['tiles']:
            for t in row:
                if isinstance(t, dict) and t.get('crop') == 'TOMATO':
                    pd = int(t['planted_day'])
                    for age, u in ((9, 4), (11, 4)):
                        d = pd + age
                        if d >= day:
                            mine[d] = mine.get(d, 0) + u
        rev = 0.0
        for d in range(day, 30):
            unl = min(8, d // 3) - n_shops
            k = k_now + max(0, unl) * 0.25 * GC_P['future_shop_w']
            inv -= 6.0 * k + 1.0
            inv += opp_sup.get(d, 0) + mine.get(d, 0)
            for age in (9, 11):
                if d == day + age and d <= 29:
                    q = 4 * n
                    p0 = _gc_price('TOMATO', inv)
                    p1 = _gc_price('TOMATO', inv + q)
                    rev += q * 0.5 * (p0 + p1)
                    inv += q
        return rev

    def _straw_value(self, obs, day, n, shops, fw=None):
        inv = float(obs['market']['inventory']['STRAWBERRY'])
        sshops = ('BRUNCH_SPOT', 'ICE_CREAM_SHOP', 'SMOOTHIE_SHOP', 'FARMERS_MARKET')
        k_now = sum((1 for s in shops if s in sshops))
        n_shops = len(shops)
        sup = {}
        lag = int(1)
        for side, w in ((self.me, 0.9), (1 - self.me, GC_P['straw_opp_w'])):
            for row in obs['farms'][side]['tiles']:
                for t in row:
                    if isinstance(t, dict) and t.get('crop') == 'STRAWBERRY':
                        pd = int(t['planted_day'])
                        for k in range(4):
                            d = pd + 10 + 2 * k + lag
                            if d >= day:
                                sup[d] = sup.get(d, 0) + GC_P['straw_units'] * w
                        yu = int(t.get('yield_units', 0) or 0)
                        if yu:
                            sup[day + lag] = sup.get(day + lag, 0) + yu * w
        rev = 0.0
        new_days = {day + 10 + 2 * k + lag for k in range(4)}
        for d in range(day, 30):
            unl = min(8, d // 3) - n_shops
            k = k_now + max(0, unl) * 0.5 * GC_P['future_shop_w'] * (GC_P['straw_future_w'] if fw is None else fw)
            inv -= 6.0 * k + 1.0
            inv += sup.get(d, 0)
            if n == 0 and getattr(self, '_straw_path', None) is not None:
                self._straw_path.append((d, _gc_price('STRAWBERRY', int(inv))))
            if d in new_days and n > 0:
                q = GC_P['straw_units'] * n
                p0 = _gc_price('STRAWBERRY', int(inv))
                p1 = _gc_price('STRAWBERRY', int(inv + q))
                rev += q * 0.5 * (p0 + p1)
                inv += q
        return rev

    def rich_eval(self, obs):
        farm = obs['farms'][self.me]
        quads = list(farm['unlocked_quadrants'])
        if 'SE' in quads or 'NE' not in quads or 'SW' not in quads:
            return -1000000000.0
        money = float(farm['money'])
        if money < 4000 + GC_P['se_reserve'] + GC_P['rich_hire_budget']:
            return -1000000000.0
        day = int(obs['step']) // 24
        self._values(obs)
        shops = list(_gc_get(obs['town'], 'unlocked_shops', []) or [])
        n_se = min(GC_P['se_plots'], int((money - GC_P['rich_hire_budget'] - 4000 - GC_P['se_reserve']) // 100))
        if n_se <= 0:
            return -1000000000.0
        fert = self.pnow.get('FERTILIZER', 50)
        gain = self._straw_value(obs, day, n_se, shops) - self._straw_value(obs, day, 0, shops)
        if GC_P.get('straw_debug'):
            self._straw_path = []
            self._straw_value(obs, day, 0, shops)
            pl = []
            for side in (self.me, 1 - self.me):
                for row in obs['farms'][side]['tiles']:
                    for t in row:
                        if isinstance(t, dict) and t.get('crop') == 'STRAWBERRY':
                            pl.append('%s%d/%d' % ('u' if side == self.me else 'r', int(t['planted_day']), int(t.get('yield_units', 0) or 0)))
        return gain - (4000 + n_se * (100 + 3 * fert + GC_P['straw_labor']))

    def rich_eval_tom(self, obs):
        farm = obs['farms'][self.me]
        quads = list(farm['unlocked_quadrants'])
        if 'SE' in quads or 'NE' not in quads or 'SW' not in quads:
            return -1000000000.0
        money = float(farm['money'])
        if money < 4000 + GC_P['se_reserve'] + GC_P['rich_hire_budget']:
            return -1000000000.0
        day = int(obs['step']) // 24
        self._values(obs)
        shops = list(_gc_get(obs['town'], 'unlocked_shops', []) or [])
        n_se = GC_P['se_plots']
        fert = self.pnow.get('FERTILIZER', 50)
        gain = self._tomato_value(obs, day, n_se, shops) - self._tomato_value(obs, day, 0, shops)
        return gain - (4000 + n_se * (50 + 2 * fert + GC_P['tomato_labor']))

    def _straw_count(self, obs, day, n_free, shops):
        if not GC_P['straw_fc'] or day > GC_P['straw_fc_last'] or n_free <= 0:
            return 0
        fert = self.pnow.get('FERTILIZER', 50)
        life = min(16, 29 - day) + 1
        alt = GC_P['straw_alt_day'] * life
        cost = 100 + 3 * fert + GC_P['straw_labor']
        cfw = None
        base = self._straw_value(obs, day, 0, shops, fw=cfw)
        best_n, best_v = (0, 0.0)
        for n in range(GC_P['straw_fc_step'], min(n_free, GC_P['straw_fc_max']) + 1, GC_P['straw_fc_step']):
            v = self._straw_value(obs, day, n, shops, fw=cfw) - base - n * (cost + alt)
            if v > best_v:
                best_n, best_v = (n, v)
        return best_n

    def _tomato_count(self, obs, day, n_free, shops, val):
        if not GC_P['tomato_on'] or day < GC_P['tomato_first'] or day > GC_P['tomato_last'] or (n_free <= 0):
            return 0
        fert = self.pnow.get('FERTILIZER', 50)
        alt = GC_P['tomato_alt_day'] * 12.0
        cost = 50 + 2 * fert + GC_P['tomato_labor']
        best_n, best_v = (0, 0.0)
        base = self._tomato_value(obs, day, 0, shops)
        mx = GC_P['tomato_max_day']
        if getattr(self, 'se_day', None) == day:
            mx = max(mx, GC_P['se_plots'])
        for n in range(GC_P['tomato_step'], min(n_free, mx) + 1, GC_P['tomato_step']):
            v = self._tomato_value(obs, day, n, shops) - base - n * (cost + alt)
            if v > best_v:
                best_n, best_v = (n, v)
        return best_n

    def _melon_value(self, obs, day, n):
        inv = float(obs['market']['inventory']['MELON'])
        sup = {}
        for farm in obs['farms']:
            for row in farm['tiles']:
                for t in row:
                    if isinstance(t, dict) and t.get('crop') == 'MELON':
                        hd = int(t['planted_day']) + GC_P['melon_age']
                        if hd >= day:
                            sup[hd] = sup.get(hd, 0) + 6
        rev = 0.0
        hd_new = day + GC_P['melon_age']
        for d in range(day, 30):
            inv -= 1.0
            inv += sup.get(d, 0)
            if d == min(hd_new, 29) and n > 0:
                q = 6 * n
                tot = 0.0
                for k in range(q):
                    tot += _gc_price('MELON', int(inv) + k)
                rev += tot
                inv += q
        return rev

    def _melon_count(self, obs, day, n_free):
        if not GC_P['melon_on'] or day > GC_P['melon_last'] or n_free <= 0:
            return 0
        fert = self.pnow.get('FERTILIZER', 50)
        alt = GC_P['melon_alt_day'] * GC_P['melon_age']
        cost = 80 + GC_P['melon_labor']
        base = self._melon_value(obs, day, 0)
        best_n, best_v = (0, 0.0)
        for n in range(1, min(n_free, GC_P['melon_max_day']) + 1):
            v = self._melon_value(obs, day, n) - base - n * (cost + alt)
            if v > best_v:
                best_n, best_v = (n, v)
        return best_n

    def _carrot_book_at_harvest(self, obs, day, shops):
        inv = float(obs['market']['inventory']['CARROT'])
        per_day = 1.0 + sum((12.0 if sh == 'PET_CAFE' else 6.0 if sh == 'FARMERS_MARKET' else 0.0 for sh in shops))
        sup = 0.0
        for farm in obs['farms']:
            for row in farm['tiles']:
                for t in row:
                    if isinstance(t, dict) and t.get('crop') == 'CARROT':
                        hd = int(t['planted_day']) + 3
                        if day <= hd <= day + 3:
                            sup += GC_P['carrot_fc_units']
        return inv - per_day * 3.0 + sup

    def _choose_crops(self, obs, day, free, replant, shops, val, counts):
        out = {}
        straw_room = 0
        if day <= GC_P['straw_last_plant']:
            straw_room = max(0, GC_P['straw_target'] - counts.get('STRAWBERRY', 0))
        carrot_demand = sum((2 if s == 'PET_CAFE' else 1 if s == 'FARMERS_MARKET' else 0 for s in shops))
        fert = self.pnow.get('FERTILIZER', 50)
        v_wheat = (6 * val['WHEAT'] - 10 - fert) / 4.0 + GC_P['wheat_feed_bonus']
        v_carrot = (4 * val['CARROT'] - 20 - fert) / 3.0
        filler = 'WHEAT'
        if carrot_demand >= GC_P['carrot_min_demand'] and v_carrot > 0.85 * v_wheat and (day >= GC_P['carrot_first']):
            filler = 'CARROT'

        def fill(d):
            if filler == 'CARROT' and d <= 26:
                return 'CARROT'
            if d <= GC_P['wheat_last_plant']:
                return 'WHEAT'
            if d <= 26:
                return 'CARROT'
            return None
        wheat_now = max(0, counts.get('WHEAT', 0) - len(replant))
        need_w = int(GC_P['feed_tiles_per_animal'] * self.n_animals + 0.999) if day <= GC_P['wheat_last_plant'] and False else 0
        slots = sorted(free, key=lambda p: _gc_dist(p, (4.5, 4.5))) + sorted(replant, key=lambda p: _gc_dist(p, (4.5, 4.5)))
        n_slots = len(slots)
        feed_first = max(0, need_w - wheat_now) if need_w > 0 else 0
        spare = max(0, n_slots - feed_first - (straw_room if day <= GC_P['straw_last_plant'] else 0))
        n_sfc = min(self._straw_count(obs, day, spare, shops), spare) if GC_P['straw_fc'] else 0
        straw_room += n_sfc
        spare -= n_sfc
        n_tom = min(self._tomato_count(obs, day, spare, shops, val), spare)
        self.n_tomato_today = n_tom
        n_mel = min(self._melon_count(obs, day, spare - n_tom), spare - n_tom) if GC_P['melon_on'] else 0
        placed_m = 0
        placed_t = 0
        straw_any = n_sfc > 0 and False
        far = sorted(slots, key=lambda p: -_gc_dist(p, (4.5, 4.5)))
        feed_tiles = set(far[:feed_first])
        n_car = 0
        car_inv = None
        late = False
        if day >= GC_P['carrot_first'] and (day <= 26 or late):
            car_inv = self._carrot_book_at_harvest(obs, day, shops)
        if late:

            def late_units(crop, bonus):
                cd = _GC_CROPS[crop]
                ws = (cd['my'] + 1) // 2
                if day + cd['fy'] > 29:
                    return 0
                return min(cd['mx'], 1 + bonus * len([d for d in range(day + ws, day + cd['my'] + 1) if d <= 29]))
            uw = late_units('WHEAT', 2)
            uc = late_units('CARROT', 2 if GC_P['fert_carrots'] else 1)
            vw_late = uw * val['WHEAT'] - 10 - fert if uw else -1000000000.0
            if car_inv is None:
                car_inv = float(obs['market']['inventory']['CARROT'])
        for pos in slots:
            if pos in feed_tiles:
                out[pos] = 'WHEAT'
                continue
            if straw_room > 0 and (pos in free or straw_any):
                out[pos] = 'STRAWBERRY'
                straw_room -= 1
            elif placed_t < n_tom:
                out[pos] = 'TOMATO'
                placed_t += 1
            elif placed_m < n_mel:
                out[pos] = 'MELON'
                placed_m += 1
            elif late:
                pc = _gc_price('CARROT', int(car_inv + uc * n_car + 2))
                vc_late = uc * pc - 20 - (fert if GC_P['fert_carrots'] else 0) if uc else -1000000000.0
                if max(vc_late, vw_late) >= GC_P['late_plan_min']:
                    if vc_late >= vw_late:
                        out[pos] = 'CARROT'
                        n_car += 1
                    else:
                        out[pos] = 'WHEAT'
            elif car_inv is not None:
                q = car_inv + 4 * n_car + 2
                pc = _gc_price('CARROT', int(q))
                vc = (4 * pc - 20 - fert) / 3.0
                vw = v_wheat if day <= GC_P['wheat_last_plant'] else -1000000000.0
                if vc > 0.85 * vw and vc > 0:
                    out[pos] = 'CARROT'
                    n_car += 1
                elif day <= GC_P['wheat_last_plant']:
                    out[pos] = 'WHEAT'
            else:
                c = fill(day)
                if c:
                    out[pos] = c
        if n_car:
            pass
        if placed_m:
            pass
        n_tom = n_tom - placed_t
        if self.n_tomato_today:
            pass
        return out

    def _spawns(self, n_hires, farmer_pos):
        occ = {p: 0 for p in _GC_ACCESS}
        if tuple(farmer_pos) in occ:
            occ[tuple(farmer_pos)] += 1
        out = []
        for _ in range(n_hires):
            best = min(_GC_ACCESS, key=lambda p: (occ[p], _GC_ACCESS.index(p)))
            occ[best] += 1
            out.append(best)
        return out

    def _vrp(self, visits, h, starts=None, caps=None):

        def k_far(v):
            return (0 if v.must else 1, -(abs(v.pos[0] - 4.5) + abs(v.pos[1] - 4.5)) if v.must else -v.value / (len(v.acts) + 2.0))

        def k_ang(v):
            return (0 if v.must else 1, _gc_math.atan2(v.pos[1] - 4.5, v.pos[0] - 4.5) if v.must else -v.value / (len(v.acts) + 2.0))

        def k_val(v):
            return (0 if v.must else 1, -v.value / (len(v.acts) + 2.0))
        best = None
        for key in (k_far, k_ang, k_val):
            routes, spawns, unserved = self._vrp1(visits, h, key, starts, caps)
            nm = sum((1 for v in unserved if v.must))
            if self.final and False:
                nm = 0
            uv = sum((v.value for v in unserved))
            tc = sum((self._rcost(spawns[u], r) for u, r in enumerate(routes)))
            sc = (nm, uv, tc)
            if best is None or sc < best[0]:
                best = (sc, routes, spawns, unserved)
        routes, spawns, unserved = (best[1], best[2], best[3])
        if float(0.0) > 0:
            for u, r in enumerate(routes):
                if len(r) > 1 and any((self._prem_value(v) >= float(0.0) for v in r)):
                    cap = caps[u] if caps is not None else self._cap(u)
                    new = self._order_anim_first(spawns[u], r, cap)
                    if self._rcost(spawns[u], new) <= cap:
                        routes[u] = new
        return (routes, spawns, unserved)

    def _order_anim_first(self, start, vs, cap):
        plain = self._order(start, vs)
        dprem = float(0.0)
        pr = [v for v in vs if dprem > 0 and self._prem_value(v) >= dprem]
        an = [v for v in vs if v.tag == 'A' and v not in pr]
        if not (an or pr) or len(an) + len(pr) == len(vs):
            if pr and an:
                pass
            else:
                return plain
        head = self._order(start, pr) if pr else []
        pos = head[-1].pos if head else start
        a_ord = self._order(pos, an) if an else []
        pos = a_ord[-1].pos if a_ord else pos
        rest = self._order(pos, [v for v in vs if v not in pr and v not in an])
        mixed = head + a_ord + rest
        cm = self._rcost(start, mixed)
        if pr and cm <= cap:
            return mixed
        if cm <= min(cap, self._rcost(start, plain) + 2):
            return mixed
        return plain

    @staticmethod
    def _order(start, vs):
        if len(vs) <= 1:
            return list(vs)
        rem = list(vs)
        out = []
        pos = start
        while rem:
            j = min(range(len(rem)), key=lambda i: abs(pos[0] - rem[i].pos[0]) + abs(pos[1] - rem[i].pos[1]))
            v = rem.pop(j)
            out.append(v)
            pos = v.pos
        n = len(out)
        end = (4.5, 4.5)
        improved = True
        it = 0
        while improved and it < 8:
            improved = False
            it += 1
            for i in range(0, n - 1):
                a = start if i == 0 else out[i - 1].pos
                b = out[i].pos
                for j in range(i + 1, n):
                    c = out[j].pos
                    d = out[j + 1].pos if j + 1 < n else end
                    old = abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(c[0] - d[0]) + abs(c[1] - d[1])
                    new = abs(a[0] - c[0]) + abs(a[1] - c[1]) + abs(b[0] - d[0]) + abs(b[1] - d[1])
                    if new < old - 1e-09:
                        out[i:j + 1] = out[i:j + 1][::-1]
                        improved = True
                        b = out[i].pos
        return out

    def _rcost(self, start, r):
        t = 0
        if any((v.wheat for v in r)):
            t += 1
        if any((v.fert for v in r)):
            t += 1
        t += len({v.anim for v in r if v.anim})
        pos = start
        dprem = float(0.0)
        pv = 0.0
        last_p = None
        for v in r:
            t += abs(pos[0] - v.pos[0]) + abs(pos[1] - v.pos[1]) + len(v.acts)
            pos = v.pos
            if dprem > 0:
                if v.tag == 'S':
                    pv = 0.0
                    last_p = None
                else:
                    x = self._prem_value(v)
                    pv += x
                    if x > 0:
                        last_p = v.pos
        if dprem > 0 and pv >= dprem and (last_p is not None):
            t += self._ret(last_p) + 1
        return t

    @staticmethod
    def _ret(pos):
        a = _gc_near_access(pos)
        return abs(pos[0] - a[0]) + abs(pos[1] - a[1]) + 1

    def _vrp1(self, visits, h, order_key, starts=None, caps=None):
        n_units = 1 + h
        spawns = [(4, 4)] + self._spawns(h, (4, 4))
        if starts is not None:
            spawns = list(starts)
            n_units = len(spawns)
        d28r = None is not None
        fr = self.final and True or d28r
        s = 0 if not self.final else 5
        n0 = getattr(self, 'n0_hires', 9)
        if fr:
            fc = None if d28r else 19
            caps = [fc] + [fc if i < n0 else fc - 1 for i in range(h)]
        elif caps is None:
            caps = [23 - s] + [(23 if i < n0 else 22) - s for i in range(h)]
        ret = self._ret
        routes = [[] for _ in range(n_units)]
        costs = [0] * n_units
        flags = [[False, False, set()] for _ in range(n_units)]
        unserved = []
        dprem = float(0.0)
        pvals = [0.0] * n_units
        for v in sorted(visits, key=order_key):
            best = None
            xv = self._prem_value(v) if dprem > 0 else 0.0
            for u in range(n_units):
                r = routes[u]
                fl = flags[u]
                extra = (1 if v.wheat and (not fl[0]) else 0) + (1 if v.fert and (not fl[1]) else 0) + (1 if v.anim and v.anim not in fl[2] else 0)
                if dprem > 0 and xv > 0 and (pvals[u] < dprem) and (pvals[u] + xv >= dprem):
                    extra += self._ret(v.pos) + 1
                base = costs[u] + extra + len(v.acts)
                if base > caps[u]:
                    continue
                r_old = ret(r[-1].pos) if fr and r else 0
                prev = spawns[u]
                for i in range(len(r) + 1):
                    nxt = r[i].pos if i < len(r) else None
                    dd = abs(prev[0] - v.pos[0]) + abs(prev[1] - v.pos[1])
                    if nxt is not None:
                        dd += abs(v.pos[0] - nxt[0]) + abs(v.pos[1] - nxt[1]) - abs(prev[0] - nxt[0]) - abs(prev[1] - nxt[1])
                    c = base + dd
                    if fr:
                        r_new = ret(v.pos) if i == len(r) else r_old
                        if c + r_new <= caps[u] and (best is None or c + r_new - costs[u] - r_old < best[0]):
                            best = (c + r_new - costs[u] - r_old, u, i, c)
                    elif c <= caps[u] and (best is None or c - costs[u] < best[0]):
                        best = (c - costs[u], u, i, c)
                    if nxt is not None:
                        prev = nxt
            if best is None:
                unserved.append(v)
                continue
            _, u, i, c = best
            routes[u].insert(i, v)
            costs[u] = c
            pvals[u] += xv
            fl = flags[u]
            if v.wheat:
                fl[0] = True
            if v.fert:
                fl[1] = True
            if v.anim:
                fl[2].add(v.anim)
        for u in range(n_units):
            if len(routes[u]) > 2:
                new = self._order_anim_first(spawns[u], routes[u], caps[u])
                c = self._rcost(spawns[u], new)
                if fr:
                    if c + ret(new[-1].pos) <= caps[u]:
                        routes[u] = new
                        costs[u] = c
                elif c <= caps[u] or c <= costs[u] or (not GC_P['order_cap_fix']):
                    routes[u] = new
                    costs[u] = c
        if unserved:
            left = []
            for v in unserved:
                best = None
                for u in range(n_units):
                    r = routes[u]
                    for i in range(len(r) + 1):
                        rr = r[:i] + [v] + r[i:]
                        c = self._rcost(spawns[u], rr) + (ret(rr[-1].pos) if fr else 0)
                        if c <= caps[u] and (best is None or c < best[0]):
                            best = (c, u, i)
                if best is None:
                    left.append(v)
                else:
                    c, u, i = best
                    routes[u].insert(i, v)
                    costs[u] = self._rcost(spawns[u], routes[u])
            unserved = left
        return (routes, spawns, unserved)

    @staticmethod
    def _order(start, vs):
        if len(vs) <= 1:
            return list(vs)
        rem = list(vs)
        out = []
        pos = start
        while rem:
            j = min(range(len(rem)), key=lambda i: abs(pos[0] - rem[i].pos[0]) + abs(pos[1] - rem[i].pos[1]))
            v = rem.pop(j)
            out.append(v)
            pos = v.pos
        n = len(out)
        P = [v.pos for v in out]
        improved = True
        it = 0
        while improved and it < 8:
            improved = False
            it += 1
            for i in range(0, n - 1):
                a = start if i == 0 else P[i - 1]
                for j in range(i + 1, n):
                    b = P[i]
                    c = P[j]
                    old = abs(a[0] - b[0]) + abs(a[1] - b[1])
                    new = abs(a[0] - c[0]) + abs(a[1] - c[1])
                    if j + 1 < n:
                        d = P[j + 1]
                        old += abs(c[0] - d[0]) + abs(c[1] - d[1])
                        new += abs(b[0] - d[0]) + abs(b[1] - d[1])
                    if new < old:
                        out[i:j + 1] = out[i:j + 1][::-1]
                        P[i:j + 1] = P[i:j + 1][::-1]
                        improved = True
        return out

    def _route_and_hire(self, visits, cash, final, day):
        best = None
        lo = 0 if day == 576 // 24 or final else max(0, self.last_hires - 3)
        hi = GC_P['max_hands_final'] if final else 15
        while lo > 0 and sum((_gc_fib(q) for q in range(lo))) > cash - 20:
            lo -= 1
        for h in range(lo, hi + 1):
            cost = sum((_gc_fib(q) for q in range(h)))
            if h > 0 and cost > cash - 20:
                break
            routes, spawns, unserved = self._vrp(visits, h)
            keep_idx = [u for u in range(len(routes)) if u == 0 or routes[u]]
            if final and False:
                pen = sum((v.value for v in unserved))
            else:
                pen = sum((v.value + (100000.0 if v.must else 0.0) for v in unserved))
            ovf = 0
            if GC_P['ovf_hire'] and (not final):
                if GC_P['stop_v2']:
                    rr = [list(r) for r in routes]
                    ovf, popped = self._plan_stops(rr, spawns)
                    dprem = float(0.0)
                    if dprem > 0:
                        undel = sum((self._prem_after_stop(r) for r in rr if self._prem_after_stop(r) >= dprem))
                        pen += undel * GC_P['deliver_prem_w']
                        if undel > 0:
                            ovf += 1
                else:
                    _d, ovf, popped = self._plan_drops([list(r) for r in routes], spawns)
                pen += ovf * 100.0 + popped
            score = -pen - 0.6 * cost
            if best is None or score > best[0]:
                best = (score, h, routes, spawns, sum((v.value for v in unserved)))
                self._last_unserved = (sum((1 for v in unserved if v.must)), len(unserved), sorted({v.tag for v in unserved}))
            if not unserved and ovf == 0 and (best[1] < h):
                break
        return (best[2], best[1], best[3])

    def _compile(self, routes, spawns, hour0=True):
        qs = []
        for u, r in enumerate(routes):
            q = []
            if u == 0 and hour0:
                q.append((spawns[0], ['PASS'], None))
            wheat = sum((v.wheat for v in r))
            fert = sum((v.fert for v in r))
            if wheat:
                q.append((spawns[u], ['PICKUP', 'WHEAT', wheat], None))
            if fert:
                q.append((spawns[u], ['PICKUP', 'FERTILIZER', fert], None))
            for an in ('COW', 'SHEEP', 'GOOSE'):
                n = sum((1 for v in r if v.anim == an))
                if n:
                    q.append((spawns[u], ['PICKUP', an, n], None))
            drop_at = self.drop_at.get(u)
            for k, v in enumerate(r):
                for a in v.acts:
                    q.append((v.pos, list(a), v))
                if drop_at is not None and k == drop_at:
                    q.append((_gc_near_access(v.pos), ['DROP'], None))
            qs.append(q)
        return qs

    def _cap(self, u):
        s = 0 if not self.final else 5
        return (23 if u == 0 else 23 if u <= self.n0_hires else 22) - s

    @staticmethod
    def _stop_visit(pos):
        return _GcVisit(_gc_near_access(pos), [['DROP']], value=0.0, must=True, tag='S')

    @staticmethod
    def _eod_carry(r):
        c = 0
        for v in r:
            if v.tag == 'S':
                c = 0
            else:
                c += v.carry
        return c

    @staticmethod
    def _ins_delta(start, r, v):
        extra = len(v.acts)
        if v.wheat and (not any((x.wheat for x in r))):
            extra += 1
        if v.fert and (not any((x.fert for x in r))):
            extra += 1
        if v.anim and all((x.anim != v.anim for x in r)):
            extra += 1
        best_d, best_i = (None, 0)
        prev = start
        n = len(r)
        for i in range(n + 1):
            dd = abs(prev[0] - v.pos[0]) + abs(prev[1] - v.pos[1])
            if i < n:
                nx = r[i].pos
                dd += abs(v.pos[0] - nx[0]) + abs(v.pos[1] - nx[1]) - abs(prev[0] - nx[0]) - abs(prev[1] - nx[1])
                prev = nx
            if best_d is None or dd < best_d:
                best_d, best_i = (dd, i)
        return (best_d + extra, best_i)

    @staticmethod
    def _prem_value(v):
        g = v.gain or {}
        if g.get('prod') in _GC_PREMIUM:
            return float(g.get('units', v.carry)) * float(g.get('pv', 0.0))
        return 0.0

    def _prem_after_stop(self, r):
        val = 0.0
        for v in r:
            if v.tag == 'S':
                val = 0.0
            else:
                val += self._prem_value(v)
        return val

    def _plan_stops(self, routes, spawns, caps_in=None):
        room = GC_P['eod_room']
        if GC_P['d28_zero_reserve'] and getattr(self, 'day', 0) == 28:
            room = GC_P['eod_room_d28']
        popped = 0.0
        n = len(routes)
        caps = list(caps_in) if caps_in is not None else [self._cap(u) for u in range(n)]
        costs = [self._rcost(spawns[u], routes[u]) for u in range(n)]
        tried = set()
        dprem = float(0.0)
        for _it in range(3 * n + 5):
            total = sum((self._eod_carry(r) for r in routes))
            pending = [u for u in range(n) if dprem > 0 and u not in tried and (self._prem_after_stop(routes[u]) >= dprem)]
            if total <= room and (not pending):
                break
            best = None
            for u in range(n):
                r = routes[u]
                if u in tried or not r:
                    continue
                if total <= room and u not in pending:
                    continue
                if u not in pending and self._eod_carry(r) < GC_P['deliver_min']:
                    continue
                last_s = max((i for i, v in enumerate(r) if v.tag == 'S'), default=-1)
                carried = 0
                t = 0
                pos = spawns[u]
                if any((v.wheat for v in r)):
                    t += 1
                if any((v.fert for v in r)):
                    t += 1
                t += len({v.anim for v in r if v.anim})
                pcar = 0.0
                kp = max((i for i, v in enumerate(r) if i > last_s and self._prem_value(v) >= dprem), default=None) if u in pending else None
                for k, v in enumerate(r):
                    t += abs(pos[0] - v.pos[0]) + abs(pos[1] - v.pos[1]) + len(v.acts)
                    pos = v.pos
                    if k <= last_s:
                        continue
                    carried += v.carry
                    if dprem > 0:
                        pcar += self._prem_value(v)
                    if kp is not None and k != kp:
                        continue
                    if carried < GC_P['deliver_min'] and (not (u in pending and pcar >= dprem)):
                        continue
                    a = _gc_near_access(v.pos)
                    back = abs(v.pos[0] - a[0]) + abs(v.pos[1] - a[1])
                    if t + back + 1 > caps[u] - 1:
                        continue
                    if k + 1 < len(r):
                        nx = r[k + 1].pos
                        extra = back + 1 + abs(a[0] - nx[0]) + abs(a[1] - nx[1]) - (abs(v.pos[0] - nx[0]) + abs(v.pos[1] - nx[1]))
                    else:
                        extra = back + 1
                    sc = (carried + pcar / 50.0) / (extra + 0.5)
                    if best is None or sc > best[0]:
                        best = (sc, u, k, extra)
            if best is None:
                break
            _, u, k, extra = best
            if not GC_P['multi_stop']:
                tried.add(u)
            r2 = routes[u][:k + 1] + [self._stop_visit(routes[u][k].pos)] + routes[u][k + 1:]
            c2 = costs[u] + extra
            moved = []
            pv = 0.0
            guard = 0
            while c2 > caps[u] and guard < 15:
                guard += 1
                cands = []
                for i in range(k + 2, len(r2)):
                    v = r2[i]
                    if v.tag == 'S':
                        continue
                    sav = c2 - self._rcost(spawns[u], r2[:i] + r2[i + 1:])
                    cands.append((sav, i))
                if not cands:
                    break
                cands.sort(key=lambda x: -x[0])
                done = False
                for sav, i in cands[:6]:
                    v = r2[i]
                    bw = None
                    for w in range(n):
                        if w == u:
                            continue
                        d, j = self._ins_delta(spawns[w], routes[w], v)
                        if costs[w] + d <= caps[w] and (bw is None or d < bw[0]):
                            bw = (d, w, j)
                    if bw is not None:
                        d, w, j = bw
                        routes[w] = routes[w][:j] + [v] + routes[w][j:]
                        costs[w] += d
                        moved.append((w, v))
                        r2 = r2[:i] + r2[i + 1:]
                        c2 = self._rcost(spawns[u], r2)
                        done = True
                        break
                if not done:
                    opt = [i for i in range(k + 2, len(r2)) if not r2[i].must and r2[i].tag != 'S']
                    if not opt:
                        break
                    j = min(opt, key=lambda i: r2[i].value / (len(r2[i].acts) + 1.0))
                    pv += r2[j].value
                    r2 = r2[:j] + r2[j + 1:]
                    c2 = self._rcost(spawns[u], r2)
            if c2 <= caps[u]:
                routes[u] = r2
                costs[u] = c2
                popped += pv
            else:
                tried.add(u)
                for w, v in moved:
                    routes[w] = [x for x in routes[w] if x is not v]
                    costs[w] = self._rcost(spawns[w], routes[w])
        return (max(0, sum((self._eod_carry(r) for r in routes)) - room), popped)

    def _plan_drops(self, routes, spawns):
        drop_at = {}
        room = GC_P['eod_room']
        carried = [sum((v.carry for v in r)) for r in routes]
        total = sum(carried)
        done = set()
        popped = 0.0
        guard = 0
        while (total > room or False) and guard < 40:
            guard += 1
            best = None
            for u, r in enumerate(routes):
                if u in done or not r or carried[u] < GC_P['deliver_min']:
                    continue
                cap = 23 if u == 0 else 23 if u <= self.n0_hires else 22
                k, extra, got = self._drop_best(spawns[u], r, cap + 99)
                if k is None:
                    continue
                sc = got / (extra + 0.5)
                if best is None or sc > best[0]:
                    best = (sc, u, k, extra, got)
            if best is None:
                break
            _, u, k, extra, got = best
            cap = 23 if u == 0 else 23 if u <= self.n0_hires else 22
            r = routes[u]
            while self._rcost(spawns[u], r) + extra > cap:
                opt = [i for i, v in enumerate(r) if not v.must and i > k]
                if not opt:
                    break
                j = min(opt, key=lambda i: r[i].value / (len(r[i].acts) + 1.0))
                popped += r[j].value
                r.pop(j)
            if self._rcost(spawns[u], r) + extra <= cap:
                drop_at[u] = k
                total -= got
            done.add(u)
        return (drop_at, max(0, total - room), popped)

    def _drop_best(self, spawn, r, cap):
        base = self._rcost(spawn, r)
        best = None
        carried = 0
        for k, v in enumerate(r):
            carried += v.carry
            if carried < GC_P['deliver_min']:
                continue
            a = _gc_near_access(v.pos)
            back = abs(v.pos[0] - a[0]) + abs(v.pos[1] - a[1])
            if k + 1 < len(r):
                nx = r[k + 1].pos
                extra = back + 1 + abs(a[0] - nx[0]) + abs(a[1] - nx[1]) - (abs(v.pos[0] - nx[0]) + abs(v.pos[1] - nx[1]))
            else:
                extra = back + 1
            if base + extra > cap:
                continue
            prem = sum((x.carry for x in r[:k + 1] if x.tag == 'A'))
            sc = (carried + GC_P['prem_w'] * prem) / (extra + 0.5)
            if best is None or sc > best[0]:
                best = (sc, k, extra, carried)
        if best is None:
            return (None, 0, 0)
        return (best[1], best[2], best[3])

    def _useful(self, act, tile, inv, seeds, planting, shed, room):
        op = act[0]
        if op == 'PASS':
            return True
        if op == 'PICKUP':
            return shed.get(act[1], 0) > 0
        if op == 'DROP':
            n = sum((int(x) for x in inv.values()))
            return n > 0 and room[0] >= n
        if op == 'PLACE':
            return inv.get(act[1], 0) > 0 and isinstance(tile, dict) and (tile.get('kind') == _GC_ANIM[act[1]]['st']) and ('animal' not in tile)
        if tile == 'LOCKED':
            return False
        if op == 'PLANT':
            return tile is None and seeds.get(act[1], 0) - planting.get(act[1], 0) > 0
        if op == 'DIG':
            return tile is not None and (not (isinstance(tile, dict) and 'animal' in tile))
        if op in ('BUILD_COOP', 'BUILD_PASTURE'):
            return tile is None
        if not isinstance(tile, dict):
            return False
        k = tile.get('kind')
        if op == 'WATER':
            return k == 'PLANT' and (not tile.get('watered_today'))
        if op == 'HARVEST':
            return int(tile.get('yield_units', 0) or 0) > 0 and (k == 'PLANT' or 'animal' in tile)
        if op == 'FERTILIZE':
            return k == 'PLANT' and inv.get('FERTILIZER', 0) > 0
        if op == 'FEED':
            return 'animal' in tile and (not tile.get('fed_today')) and (inv.get('WHEAT', 0) > 0)
        if op == 'CARE':
            return 'animal' in tile and (not tile.get('cared_today'))
        if op == 'COLLECT_FERTILIZER':
            return 'animal' in tile and bool(tile.get('fertilizer_available'))
        return True

    def _trim_queue(self, q, pos, turns_left):

        def cost(qq):
            t = 0
            p = pos
            for tgt, a, v in qq:
                t += abs(p[0] - tgt[0]) + abs(p[1] - tgt[1]) + 1
                p = tgt
            return t
        guard = 0
        while q and cost(q) > turns_left and (guard < 30):
            guard += 1
            opt = {id(v): v for _, _, v in q if v is not None and (not v.must)}
            if not opt:
                break
            worst = min(opt.values(), key=lambda v: v.value / (len(v.acts) + 1.0))
            q[:] = [it for it in q if it[2] is not worst]

    def _dispatch(self, u, pos, inv, turns_left, tiles, sim, seeds, shed, claimed, day, hour):
        if turns_left <= 1:
            return None
        cache = getattr(self, '_dcache', None)
        if cache is None or cache[0] != (day, hour):
            cands = []
            for y in range(10):
                for x in range(10):
                    key = (x, y)
                    t = sim[key] if key in sim else tiles[y][x]
                    if not isinstance(t, dict):
                        continue
                    if t.get('kind') == 'PLANT':
                        v = self._plant_visit(key, t, day, self.val, self.final)
                    elif t.get('animal'):
                        v = self._animal_visit(key, t, day, self.val, self.final)
                    else:
                        v = None
                    if v is None:
                        continue
                    acts = []
                    for a in v.acts:
                        op = a[0]
                        if op == 'WATER' and t.get('watered_today'):
                            continue
                        if op == 'FEED' and t.get('fed_today'):
                            continue
                        if op == 'CARE' and t.get('cared_today'):
                            continue
                        if op == 'COLLECT_FERTILIZER' and (not t.get('fertilizer_available')):
                            continue
                        if op == 'HARVEST' and int(t.get('yield_units', 0) or 0) <= 0:
                            continue
                        if op in ('PLANT', 'DIG', 'BUILD_COOP', 'BUILD_PASTURE', 'PLACE'):
                            continue
                        acts.append(list(a))
                    if not acts:
                        continue
                    val = v.value * len(acts) / max(1, len(v.acts))
                    if any((a[0] == 'CARE' for a in acts)) and (not t.get('fed_today')) and (not any((a[0] == 'FEED' for a in acts))):
                        acts = [a for a in acts if a[0] != 'CARE']
                        if not acts:
                            continue
                    cands.append((key, acts, val, v.must))
            self._dcache = ((day, hour), cands)
            cache = self._dcache
        best = None
        for key, acts, val, must in cache[1]:
            if key in claimed:
                continue
            need_w = any((a[0] == 'FEED' for a in acts)) and inv.get('WHEAT', 0) <= 0
            need_f = any((a[0] == 'FERTILIZE' for a in acts)) and inv.get('FERTILIZER', 0) <= 0
            acts2 = acts
            if need_f:
                acts2 = [a for a in acts2 if a[0] != 'FERTILIZE']
            detour = 0
            pick = None
            if need_w:
                if shed.get('WHEAT', 0) <= 0:
                    acts2 = [a for a in acts2 if a[0] not in ('FEED', 'CARE')]
                else:
                    a0 = _gc_near_access(pos)
                    detour = _gc_dist(pos, a0) + 1 + _gc_dist(a0, key) - _gc_dist(pos, key)
                    pick = a0
            if not acts2:
                continue
            cost = _gc_dist(pos, key) + detour + len(acts2)
            if cost > turns_left:
                continue
            v2 = val if acts2 is acts else val * len(acts2) / max(1, len(acts))
            if v2 < GC_P['dispatch_min_value']:
                continue
            sc = (10000.0 if must else 0) + v2 / (cost + 0.5)
            if best is None or sc > best[0]:
                best = (sc, key, acts2, pick)
        if best is None:
            return None
        _, key, acts2, pick = best
        q = []
        if pick is not None:
            q.append((pick, ['PICKUP', 'WHEAT', 2], None))
        for a in acts2:
            q.append((key, a, None))
        return q

    def _rematch(self, farm):
        n0 = getattr(self, 'n0_hires', 10)
        hands = [tuple(p) for p in farm['hands']]
        late = [u for u in range(n0 + 1, len(hands) + 1) if u in self.queues]
        if len(late) < 2:
            return

        def qcost(q, start):
            t = 0
            p = start
            for tgt, a, v in q:
                if a[0] in ('PICKUP', 'DROP'):
                    tg = p if p in _GC_ACCESS_SET else _gc_near_access(p)
                else:
                    tg = tgt
                t += abs(p[0] - tg[0]) + abs(p[1] - tg[1]) + 1
                p = tuple(tg)
            return t
        qs = [self.queues[u] for u in late]
        pos = [hands[u - 1] for u in late]
        import itertools
        best = None
        if len(late) <= 6:
            for perm in itertools.permutations(range(len(late))):
                c = sum((max(0, qcost(qs[perm[i]], pos[i]) - 22) * 100 + qcost(qs[perm[i]], pos[i]) for i in range(len(late))))
                if best is None or c < best[0]:
                    best = (c, perm)
            perm = best[1]
        else:
            perm = list(range(len(late)))
        for i, u in enumerate(late):
            self.queues[u] = qs[perm[i]]

    def _courier(self, positions, invs, tiles, shed, hour):
        turns_left = 23 - hour + 1
        res = sum((int(v) for v in self.reserve.values()))
        shed_eod = min(sum((int(v) for v in shed.values())), res)
        hn = {}
        info = []
        total = shed_eod
        for u, pos in enumerate(positions):
            pos = tuple(pos)
            inv = invs[u] if u < len(invs) else {}
            c = sum((int(x) for x in inv.values()))
            c_sell = c
            q = self.queues.get(u) or []
            last_drop = max((i for i, it in enumerate(q) if it[1][0] == 'DROP'), default=-1)
            fut = 0
            for i, (tgt, a, v) in enumerate(q):
                if i <= last_drop:
                    continue
                if a[0] == 'HARVEST':
                    t = tiles[tgt[1]][tgt[0]]
                    fut += int(t.get('yield_units', 0) or 0) if isinstance(t, dict) else 0
                elif a[0] == 'COLLECT_FERTILIZER':
                    fut += 1
            eod = fut + (0 if last_drop >= 0 else c)
            total += eod
            if last_drop < 0 and c_sell >= GC_P['courier_min']:
                qc = 0
                pp = pos
                for tgt, a, v in q:
                    qc += abs(pp[0] - tgt[0]) + abs(pp[1] - tgt[1]) + 1
                    pp = tuple(tgt)
                acc = pos if pos in _GC_ACCESS_SET else _gc_near_access(pos)
                d0 = abs(pos[0] - acc[0]) + abs(pos[1] - acc[1])
                if q:
                    nx = q[0][0]
                    detour = d0 + 1 + abs(acc[0] - nx[0]) + abs(acc[1] - nx[1]) - (abs(pos[0] - nx[0]) + abs(pos[1] - nx[1]))
                else:
                    detour = d0 + 1
                info.append((detour / float(c_sell), u, acc, c_sell, qc, detour))
        limit = 100 - GC_P['courier_margin']
        if total <= limit:
            return
        for _sc, u, acc, c, qc, detour in sorted(info):
            if total <= limit:
                break
            if qc + detour > turns_left or detour > GC_P['courier_max_detour']:
                continue
            q = self.queues.get(u) or []
            self.queues[u] = [(acc, ['DROP'], None)] + list(q)
            total -= c

    def _step_unit(self, u, pos, tiles, inv, seeds, planting, sim, shed, room, hour=0):
        q = self.queues.get(u)
        if q and hour >= GC_P['trim_hour']:
            self._trim_queue(q, pos, 23 - hour)
        while q:
            tgt, act, _v = q[0]
            if GC_P['shed_any'] and act[0] in ('PICKUP', 'DROP'):
                tgt = tuple(pos) if tuple(pos) in _GC_ACCESS_SET else _gc_near_access(pos)
            if tuple(pos) != tuple(tgt):
                dx = tgt[0] - pos[0]
                dy = tgt[1] - pos[1]
                if dx:
                    return ['EAST'] if dx > 0 else ['WEST']
                return ['SOUTH'] if dy > 0 else ['NORTH']
            key = (pos[0], pos[1])
            tile = sim[key] if key in sim else tiles[pos[1]][pos[0]]
            if act[0] == 'DROP' and sum((int(x) for x in inv.values())) > room[0]:
                self._drop_wait = getattr(self, '_drop_wait', 0) + sum((int(x) for x in inv.values()))
                return ['PASS']
            if self._useful(act, tile, inv, seeds, planting, shed, room):
                q.pop(0)
                if act[0] == 'PLANT':
                    planting[act[1]] = planting.get(act[1], 0) + 1
                if act[0] == 'PICKUP':
                    n = int(act[2]) if len(act) >= 3 else 1
                    shed[act[1]] = max(0, shed.get(act[1], 0) - n)
                if act[0] == 'DROP':
                    n = sum((int(x) for x in inv.values()))
                    room[0] -= n
                    for k2, n2 in inv.items():
                        shed[k2] = shed.get(k2, 0) + int(n2)
                return act
            q.pop(0)
        return ['PASS']

    def act(self, obs):
        hour = int(obs['hour'])
        day = int(obs['day'])
        try:
            self._mk_track(obs)
        except Exception:
            pass
        me = self.me
        farm = obs['farms'][me]
        priv = obs['private']
        if self.day_plan != day:
            self.plan_day(obs)
            self.day_plan = day
            self.queues = {u: q for u, q in enumerate(self._compile(self.routes, self.spawns))}
        tiles = farm['tiles']
        self._drop_wait = 0
        if GC_P['rematch'] and hour == 2 and (not getattr(self, '_rematched', None) == day):
            self._rematched = day
            self._rematch(farm)
        self._mid_orders = []
        seeds = dict(priv['seeds'])
        shed = {k: int(v) for k, v in dict(priv['shed']).items()}
        room = [100 - sum(shed.values())]
        invs = list(priv['inventories'])
        planting = {}
        sim = {}
        positions = [farm['farmer']] + list(farm['hands'])
        if GC_P['courier'] and hour >= GC_P['courier_hour'] and (not self.final):
            self._courier(positions, invs, tiles, shed, hour)
        units = []
        claimed = {tgt for qq in self.queues.values() for tgt, _a, _v in qq or []}
        for u, pos in enumerate(positions):
            inv = dict(invs[u]) if u < len(invs) else {}
            if GC_P['final_flush'] and self.final and (not self.queues.get(u)) and (sum((int(x) for x in inv.values())) > 0) and (hour <= 22):
                self.queues[u] = [(_gc_near_access(tuple(pos)), ['DROP'], None)]
            if GC_P['dispatch'] and (not self.queues.get(u)) and (hour >= 1) and (not (self.final and hour >= 18)):
                nq = self._dispatch(u, pos, inv, 23 - hour + 1, tiles, sim, seeds, shed, claimed, day, hour)
                if nq:
                    if GC_P['final_flush'] and self.final:
                        last = nq[-1][0]
                        nq = nq + [(_gc_near_access(tuple(last)), ['DROP'], None)]
                    self.queues[u] = nq
                    claimed.update((tgt for tgt, _a, _v in nq))
            a = self._step_unit(u, pos, tiles, inv, seeds, planting, sim, shed, room, hour)
            key = (pos[0], pos[1])
            if a[0] in ('WATER', 'CARE', 'FEED', 'HARVEST', 'COLLECT_FERTILIZER') and isinstance(tiles[pos[1]][pos[0]], dict):
                t2 = dict(sim[key] if key in sim else tiles[pos[1]][pos[0]])
                if a[0] == 'WATER':
                    t2['watered_today'] = True
                elif a[0] == 'CARE':
                    t2['cared_today'] = True
                elif a[0] == 'FEED':
                    t2['fed_today'] = True
                elif a[0] == 'HARVEST':
                    t2['yield_units'] = 0
                elif a[0] == 'COLLECT_FERTILIZER':
                    t2['fertilizer_available'] = False
                sim[key] = t2
            units.append(a)
        carried = 0
        self.carried_items = {}
        for u in range(len(positions)):
            if units[u][0] == 'DROP':
                continue
            inv = dict(invs[u]) if u < len(invs) else {}
            carried += sum((int(x) for x in inv.values()))
            for k2, n2 in inv.items():
                self.carried_items[k2] = self.carried_items.get(k2, 0) + int(n2)
        market = self._market(obs, shed, carried, hour, day)[:10]
        try:
            self._mk_store(obs, shed, market)
        except Exception:
            pass
        if hour == 23:
            left = [(u, len(q), sum((1 for _, a, _v in q if a[0] not in ('DROP',)))) for u, q in self.queues.items() if q]
        return {'farmer': units[0], 'hands': units[1:], 'market': market[:10]}

    @staticmethod
    def _town_draw(shops, step):
        draw = {}
        if step % 4 == 0:
            for sh in shops:
                items = _GC_SHOPS.get(sh, [])
                for it in items:
                    draw[it] = draw.get(it, 0) + (2 if len(items) == 1 else 1)
        if step % 24 == 0:
            for it in _GC_PRODUCTS:
                if it != 'FERTILIZER':
                    draw[it] = draw.get(it, 0) + 1
        return draw

    def _mk_track(self, obs):
        step = int(obs['step'])
        inv = obs['market']['inventory']
        prev = self._mk_prev
        if prev is None or prev['step'] != step - 1:
            return
        draw = self._town_draw(prev['shops'], step - 1)
        for p in _GC_PRODUCTS:
            if prev['px'].get(p, 0) <= 1:
                continue
            resid = int(inv[p]) - int(prev['inv'][p]) + draw.get(p, 0) - prev['sold'].get(p, 0) + prev['bought'].get(p, 0)
            if resid >= GC_P['rival_min_lot']:
                self.rival_sales.setdefault(p, []).append(((step - 1) // 24, (step - 1) % 24, resid))

    def _mk_store(self, obs, shed, market):
        sold = {}
        bought = {}
        for o in market:
            if not o or len(o) < 3:
                continue
            if o[0] == 'SELL':
                sold[o[1]] = sold.get(o[1], 0) + int(o[2])
            elif o[0] == 'BUY_PRODUCT':
                bought[o[1]] = bought.get(o[1], 0) + int(o[2])
        for p in list(sold):
            sold[p] = min(sold[p], max(0, int(shed.get(p, 0))))
        m = obs['market']
        self._mk_prev = {'step': int(obs['step']), 'inv': {p: int(m['inventory'][p]) for p in _GC_PRODUCTS}, 'px': {p: int(m['prices'][p]) for p in _GC_PRODUCTS}, 'shops': list(_gc_get(obs['town'], 'unlocked_shops', []) or []), 'sold': sold, 'bought': bought}

    def _floor_recovers(self, obs, p, fl, day):
        return True
        inv = int(obs['market']['inventory'][p])
        k = 0
        while k < 400 and _gc_price(p, inv - k) < fl:
            k += 1
        shops = list(_gc_get(obs['town'], 'unlocked_shops', []) or [])
        per_day = 0 if p == 'FERTILIZER' else 1
        for sh in shops:
            items = _GC_SHOPS.get(sh, [])
            if p in items:
                per_day += 6 * (2 if len(items) == 1 else 1)
        return per_day > 0 and k <= per_day * GC_P['floor_wait_days']

    def _rival_wait(self, p, day, hour):
        lo = day - GC_P['rival_days']
        hours = sorted({h for d, h, q in self.rival_sales.get(p, ()) if d >= lo})
        if not hours:
            return None
        cur = day * 24 + hour
        cands = [day * 24 + h for h in hours if day * 24 + h >= cur + 1] + [(day + 1) * 24 + h for h in hours]
        return max(0, min(cands) - 1 - cur)

    def _unit_cap(self, obs, p, n, before=0):
        fr = GC_P['unit_floor_frac']
        if fr <= 0 or p not in GC_P['unit_floor_items'] or int(obs['step']) >= GC_P['unit_floor_step'] or (n <= 0):
            return n
        fl = fr * _GC_MKT[p][0]
        i0 = int(obs['market']['inventory'][p]) + before
        k = 0
        while k < n and _gc_price(p, i0 + k) >= fl:
            k += 1
        if k < n:
            pass
        return k

    def _market(self, obs, shed, carried, hour, day):
        step = int(obs['step'])
        sells = self._sell_orders(obs, shed, carried, hour, day, step)
        if GC_P['tick_defer'] and hour % 4 == 0 and (hour > 0) and (day < GC_P['tick_last_day']):
            sells = [o for o in sells if o[0] != 'SELL' or (GC_P['tick_keep_due'] and o[1] in self._due)]
        prem = [o for o in sells if o[1] in _GC_PREMIUM]
        rest = [o for o in sells if o[1] not in _GC_PREMIUM]
        if hour == 0:
            fixed = list(self.orders0)
            h0 = max(0, min(self.hires_planned, 10 - len(fixed)))
            self.hires_left = self.hires_planned - h0
            orders = fixed + [['HIRE']] * h0
            have = {o[1] for o in fixed if o and o[0] == 'SELL'}
            orders += [o for o in prem if o[1] not in have and o[1] in self._due]
            return orders[:10]
        mid = list(getattr(self, '_mid_orders', []) or [])
        if mid:
            return (mid + prem + rest)[:10]
        if hour == 1:
            h1 = min(self.hires_left, 10 - len(self.orders1))
            self.hires_left -= h1
            return ([['HIRE']] * h1 + list(self.orders1) + prem + rest)[:10]
        if self.hires_left and hour == 2:
            h2 = min(self.hires_left, 10)
            self.hires_left = 0
            return ([['HIRE']] * h2 + prem + rest)[:10]
        return prem + rest

    def _dp_sell(self, obs, p, n, step, day, hour, shops, cap_night=None):
        cap = int(GC_P['mkt_dp_cap'])
        K = int(GC_P['mkt_dp_periods'])
        if n > cap + 30:
            return n - cap
        rd = int(GC_P['mkt_dp_rival_days'])
        byh = {}
        for d, h, q in self.rival_sales.get(p, ()):
            if day - rd <= d < day or (d == day and h < hour):
                byh[h] = byh.get(h, 0.0) + q
        ndays = float(max(1, min(rd, day)))
        rival_h = {h: v / ndays for h, v in byh.items()}
        rv = lambda s2: rival_h.get((s2 + 1) % 24, 0.0)
        ad = globals().get('_AD_STATE')
        if step % 4 != 1 and step > 0:
            nxt = step + (1 - step) % 4
            if sum((rv(s2) for s2 in range(step, nxt))) < float(3.0):
                return None
        inv0 = int(obs['market']['inventory'][p])
        dsteps = [step + 4 * k for k in range(K + 1) if step + 4 * k <= 718]
        carried = int(getattr(self, 'carried_items', {}).get(p, 0))
        exo = []
        stock = []
        rq = []
        I = float(inv0)
        cum = n
        for k, t in enumerate(dsteps):
            if k > 0:
                for s2 in range(dsteps[k - 1], t):
                    I -= self._town_draw(shops, s2).get(p, 0)
                    I += rv(s2)
                if dsteps[k - 1] // 24 < t // 24:
                    cum += carried
            exo.append(I)
            stock.append(cum)
            rq.append(int(round(sum((rv(s2) for s2 in range(t, min(t + 4, 719)))))))
        U = stock[-1]
        caps = [cap] * len(dsteps)
        if cap_night is not None:
            for k in range(len(dsteps) - 1):
                if dsteps[k] // 24 < dsteps[k + 1] // 24:
                    caps[k] = max(0, min(cap, int(cap_night)))
        rmax = max(rq) if rq else 0
        imin = int(min(exo)) - 2
        imax = int(max(exo)) + U + rmax + 2
        pr = [0.0]
        for i in range(imin, imax + 1):
            pr.append(pr[-1] + _gc_price(p, i))
        w = float(1.5)
        NEG = -1e+18
        Kd = len(dsteps)
        V = [0.0] * (U + 1)
        best0 = 0
        for k in range(Kd - 1, -1, -1):
            Vn = [NEG] * (U + 1)
            base = int(exo[k]) - imin
            r = rq[k]
            for c in range(min(stock[k], U) + 1):
                avail = stock[k] - c
                best = NEG
                bx = 0
                lo_x = avail if k == Kd - 1 else max(0, avail - caps[k])
                for x in range(lo_x, avail + 1):
                    a = base + c
                    v = pr[a + x] - pr[a] + V[c + x]
                    if w and r:
                        v -= w * (pr[a + x + r] - pr[a + x])
                    if v > best:
                        best = v
                        bx = x
                Vn[c] = best
                if k == 0 and c == 0:
                    best0 = bx
            V = Vn
        return int(best0)

    def _dp_room(self, obs, shed, carried):
        tiles = obs['farms'][self.me]['tiles']
        invs = list(obs['private'].get('inventories', []) or [])
        eod = 0
        for u, q in self.queues.items():
            q = q or []
            last_drop = max((i for i, it in enumerate(q) if it[1][0] == 'DROP'), default=-1)
            if last_drop < 0 and u < len(invs):
                eod += sum((int(x) for x in dict(invs[u]).values()))
            for i, (tgt, a, _v) in enumerate(q):
                if i <= last_drop:
                    continue
                if a[0] == 'HARVEST':
                    t = tiles[tgt[1]][tgt[0]]
                    eod += int(t.get('yield_units', 0) or 0) if isinstance(t, dict) else 0
                elif a[0] == 'COLLECT_FERTILIZER':
                    eod += 1
        for u in range(len(invs)):
            if u not in self.queues:
                eod += sum((int(x) for x in dict(invs[u]).values()))
        kept = sum((min(int(shed.get(p, 0)), int(self.reserve.get(p, 0))) for p in _GC_PRODUCTS if p not in GC_P['mkt_dp_prods']))
        kept += 0
        return int(90) - kept - eod

    def _sell_orders(self, obs, shed, carried, hour, day, step):
        inv = obs['market']['inventory']
        out = []
        reserve = self.reserve
        last = step >= 716 or day >= 29
        ci = getattr(self, 'carried_items', {})
        total_shed = sum((int(v) for v in shed.values()))
        pressure = total_shed + carried > GC_P['drip_room']
        held = {}
        dp_budget = None
        if not last:
            try:
                dp_budget = self._dp_room(obs, shed, carried)
            except Exception as e:
                dp_budget = None
            if dp_budget is not None:
                pass
        self._due = set()
        val_now = {q: _gc_price(q, inv[q]) for q in _GC_PRODUCTS}
        urgent = None is not None
        for p in _GC_PRODUCTS:
            n = int(shed.get(p, 0))
            a = 0
            if a > 0:
                a = min(a, n)
                if last or val_now.get(p, 0) >= GC_P['arb_target'].get(p, 150):
                    self.arb[p] = 0
                else:
                    n -= a
            if not last:
                keep = int(reserve.get(p, 0))
                if hour >= GC_P['reserve_release_hour']:
                    keep = max(0, keep - int(ci.get(p, 0)))
                n -= keep
            if n <= 0:
                continue
            lot = None
            if lot and (not last) and (not pressure) and (day < 29):
                n = min(n, lot)
            if urgent:
                out.append(['SELL', p, n])
                continue
            if p in GC_P['mkt_dp_prods'] and (not last) and (day <= 28) and (day >= 0):
                try:
                    x = self._dp_sell(obs, p, n, step, day, hour, list(_gc_get(obs['town'], 'unlocked_shops', []) or []), cap_night=None if dp_budget is None else max(0, dp_budget))
                except Exception as e:
                    x = n
                if x is None:
                    held[p] = held.get(p, 0) + n
                    continue
                if x < n:
                    held[p] = held.get(p, 0) + (n - x)
                    if dp_budget is not None:
                        dp_budget -= n - x
                    n = x
                if n <= 0:
                    continue
                out.append(['SELL', p, n])
                continue
            fl = GC_P['sell_floor'].get(p) if GC_P['sell_floor'] else None
            if fl and (not last) and (day <= GC_P['floor_last_day']) and (val_now.get(p, 0) < fl) and self._floor_recovers(obs, p, fl, day):
                held[p] = n
                continue
            if fl and GC_P['floor_marginal'] and (not last) and (day <= GC_P['floor_last_day']) and self._floor_recovers(obs, p, fl, day):
                k = 0
                i0 = int(inv[p])
                while k < n and _gc_price(p, i0 + k) >= fl:
                    k += 1
                if k < n:
                    held[p] = n - k
                    n = k
                    if n <= 0:
                        continue
            if p in GC_P['timed'] and (not last) and (day >= 0):
                w = self._rival_wait(p, day, hour)
                if w is not None and 0 < w <= GC_P['hold_max']:
                    held[p] = held.get(p, 0) + n
                    continue
                if w == 0:
                    self._due.add(p)
            if GC_P['unit_floor_frac'] > 0:
                k = self._unit_cap(obs, p, n)
                if k < n:
                    held[p] = held.get(p, 0) + (n - k)
                    n = k
                    if n <= 0:
                        continue
            out.append(['SELL', p, n])
        if held:
            total = sum((int(v) for v in shed.values())) - sum((int(o[2]) for o in out))
            over = max(total + (carried if hour >= 20 else 0) - (100 if hour >= 20 else GC_P['hold_room']), total + getattr(self, '_drop_wait', 0) - 100)
            for p in sorted(held, key=lambda q: -val_now.get(q, 0) / float(_GC_MKT[q][0])):
                if over <= 0:
                    break
                k = min(over, held[p])
                out.append(['SELL', p, k])
                over -= k
                held[p] -= k
        self._held_now = {p: q for p, q in held.items() if q > 0}
        if hour == 23 and (not last):
            total = sum((int(v) for v in shed.values())) - sum((int(o[2]) for o in out))
            over = total + carried - 100
            if over > 0:
                for p in ('FERTILIZER', 'WHEAT'):
                    k = min(over, int(shed.get(p, 0)) - sum((int(o[2]) for o in out if o[1] == p)))
                    if k > 0:
                        out.append(['SELL', p, k])
                        over -= k
        return out
_GC = GoldCtl()
_GC_DIV_SAVED = {}
_GC_RICH = {}
_ARB_STATE = {}
_SANX = {}
_SANX_TILES = sorted([(x, y) for y in range(5, 10) for x in range(5, 10)], key=lambda p: (abs(p[0] - 4.5) + abs(p[1] - 4.5), p[1], p[0]))
_SANX_MASK = {'on': False}
_AD_SIG_ORIG = globals().get('_ad_sig')

def _ad_sig(farm):
    out = _AD_SIG_ORIG(farm)
    if _SANX_MASK['on'] and GC_P['sanx_mask_adapt'] and (len(out) == 100):
        out = list(out)
        for y in range(5, 10):
            for x in range(5, 10):
                out[y * 10 + x] = '#'
    return out
_SANX_PARENT = agent

def agent(observation, configuration=None):
    action = _SANX_PARENT(observation, configuration)
    return action
_ARB_PARENT = agent

def agent(observation, configuration=None):
    action = _ARB_PARENT(observation, configuration)
    return action
_GC_PARENT = agent
_STRAW_CAP_STATE = {}

def _v219x_size(obs):
    me = int(obs['player'])
    inv0 = float(obs['market']['inventory']['TOMATO'])
    shops = list(_gc_get(obs['town'], 'unlocked_shops', []) or [])
    k_now = sum((1 for sh in shops if sh in ('PIZZA_SHOP', 'FARMERS_MARKET')))
    n_shops = len(shops)
    u = GC_P['v219x_units']
    rsup = {}
    n_opp = 0
    for row in obs['farms'][1 - me]['tiles']:
        for t in row:
            if isinstance(t, dict) and t.get('crop') == 'TOMATO':
                n_opp += 1
                pd = int(t['planted_day'])
                for a in range(8, 12):
                    if 18 <= pd + a <= 29:
                        rsup[pd + a] = rsup.get(pd + a, 0.0) + u * GC_P['v219x_opp_w']
    if n_opp == 0 and GC_P['v219x_copy_n'] > 0:
        for d in range(26, 30):
            rsup[d] = rsup.get(d, 0.0) + u * GC_P['v219x_copy_n']
    fert = float(obs['market']['prices']['FERTILIZER'])
    vals = {}
    P = int(obs['step']) // 24
    for n in GC_P['v219x_sizes']:
        inv = inv0
        rev = 0.0
        for d in range(P, 30):
            unl = min(8, d // 3) - n_shops
            inv -= 6.0 * (k_now + max(0, unl) * 0.25 * GC_P['future_shop_w']) + 1.0
            q_us = u * n if P + 8 <= d <= min(29, P + 11) else 0.0
            q_r = rsup.get(d, 0.0)
            tot = q_us + q_r
            if tot <= 0:
                continue
            if q_us > 0:
                sm = sum((_gc_price('TOMATO', inv + i) for i in range(int(round(tot)))))
                rev += sm * q_us / tot
            inv += tot
        extra_days = max(0, -(-n // 5) - 2) + 3 * max(0, -(-n // 8) - 1)
        vals[n] = rev - n * (50.0 + 2.0 * fert) - extra_days * GC_P['v219x_worker_cost']
    if GC_P['v219x_margins']:
        best = 10
        for n, m in sorted(((int(k), float(v)) for k, v in GC_P['v219x_margins'].items())):
            if n in vals and vals[n] - vals.get(10, 0.0) >= m:
                best = n
        return (best, vals)
    best = max(vals, key=lambda n: vals[n])
    if best != 10 and vals[best] - vals.get(10, 0.0) < GC_P['v219x_margin']:
        best = 10
    return (best, vals)
_DIV2 = {}

def _div2_check(obs):
    step = int(obs['step'])
    if step == 0:
        _DIV2.clear()
    if step == 2 and 'on' not in _DIV2:
        me = int(obs['player'])
        rm = float(obs['farms'][1 - me]['money'])
        lo, hi = GC_P['div2_band']
        _DIV2['on'] = not lo <= rm <= hi
_STRAW_SHOPS = ('BRUNCH_SPOT', 'ICE_CREAM_SHOP', 'SMOOTHIE_SHOP', 'FARMERS_MARKET')
_ES = {}

def _straw_to_tom(obs, action):
    day = int(obs['step']) // 24
    if day not in GC_P['s2t_days'] or not (_DIV2.get('on') or False):
        return action
    shops = list(_gc_get(obs['town'], 'unlocked_shops', []) or [])
    if sum((1 for s in shops if s in _STRAW_SHOPS)) > 0:
        return action
    me = int(obs['player'])
    same = 0
    n = 0
    for ra, rb in zip(obs['farms'][me]['tiles'], obs['farms'][1 - me]['tiles']):
        for ta, tb in zip(ra, rb):
            ka = ta if not isinstance(ta, dict) else ta.get('crop') or ta.get('animal') or ta.get('kind')
            kb = tb if not isinstance(tb, dict) else tb.get('crop') or tb.get('animal') or tb.get('kind')
            same += ka == kb
            n += 1
    sim = same / float(max(1, n))
    if sim > 0.97:
        return action
    crop = 'TOMATO'
    cmds = [action.get('farmer') or ['PASS']] + list(action.get('hands') or [])
    changed = 0
    new = []
    for c in cmds:
        if isinstance(c, list) and len(c) >= 2 and (c[0] == 'PLANT') and (c[1] == 'STRAWBERRY'):
            c = ['PLANT', crop]
            changed += 1
        new.append(c)
    market = []
    for o in action.get('market') or []:
        if isinstance(o, list) and len(o) >= 3 and (o[0] == 'BUY_SEED') and (o[1] == 'STRAWBERRY'):
            o = ['BUY_SEED', crop, o[2]]
            changed += 1
        market.append(o)
    if changed:
        action = dict(action)
        action['farmer'] = new[0]
        action['hands'] = new[1:]
        action['market'] = market
    return action

def _gc_chassis_floor(obs, act):
    if not isinstance(act, dict) or not act.get('market'):
        return act
    priv = obs['private']
    shed_tot = sum((int(v) for v in dict(priv['shed']).values()))
    carried = sum((int(v) for inv in priv.get('inventories', []) for v in dict(inv).values()))
    sold = sum((int(o[2]) for o in act['market'] if o and o[0] == 'SELL' and (len(o) > 2)))
    room = 100 - GC_P['chassis_floor_room'] - (shed_tot - sold + carried)
    if room <= 0:
        return act
    fr = 0.08
    out = []
    for o in act['market']:
        if o and o[0] == 'SELL' and (len(o) > 2) and (o[1] in GC_P['unit_floor_items']) and (room > 0):
            p, n = (o[1], int(o[2]))
            i0 = int(obs['market']['inventory'][p])
            k = 0
            while k < n and _gc_price(p, i0 + k) >= fr * _GC_MKT[p][0]:
                k += 1
            k = max(k, n - room)
            if k < n:
                room -= n - k
                if k <= 0:
                    continue
                o = ['SELL', p, k]
        out.append(o)
    act = dict(act)
    act['market'] = out
    return act

def _v219x_set_melons(obs, n):
    if not isinstance(globals().get('_V219_MELON'), list):
        return
    k, mv = (0, {})
    _V219_MELON[0] = k
    if mv:
        pass

def agent(observation, configuration=None):
    step = int(observation['step'])
    if step == 0:
        _GC.reset()
    _GC.me = int(observation['player'])
    if step == 0 and _GC_DIV_SAVED:
        GC_P.update(_GC_DIV_SAVED)
        _GC_DIV_SAVED.clear()
    if step == 0:
        _GC_RICH.clear()
    start = 576
    if GC_P.get('tom_debug') and step == 288 and (not _GC_RICH.get('tdbg')):
        _GC_RICH['tdbg'] = True
        pl = []
        for side in (_GC.me, 1 - _GC.me):
            for row in observation['farms'][side]['tiles']:
                for t in row:
                    if isinstance(t, dict) and t.get('crop') == 'TOMATO':
                        pl.append('%s%d/%d' % ('u' if side == _GC.me else 'r', int(t['planted_day']), int(t.get('yield_units', 0) or 0)))
    steps = (288,)
    due = [s for s in steps if s <= step and s not in _GC_RICH.get('done', ())]
    if due and (not _GC_RICH.get('rich')) and (not _GC_RICH.get('taken')):
        _GC_RICH.setdefault('done', set()).update(due)
        _GC_RICH['checked'] = True
        shops = list(_gc_get(observation['town'], 'unlocked_shops', []) or [])[:4]
        k = sum((1 for s in shops if s in ('BRUNCH_SPOT', 'ICE_CREAM_SHOP', 'SMOOTHIE_SHOP', 'FARMERS_MARKET')))
        _GC_RICH['rich'] = k >= 3
        if _GC_RICH['rich'] and True:
            try:
                ev = _GC.rich_eval(observation)
            except Exception as e:
                ev = -1000000000.0
            _mg = GC_P['se_straw_margin']
            _ad = globals().get('_AD_STATE')
            _GC_RICH['rich'] = ev > _mg
        if not _GC_RICH['rich'] and 0 > 0:
            kt = sum((1 for s in shops[:4] if s in ('PIZZA_SHOP', 'FARMERS_MARKET')))
            if kt >= 0:
                try:
                    evt = _GC.rich_eval_tom(observation)
                except Exception as e:
                    evt = -1000000000.0
                if evt > GC_P['rich_tom_margin']:
                    _GC_RICH['rich'] = True
                    _GC_RICH['tom'] = True
                    for kk, v in {}.items():
                        if kk not in _GC_DIV_SAVED:
                            _GC_DIV_SAVED[kk] = GC_P.get(kk)
                    GC_P.update({})
        if not _GC_RICH['rich'] and 0 > 0:
            kd = sum((6 for s in shops[:4] if s in ('PIZZA_SHOP', 'FARMERS_MARKET')))
            if kd >= 0:
                _GC_RICH['rich'] = True
                _GC_RICH['tomdem'] = True
                for kk, v in {}.items():
                    if kk not in _GC_DIV_SAVED:
                        _GC_DIV_SAVED[kk] = GC_P.get(kk)
                GC_P.update({})
        if not _GC_RICH['rich'] and 0 > 0:
            kc = sum((2 if s == 'PET_CAFE' else 1 if s == 'FARMERS_MARKET' else 0 for s in shops[:4]))
            if kc >= 0:
                _GC_RICH['rich'] = True
                _GC_RICH['car'] = True
                for kk, v in {}.items():
                    if kk not in _GC_DIV_SAVED:
                        _GC_DIV_SAVED[kk] = GC_P.get(kk)
                GC_P.update({})
        if not _GC_RICH['rich'] and 4000.0 is not None:
            try:
                me = int(observation['player'])
                _GC.me = me
                farm = observation['farms'][me]
                quads = list(farm['unlocked_quadrants'])
                n_empty = sum((1 for row in farm['tiles'] for t in row if t is None))
                se_open = 'SE' not in quads and 'NE' in quads and ('SW' in quads)
                allshops = list(_gc_get(observation['town'], 'unlocked_shops', []) or [])
                hk, hn, hv, _hs = _GC._herd_plan(observation, step // 24, allshops, max(0, n_empty - GC_P['herd_keep_free']), se_open, float(farm['money']) - GC_P['rich_hire_budget'], kinds=GC_P['herd_rich_over'].get('herd_kinds'))
            except Exception as e:
                hk, hn, hv = (None, 0, -1000000000.0)
            if hk and hv > 4000.0:
                _GC_RICH['rich'] = True
                _GC_RICH['herd'] = True
                for kk, v in GC_P['herd_rich_over'].items():
                    if kk not in _GC_DIV_SAVED:
                        _GC_DIV_SAVED[kk] = GC_P.get(kk)
                GC_P.update(GC_P['herd_rich_over'])
        if _GC_RICH['rich'] and GC_P['rich_over'] and (not _GC_RICH.get('tom')) and (not _GC_RICH.get('car')) and (not _GC_RICH.get('herd')) and (not _GC_RICH.get('tomdem')):
            for kk, v in GC_P['rich_over'].items():
                if kk not in _GC_DIV_SAVED:
                    _GC_DIV_SAVED[kk] = GC_P.get(kk)
            GC_P.update(GC_P['rich_over'])
    ad = globals().get('_AD_STATE')
    if isinstance(ad, dict) and ad.get('off'):
        start = 384
        adr = globals().get('_AD_REPORT') or {}
        if GC_P['div_over'] and (not _GC_RICH.get('div_applied')):
            _GC_RICH['div_applied'] = True
            for k, v in GC_P['div_over'].items():
                if k not in _GC_DIV_SAVED:
                    _GC_DIV_SAVED[k] = GC_P.get(k)
            GC_P.update(GC_P['div_over'])
    if _GC_RICH.get('rich'):
        if 'at' not in _GC_RICH:
            _GC_RICH['at'] = step
        start = min(start, _GC_RICH['at'])
    if step >= start:
        _GC_RICH['taken'] = True
    if step == 0 and None:
        for kk, vv in None.items():
            if kk in globals():
                globals()[kk] = vv
    if step == 0 and None:
        for kk, vv in None.items():
            _AD_CFG['thresh'][int(kk)] = float(vv)
    if step < start and isinstance(globals().get('_V219_N'), list):
        if step == 0:
            _V219_N[0] = 10
            if isinstance(globals().get('_V219_DAY'), list):
                _V219_DAY[0] = int(GC_P['v219x_day'])
            if isinstance(globals().get('_V219_THIRST'), list):
                _V219_THIRST[0] = bool(True)
            if isinstance(globals().get('_V219_MELON'), list):
                _V219_MELON[0] = 0
        elif step == 24 * 16 and isinstance(globals().get('_V219_DAY'), list) and (_V219_DAY[0] == 18):
            try:
                n, vals = _v219x_size(observation)
            except Exception as e:
                n, vals = (10, {})
            if n >= 20:
                _V219_DAY[0] = 16
                _V219_N[0] = n
                _v219x_set_melons(observation, n)
        elif step == 24 * (_V219_DAY[0] if isinstance(globals().get('_V219_DAY'), list) else 18):
            try:
                n, vals = _v219x_size(observation)
            except Exception as e:
                n, vals = (10, {})
            _V219_N[0] = n
            _v219x_set_melons(observation, n)
    if step < start:
        action = _GC_PARENT(observation, configuration)
        if GC_P['s2t_days']:
            try:
                _div2_check(observation)
                action = _straw_to_tom(observation, action)
            except Exception as e:
                pass
        if step >= 24 * GC_P['chassis_floor_from']:
            try:
                action = _gc_chassis_floor(observation, action)
            except Exception as e:
                pass
        return action
    try:
        return _GC.act(observation)
    except Exception as e:
        return {'farmer': ['PASS'], 'hands': [], 'market': []}
agent.telemetry = _GC_REPORT
globals().pop('kaggle_submission_agent', None)
kaggle_submission_agent = agent
