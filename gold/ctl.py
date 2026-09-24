
# =====================================================================================
# GOLD controller (offhand, 2026-09-24). From step GC_P['start'] (hour 0 of a day) this layer owns every
# unit and the market. Before that the chassis above plays unchanged.
# Each day at hour 0: value every tile job as the loss from deferring it a day, choose plantings/purchases,
# pick the number of hands by marginal value against the Fibonacci wage, build routes (angular sweep +
# nearest neighbour + 2-opt + cheapest insertion of overflow) that end with a delivery at the shed, then
# execute the routes turn by turn, skipping any action that would be a no-op. Everything in the shed
# beyond the feed/fertilizer reserve is sold every turn; the shed is kept clear for end-of-day drops.
# =====================================================================================
import math as _gc_math

GC_P = dict(
    start=288,            # takeover step (must be hour 0)
    max_hands=12,
    animals_must=True,
    wheat_fert_gain=25.0,  # fertilize one-time crops only when the extra yield beats selling the fertilizer by this much
    wheat_last_plant=25,  # wheat planted on day d is ripe on day d+4
    carrot_last_plant=27,
    carrot_first=14,
    carrot_min_demand=1,
    wheat_feed_bonus=4.0,  # own wheat saves buying feed at the ask
    straw_last_plant=12,
    straw_target=33,      # strawberry plants to hold while planting them is allowed
    feed_reserve=1.0,     # wheat kept per animal for the next morning
    fert_keep=6,
    fert_carrots=True,
    drip_on=True,
    drip={'STRAWBERRY': 6, 'MILK': 6, 'WOOL': 4, 'TOMATO': 6},
    drip_room=80,
    prem_drop=True,
    prem_drop_max=4,
    replant_done=False,
    feed_tiles_per_animal=0.75,
    feed_reserve_tiles=False,
    tomato_on=True,
    tomato_first=12,
    tomato_last=18,
    tomato_max_day=12,
    tomato_step=2,
    tomato_alt_day=35.0,
    tomato_labor=60.0,
    tomato_harvest_min=3,
    opp_tomato_w=1.0,
    future_shop_w=1.0,
    plant_must=True,
    plant_must_last=25,
    final_water=True,
    carrot_edge=1.0,
    hire_cost_w=1.0,
    dispatch=True,
    dispatch_min_value=8.0,
    fert_cost_w=1.0,
    ongoing_fert_gain=10.0,
    feed_all=False,
    max_sell0=3,
    fert_buy_margin=20.0,
    trim_hour=10,
    reserve_release_hour=18,
    care_min_price=12,
    harvest_min_price=3,
    plant_defer=0.3,      # value of planting today = this fraction of the crop's net value
    land_sw_day=11,
    drop_slack=0,         # turns kept free in each route for a shed stop
    always_drop=False,
    eod_room=88,
    prem_w=1.0,
    drop_after_animals=True,
    deliver_min=6,        # append a shed delivery when a route is expected to carry at least this many goods
)

_GC_CROPS = {
    "WHEAT": dict(seed=10, fy=2, my=4, iv=0, mx=6, on=False),
    "CARROT": dict(seed=20, fy=2, my=3, iv=0, mx=4, on=False),
    "TOMATO": dict(seed=50, fy=8, my=8, iv=1, mx=4, on=True),
    "STRAWBERRY": dict(seed=100, fy=10, my=10, iv=2, mx=4, on=True),
    "MELON": dict(seed=80, fy=10, my=12, iv=0, mx=6, on=False),
}
_GC_ANIM = {
    "GOOSE": dict(cost=300, st="COOP", fy=4, iv=1, held=4, prod="EGG"),
    "COW": dict(cost=400, st="PASTURE", fy=8, iv=2, held=6, prod="MILK"),
    "SHEEP": dict(cost=500, st="PASTURE", fy=6, iv=3, held=6, prod="WOOL"),
}
_GC_MKT = {
    "WHEAT": (25, 400, "sqrt", 0.80, "log", 0.20), "CARROT": (35, 450, "hinge", 1.00, "sqrt", 0.70),
    "TOMATO": (60, 200, "hinge", 0.40, "sqrt", 0.60), "STRAWBERRY": (120, 100, "sqrt", 0.70, "linear", 1.60),
    "MELON": (250, 300, "log", 0.20, "sq", 3.60), "EGG": (50, 332, "hinge", 0.40, "log", 0.20),
    "MILK": (160, 122, "sqrt", 0.60, "linear", 1.60), "WOOL": (200, 105, "log", 0.20, "sq", 3.20),
    "FERTILIZER": (100, 200, "linear", 0.40, "linear", 0.40),
}
_GC_SHOPS = {
    "BAKERY": ["EGG", "WHEAT"], "PIZZA_SHOP": ["MILK", "TOMATO", "WHEAT"],
    "BRUNCH_SPOT": ["EGG", "WHEAT", "STRAWBERRY"], "YARN_STORE": ["WOOL"],
    "ICE_CREAM_SHOP": ["STRAWBERRY", "MILK", "WHEAT"], "PET_CAFE": ["CARROT"],
    "SMOOTHIE_SHOP": ["STRAWBERRY", "MILK"], "FARMERS_MARKET": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"],
}
_GC_PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]
_GC_PREMIUM = ("MELON", "WOOL", "MILK", "STRAWBERRY", "TOMATO")
_GC_ACCESS = [(4, 4), (5, 4), (4, 5), (5, 5)]
_GC_ACCESS_SET = set(_GC_ACCESS)
_GC_REPORT = dict(gc_days=0, gc_errors=0, gc_hires=0, gc_noops=0, gc_unserved=0, gc_plan_ms=0, gc_room_sells=0)


def _gc_shape(f, x, T):
    x = max(0.0, x)
    if f == "linear": return x
    if f == "sq": return x * x
    if f == "sqrt": return _gc_math.sqrt(x)
    if f == "log": return _gc_math.log(1.0 + x)
    if f == "hinge":
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
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def _gc_quad(x, y):
    return ("N" if y < 5 else "S") + ("W" if x < 5 else "E")


def _gc_dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _gc_near_access(p):
    return min(_GC_ACCESS, key=lambda a: abs(a[0] - p[0]) + abs(a[1] - p[1]))


def _gc_get(d, k, default=None):
    if isinstance(d, dict):
        return d.get(k, default)
    return getattr(d, k, default)


class _GcVisit:
    __slots__ = ("pos", "acts", "wheat", "fert", "anim", "value", "must", "gain", "tag", "carry")

    def __init__(self, pos, acts, value=0.0, must=False, wheat=0, fert=0, anim=None, gain=None, tag="", carry=0):
        self.pos = pos; self.acts = acts; self.value = value; self.must = must
        self.wheat = wheat; self.fert = fert; self.anim = anim; self.gain = gain or {}; self.tag = tag
        self.carry = carry


class GoldCtl:
    def __init__(self):
        self.reset()

    def reset(self):
        self.me = None
        self.day_plan = None
        self.queues = {}
        self.routes = []
        self.spawns = []
        self.orders0 = []
        self.orders1 = []
        self.hires_planned = 0; self.hires_left = 0
        self.reserve = {}
        self.last_hires = 10
        self.n_animals = 0
        self.final = False

    # ------------------------------------------------------------------ valuation
    def _values(self, obs):
        inv = obs["market"]["inventory"]
        val = {}
        for p in _GC_PRODUCTS:
            val[p] = float(_gc_price(p, inv[p]))
        self.pnow = dict(val)
        return val

    # ------------------------------------------------------------------ planning
    def plan_day(self, obs):
        _GC_REPORT["gc_days"] += 1
        step = int(obs["step"]); day = step // 24
        me = self.me
        farm = obs["farms"][me]
        priv = obs["private"]
        shed = {k: int(v) for k, v in dict(priv["shed"]).items()}
        seeds = {k: int(v) for k, v in dict(priv["seeds"]).items()}
        money = float(farm["money"])
        shops = list(_gc_get(obs["town"], "unlocked_shops", []) or [])
        tiles = farm["tiles"]
        self.tiles_today = tiles
        final = day >= 29
        self.final = final
        val = self._values(obs)
        self.val = val
        quads = list(farm["unlocked_quadrants"])
        orders0 = []
        spend = 0.0
        hire_budget = sum(_gc_fib(k) for k in range(min(self.last_hires + 1, 13)))

        # ---- land (the chassis schedule: NE early, SW around day 11)
        new_quads = []
        if not final and day <= 16:
            if "NE" not in quads and money - hire_budget >= 1300:
                orders0.append(["BUY_LAND"]); spend += 1000; new_quads.append("NE")
            elif "NE" in quads and "SW" not in quads and day >= GC_P["land_sw_day"] and money - hire_budget >= 2400:
                orders0.append(["BUY_LAND"]); spend += 2000; new_quads.append("SW")
        owned = set(quads) | set(new_quads)

        # ---- scan
        plants = []; animals = []; empties = []; weeds = []; structs = []
        counts = {}
        for y in range(10):
            for x in range(10):
                t = tiles[y][x]
                if t == "LOCKED":
                    if _gc_quad(x, y) in owned:
                        empties.append((x, y))
                    continue
                if t is None:
                    empties.append((x, y)); continue
                k = t.get("kind")
                if k == "PLANT":
                    plants.append(((x, y), t)); counts[t["crop"]] = counts.get(t["crop"], 0) + 1
                elif k == "WEED": weeds.append((x, y))
                elif "animal" in t: animals.append(((x, y), t))
                elif k in ("COOP", "PASTURE"): structs.append(((x, y), k))
        self.n_animals = len(animals)

        visits = []
        replant = []
        for pos, t in plants:
            v = self._plant_visit(pos, t, day, val, final)
            if v is not None:
                visits.append(v)
                if (v.tag == "C" and v.acts and v.acts[-1][0] == "HARVEST") or v.tag == "R":
                    replant.append(v)
        for pos, t in animals:
            v = self._animal_visit(pos, t, day, val, final)
            if v is not None:
                visits.append(v)

        # ---- animals waiting in the shed
        free_struct = {"COOP": [p for p, k in structs if k == "COOP"], "PASTURE": [p for p, k in structs if k == "PASTURE"]}
        taken = set()
        for an in ("COW", "SHEEP", "GOOSE"):
            for _ in range(shed.get(an, 0)):
                st = _GC_ANIM[an]["st"]
                if free_struct[st]:
                    pos = free_struct[st].pop(0)
                    visits.append(_GcVisit(pos, [["PLACE", an]], value=300.0, must=True, anim=an, tag="L"))
                else:
                    cand = [p for p in empties if p not in taken]
                    if not cand:
                        break
                    pos = min(cand, key=lambda p: _gc_dist(p, (4.5, 4.5)))
                    taken.add(pos)
                    visits.append(_GcVisit(pos, [["BUILD_" + st], ["PLACE", an]], value=300.0, must=True, anim=an, tag="L"))

        # ---- planting
        need_seeds = {}
        if not final:
            free = [p for p in empties if p not in taken] + list(weeds)
            crop_for = self._choose_crops(obs, day, free, [v.pos for v in replant], shops, val, counts)
            for pos in free:
                crop = crop_for.get(pos)
                if not crop:
                    continue
                acts = ([["DIG"]] if pos in weeds else []) + [["PLANT", crop], ["WATER"]]
                visits.append(_GcVisit(pos, acts, value=GC_P["plant_defer"] * self._crop_value(crop, val), tag="P",
                                       must=GC_P["plant_must"] and day <= GC_P["plant_must_last"]))
                need_seeds[crop] = need_seeds.get(crop, 0) + 1
            for v in replant:
                crop = crop_for.get(v.pos)
                if not crop:
                    continue
                v.acts = v.acts + [["PLANT", crop], ["WATER"]]
                v.value += GC_P["plant_defer"] * self._crop_value(crop, val)
                need_seeds[crop] = need_seeds.get(crop, 0) + 1
            for crop, n in need_seeds.items():
                buy = n - seeds.get(crop, 0)
                if buy > 0:
                    cost = buy * _GC_CROPS[crop]["seed"]
                    avail = money - spend - hire_budget
                    if cost > avail:
                        buy = max(0, int(avail // _GC_CROPS[crop]["seed"]))
                        cost = buy * _GC_CROPS[crop]["seed"]
                    if buy > 0:
                        orders0.append(["BUY_SEED", crop, buy]); spend += cost

        # ---- inputs
        wheat_need = sum(v.wheat for v in visits)
        fert_need = sum(v.fert for v in visits)
        wheat_have = shed.get("WHEAT", 0)
        if wheat_need > wheat_have:
            short = wheat_need - wheat_have
            price = _gc_price("WHEAT", obs["market"]["inventory"]["WHEAT"] - short)
            orders0.append(["BUY_PRODUCT", "WHEAT", short]); spend += short * price
        fert_have = shed.get("FERTILIZER", 0)
        if fert_need > fert_have:
            # buy the shortfall when the fertilizations it enables are worth more than the fertilizer
            fv = sorted([v for v in visits if v.fert], key=lambda v: -v.gain.get("fert", 0.0))
            short = fert_need - fert_have
            fprice = _gc_price("FERTILIZER", obs["market"]["inventory"]["FERTILIZER"] - short)
            buy = sum(1 for v in fv[:short] if v.gain.get("fert", 0.0) > fprice + GC_P["fert_buy_margin"])
            if buy > 0 and money - spend - hire_budget > buy * fprice + 100:
                orders0.append(["BUY_PRODUCT", "FERTILIZER", buy]); spend += buy * fprice
                fert_have += buy
        if fert_need > fert_have:
            fv = sorted([v for v in visits if v.fert], key=lambda v: v.gain.get("fert", 0.0))
            for v in fv[:fert_need - fert_have]:
                v.acts = [a for a in v.acts if a[0] != "FERTILIZE"]; v.fert = 0
                v.value -= v.gain.get("fert", 0.0)
        visits = [v for v in visits if v.acts]

        # ---- hour-0 sales: free shed room before the input purchases land (a full shed rejects them)
        buys0 = [o for o in orders0 if o[0] == "BUY_PRODUCT"]
        res_w = int(GC_P["feed_reserve"] * len(animals)) + 2
        sell0 = []
        for p in sorted(_GC_PRODUCTS, key=lambda p: -(shed.get(p, 0) * val.get(p, 0))):
            n = int(shed.get(p, 0)) - (res_w if p == "WHEAT" else (GC_P["fert_keep"] if p == "FERTILIZER" else 0))
            if n > 0:
                sell0.append(["SELL", p, n])
        need_room = sum(int(v) for v in shed.values()) + sum(int(o[2]) for o in buys0) - 95
        sell0 = sell0[:max(GC_P["max_sell0"], 1 if need_room > 0 else 0)]
        self.sell0 = sell0
        self.n0_hires = 10 - len(buys0) - len(sell0)
        import time as _t
        t0 = _t.perf_counter()
        routes, hires, spawns = self._route_and_hire(visits, money - spend, final, day)
        _GC_REPORT["gc_plan_ms"] = max(_GC_REPORT["gc_plan_ms"], int(1000 * (_t.perf_counter() - t0)))
        self.hires_planned = hires
        self.last_hires = hires
        _GC_REPORT["gc_hires"] += hires
        self.orders0 = list(self.sell0) + [o for o in orders0 if o[0] == "BUY_PRODUCT"]
        self.orders1 = [o for o in orders0 if o[0] != "BUY_PRODUCT"]
        self.routes = routes
        self.spawns = spawns
        self.day = day
        # shed stops: only as many as needed so the end-of-day drop fits in the shed
        self.drop_at = {}
        room = GC_P["eod_room"]
        carried = [sum(v.carry for v in r) for r in routes]
        total = sum(carried)
        done = set()
        guard = 0
        while (total > room or GC_P["always_drop"]) and guard < 40:
            guard += 1
            best = None
            for u, r in enumerate(routes):
                if u in done or not r or carried[u] < GC_P["deliver_min"]:
                    continue
                cap = 23 if u == 0 else (23 if u <= self.n0_hires else 22)
                k, extra, got = self._drop_best(spawns[u], r, cap + 99)
                if k is None:
                    continue
                sc = got / (extra + 0.5)
                if best is None or sc > best[0]:
                    best = (sc, u, k, extra, got)
            if best is None:
                break
            _, u, k, extra, got = best
            cap = 23 if u == 0 else (23 if u <= self.n0_hires else 22)
            r = routes[u]
            # make room by dropping the lowest-value optional visits after the stop
            while self._rcost(spawns[u], r) + extra > cap:
                opt = [i for i, v in enumerate(r) if not v.must and i > k]
                if not opt:
                    break
                j = min(opt, key=lambda i: r[i].value / (len(r[i].acts) + 1.0))
                r.pop(j)
            if self._rcost(spawns[u], r) + extra <= cap:
                self.drop_at[u] = k; total -= got
            done.add(u)
        if GC_P["prem_drop"] and not final:
            for u, r in enumerate(routes):
                if u in self.drop_at or not r:
                    continue
                prem_idx = [k for k, v in enumerate(r) if v.carry > 0 and self._is_premium_visit(v)]
                if not prem_idx:
                    continue
                k = prem_idx[-1]
                v = r[k]
                a = _gc_near_access(v.pos)
                back = abs(v.pos[0] - a[0]) + abs(v.pos[1] - a[1])
                if k + 1 < len(r):
                    nx = r[k + 1].pos
                    extra = back + 1 + abs(a[0] - nx[0]) + abs(a[1] - nx[1]) - (abs(v.pos[0] - nx[0]) + abs(v.pos[1] - nx[1]))
                else:
                    extra = back + 1
                cap = 23 if u == 0 else (23 if u <= self.n0_hires else 22)
                if extra <= GC_P["prem_drop_max"] and self._rcost(spawns[u], r) + extra <= cap:
                    self.drop_at[u] = k
                    _GC_REPORT["gc_prem_drops"] = _GC_REPORT.get("gc_prem_drops", 0) + 1
        if final:
            for u, r in enumerate(routes):
                if r:
                    self.drop_at[u] = len(r) - 1
        # tomorrow's fertilizations: ongoing crops on a production eve without cover, one-time crops entering the window
        fert_tom = 0
        for pos, t in plants:
            cd = _GC_CROPS[t["crop"]]; age1 = day + 1 - int(t["planted_day"])
            fu = int(t.get("fertilized_until_day", -1))
            if cd["on"]:
                k1 = age1 + 1 - cd["fy"]
                if k1 >= 0 and k1 % cd["iv"] == 0 and (k1 // cd["iv"] + 1) <= cd["mx"] and fu < day + 1:
                    fert_tom += 1
            elif t["crop"] in ("WHEAT", "CARROT") and age1 == (cd["my"] + 1) // 2 and fu < day + 1:
                fert_tom += 1
        self.fert_tomorrow = fert_tom
        self.reserve = {"WHEAT": int(GC_P["feed_reserve"] * len(animals)) + 2,
                        "FERTILIZER": max(GC_P["fert_keep"], fert_tom + 2)}

    # ------------------------------------------------------------------ jobs
    def _plant_visit(self, pos, t, day, val, final):
        crop = t["crop"]; cd = _GC_CROPS[crop]
        age = day - int(t["planted_day"])
        cu = int(t["consecutive_unwatered"])
        yu = int(t["yield_units"])
        fu = int(t.get("fertilized_until_day", -1))
        acts = []; value = 0.0; must = False; fert = 0; gain = {}; carry = 0
        pv = val[crop]
        if not cd["on"]:
            ws = (cd["my"] + 1) // 2
            ready = age >= cd["fy"]
            in_window = ws <= age <= cd["my"]
            if final:
                if ready and yu > 0:
                    acts = []
                    g = 0
                    if GC_P["final_water"] and in_window and yu < cd["mx"] and not t.get("watered_today"):
                        g = min(2 if fu >= day else 1, cd["mx"] - yu)
                        acts.append(["WATER"])
                    acts.append(["HARVEST"])
                    return _GcVisit(pos, acts, value=(yu + g) * pv, must=True, tag="H", carry=yu + g)
                return None
            yu2 = yu
            if in_window and yu < cd["mx"]:
                fert_active = fu >= day
                if (not fert_active) and age == ws and not (crop == "CARROT" and not GC_P["fert_carrots"]):
                    rem_days = cd["my"] - age + 1
                    extra = min(cd["mx"] - yu, 2 * rem_days) - min(cd["mx"] - yu, rem_days)
                    fert_gain = extra * pv - self.pnow.get("FERTILIZER", 50)
                    if fert_gain > GC_P["wheat_fert_gain"]:
                        acts.append(["FERTILIZE"]); fert = 1; gain["fert"] = fert_gain; value += fert_gain
                        fert_active = True
                g = min(2 if fert_active else 1, cd["mx"] - yu)
                acts.append(["WATER"]); value += g * pv; yu2 = yu + g
                if cu >= 1:
                    must = True; value += (yu + g) * pv
            elif cu >= 1 and not (ready and yu > 0 and age >= cd["my"]):
                acts.append(["WATER"]); value += max(1, yu) * pv + 30; must = True
            harvest_now = ready and yu2 > 0 and (age >= cd["my"] or yu2 >= cd["mx"])
            if crop == "MELON":
                harvest_now = age >= cd["fy"] and yu2 > 0 and (yu2 >= cd["mx"] or age >= cd["my"])
            if day >= 28 and ready and yu2 > 0:
                harvest_now = True
            if harvest_now:
                acts.append(["HARVEST"]); value += yu2 * pv; must = True; carry = yu2
            if not acts:
                return None
            return _GcVisit(pos, acts, value=value, must=must, fert=fert, gain=gain, tag="C", carry=carry)
        # ongoing crops
        k_next = age + 1 - cd["fy"]
        eve = k_next >= 0 and k_next % cd["iv"] == 0 and (k_next // cd["iv"] + 1) <= cd["mx"]
        done = int(t.get("max_lifespan_step", -1)) >= 0
        if final:
            if yu > 0:
                return _GcVisit(pos, [["HARVEST"]], value=yu * pv, must=True, tag="H", carry=yu)
            return None
        fert_active = fu >= day
        add = (2 if fert_active else 1) if eve else 0
        if yu > 0:
            over = max(0, yu + add - cd["mx"])
            thr = GC_P["tomato_harvest_min"] if crop == "TOMATO" else 2
            if over > 0 or done or day >= 28 or yu >= thr:
                acts.append(["HARVEST"]); value += over * pv + (yu * pv * 0.15) + (yu * pv if done else 0); carry = yu
        if eve:
            if not fert_active:
                covered = sum(1 for dd in range(3) if (k_next + dd) >= 0 and (k_next + dd) % cd["iv"] == 0 and ((k_next + dd) // cd["iv"] + 1) <= cd["mx"])
                fert_gain = covered * pv - self.pnow.get("FERTILIZER", 50) * GC_P["fert_cost_w"]
                if fert_gain > GC_P["ongoing_fert_gain"]:
                    acts.append(["FERTILIZE"]); fert = 1; gain["fert"] = fert_gain; value += fert_gain
                    fert_active = True
            if fert_active:
                acts.append(["WATER"]); value += pv
                if cu >= 1:
                    must = True; value += 4 * pv
            elif cu >= 1:
                acts.append(["WATER"]); value += 4 * pv; must = True
        elif cu >= 1 and not done:
            acts.append(["WATER"]); value += 4 * pv; must = True
        if done and day <= GC_P["carrot_last_plant"] and GC_P["replant_done"]:
            # no further production: take what is left, clear the plant and let the tile be replanted now
            acts = [a for a in acts if a[0] == "HARVEST"] + [["DIG"]]
            return _GcVisit(pos, acts, value=value + 40.0, must=GC_P["plant_must"], tag="R", carry=carry)
        if done and yu == 0 and not acts:
            if day <= 26:
                return _GcVisit(pos, [["DIG"]], value=40.0, tag="D", must=GC_P["plant_must"])
            return None
        if not acts:
            return None
        return _GcVisit(pos, acts, value=value, must=must, fert=fert, gain=gain, tag="O", carry=carry)

    def _animal_visit(self, pos, t, day, val, final):
        a = _GC_ANIM[t["animal"]]
        yu = int(t["yield_units"]); pv = val[a["prod"]]
        pend = int(t.get("pending_care_bonus", 0) or 0)
        acts = []; value = 0.0; must = False; wheat = 0; carry = 0
        if final:
            acts = []
            if yu > 0 and pv >= 2:
                acts.append(["HARVEST"])
            if t.get("fertilizer_available") and self.pnow.get("FERTILIZER", 0) >= 3:
                acts.append(["COLLECT_FERTILIZER"])
            if acts:
                return _GcVisit(pos, acts, value=yu * pv + self.pnow.get("FERTILIZER", 0), must=True, tag="H", carry=yu + 1)
            return None
        placed = int(t.get("placed_day", 0))

        def prod_at(e):
            k = e + 1 - placed - a["fy"]
            return k >= 0 and k % a["iv"] == 0
        prod_tonight = prod_at(day)
        e = day + 1
        while e <= 28 and not prod_at(e):
            e += 1
        # bonus banked before the first production is capped by the held limit
        care_useful = e <= 28 and pend + 2 <= a["held"]
        care_worth = care_useful and pv >= GC_P["care_min_price"]
        unfed = int(t["consecutive_unfed"]) >= 1
        wheat_px = self.pnow.get("WHEAT", 40)
        bonus_tonight = prod_tonight and pv * (1 + pend) > wheat_px
        feed = day <= 28 and (unfed or care_worth or bonus_tonight or GC_P["feed_all"])
        if feed:
            acts.append(["FEED"]); wheat = 1
            if unfed:
                value += 500.0; must = True
            else:
                value += (pv * (1 + pend) if prod_tonight else 0.0) + 5.0
        if care_worth and feed:
            acts.append(["CARE"]); value += pv * 0.9
        if yu > 0:
            nxt = (1 + pend) if prod_tonight else 0
            over = max(0, yu + nxt - a["held"])
            if (over > 0 or yu >= 3 or day >= 27) and (pv >= GC_P["harvest_min_price"] or day >= 28):
                acts.append(["HARVEST"]); value += over * pv + yu * pv * 0.1; carry += yu
        if t.get("fertilizer_available"):
            acts.append(["COLLECT_FERTILIZER"]); value += max(3.0, self.pnow.get("FERTILIZER", 30) * 0.8); carry += 1
        if not acts:
            return None
        # animals are the densest value on the farm: visit every fed one every day
        must = must or (GC_P["animals_must"] and wheat > 0)
        return _GcVisit(pos, acts, value=value, must=must, wheat=wheat, tag="A", carry=carry)

    def _crop_value(self, crop, val):
        cd = _GC_CROPS[crop]
        units = {"WHEAT": 5.0, "CARROT": 3.5, "TOMATO": 7.0, "STRAWBERRY": 7.0, "MELON": 6.0}[crop]
        return units * val[crop] - cd["seed"]

    def _tomato_value(self, obs, day, n, shops):
        """Forecast revenue of n tomato plots planted today (4 units at age 9 and 11 each), selling on arrival,
        against town demand (current + expected new shops) and the opponent's visible tomato plants."""
        inv = float(obs["market"]["inventory"]["TOMATO"])
        k_now = sum(1 for s in shops if s in ("PIZZA_SHOP", "FARMERS_MARKET"))
        n_shops = len(shops)
        opp = obs["farms"][1 - self.me]
        opp_sup = {}
        for row in opp["tiles"]:
            for t in row:
                if isinstance(t, dict) and t.get("crop") == "TOMATO":
                    pd = int(t["planted_day"])
                    for age, u in ((9, 4), (11, 4)):
                        d = pd + age
                        if d >= day:
                            opp_sup[d] = opp_sup.get(d, 0) + u * GC_P["opp_tomato_w"]
        mine = {}
        for row in obs["farms"][self.me]["tiles"]:
            for t in row:
                if isinstance(t, dict) and t.get("crop") == "TOMATO":
                    pd = int(t["planted_day"])
                    for age, u in ((9, 4), (11, 4)):
                        d = pd + age
                        if d >= day:
                            mine[d] = mine.get(d, 0) + u
        rev = 0.0
        for d in range(day, 30):
            # expected tomato shops by day d (a shop unlocks at the start of days 3,6,..., 8 at most)
            unl = min(8, d // 3) - n_shops
            k = k_now + max(0, unl) * 0.25 * GC_P["future_shop_w"]
            inv -= 6.0 * k + 1.0
            inv += opp_sup.get(d, 0) + mine.get(d, 0)
            for age in (9, 11):
                if d == day + age and d <= 29:
                    q = 4 * n
                    p0 = _gc_price("TOMATO", inv); p1 = _gc_price("TOMATO", inv + q)
                    rev += q * 0.5 * (p0 + p1)
                    inv += q
        return rev

    def _tomato_count(self, obs, day, n_free, shops, val):
        if not GC_P["tomato_on"] or day < GC_P["tomato_first"] or day > GC_P["tomato_last"] or n_free <= 0:
            return 0
        fert = self.pnow.get("FERTILIZER", 50)
        alt = GC_P["tomato_alt_day"] * 12.0      # what the tile earns as wheat/carrot over the same 12 days
        cost = 50 + 2 * fert + GC_P["tomato_labor"]
        best_n, best_v = 0, 0.0
        base = self._tomato_value(obs, day, 0, shops)
        for n in range(GC_P["tomato_step"], min(n_free, GC_P["tomato_max_day"]) + 1, GC_P["tomato_step"]):
            v = self._tomato_value(obs, day, n, shops) - base - n * (cost + alt)
            if v > best_v:
                best_n, best_v = n, v
        return best_n

    def _choose_crops(self, obs, day, free, replant, shops, val, counts):
        out = {}
        straw_room = 0
        if day <= GC_P["straw_last_plant"]:
            straw_room = max(0, GC_P["straw_target"] - counts.get("STRAWBERRY", 0))
        carrot_demand = sum(2 if s == "PET_CAFE" else (1 if s == "FARMERS_MARKET" else 0) for s in shops)
        fert = self.pnow.get("FERTILIZER", 50)
        # value per tile-day at today's prices (fertilized yields, seed and fertilizer paid)
        v_wheat = (6 * val["WHEAT"] - 10 - fert) / 4.0 + GC_P["wheat_feed_bonus"]
        v_carrot = (4 * val["CARROT"] - 20 - fert) / 3.0
        filler = "WHEAT"
        if carrot_demand >= GC_P["carrot_min_demand"] and v_carrot > GC_P["carrot_edge"] * v_wheat and day >= GC_P["carrot_first"]:
            filler = "CARROT"

        def fill(d):
            if filler == "CARROT" and d <= GC_P["carrot_last_plant"]:
                return "CARROT"
            if d <= GC_P["wheat_last_plant"]:
                return "WHEAT"
            if d <= GC_P["carrot_last_plant"]:
                return "CARROT"
            return None
        # wheat plots needed to feed the herd (a fertilized plot yields ~6 per 4-day cycle)
        wheat_now = counts.get("WHEAT", 0) - len(replant)          # plots that stay wheat today
        need_w = int(GC_P["feed_tiles_per_animal"] * self.n_animals + 0.999) if (day <= GC_P["wheat_last_plant"] and GC_P["feed_reserve_tiles"]) else 0
        slots = sorted(free, key=lambda p: _gc_dist(p, (4.5, 4.5))) + sorted(replant, key=lambda p: _gc_dist(p, (4.5, 4.5)))
        n_slots = len(slots)
        feed_first = max(0, need_w - wheat_now)
        spare = max(0, n_slots - feed_first - (straw_room if day <= GC_P["straw_last_plant"] else 0))
        n_tom = min(self._tomato_count(obs, day, spare, shops, val), spare)
        self.n_tomato_today = n_tom
        placed_t = 0
        # feed wheat goes on the farthest slots (low-maintenance), tomatoes and strawberries near the shed
        far = sorted(slots, key=lambda p: -_gc_dist(p, (4.5, 4.5)))
        feed_tiles = set(far[:feed_first])
        for pos in slots:
            if pos in feed_tiles:
                out[pos] = "WHEAT"; continue
            if straw_room > 0 and pos in free:
                out[pos] = "STRAWBERRY"; straw_room -= 1
            elif placed_t < n_tom:
                out[pos] = "TOMATO"; placed_t += 1
            else:
                c = fill(day)
                if c:
                    out[pos] = c
        n_tom = n_tom - placed_t
        if self.n_tomato_today:
            _GC_REPORT["gc_tomato_planned"] = _GC_REPORT.get("gc_tomato_planned", 0) + self.n_tomato_today - n_tom
        return out

    # ------------------------------------------------------------------ routing
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

    @staticmethod
    def _cost(start, visits):
        t = 0
        if any(v.wheat for v in visits): t += 1
        if any(v.fert for v in visits): t += 1
        t += len({v.anim for v in visits if v.anim})
        pos = start
        carry = 0
        for v in visits:
            t += abs(pos[0] - v.pos[0]) + abs(pos[1] - v.pos[1]) + len(v.acts)
            pos = v.pos; carry += v.carry
        if carry >= GC_P["deliver_min"]:
            a = _gc_near_access(pos)
            t += abs(pos[0] - a[0]) + abs(pos[1] - a[1]) + 1
        return t

    def _vrp(self, visits, h):
        def k_far(v):
            return (0 if v.must else 1, -(abs(v.pos[0] - 4.5) + abs(v.pos[1] - 4.5)) if v.must else -v.value / (len(v.acts) + 2.0))

        def k_ang(v):
            return (0 if v.must else 1, _gc_math.atan2(v.pos[1] - 4.5, v.pos[0] - 4.5) if v.must else -v.value / (len(v.acts) + 2.0))

        def k_val(v):
            return (0 if v.must else 1, -v.value / (len(v.acts) + 2.0))
        best = None
        for key in (k_far, k_ang, k_val):
            routes, spawns, unserved = self._vrp1(visits, h, key)
            nm = sum(1 for v in unserved if v.must)
            uv = sum(v.value for v in unserved)
            tc = sum(self._rcost(spawns[u], r) for u, r in enumerate(routes))
            sc = (nm, uv, tc)
            if best is None or sc < best[0]:
                best = (sc, routes, spawns, unserved)
        return best[1], best[2], best[3]

    def _order_anim_first(self, start, vs, cap):
        """Animals (premium goods) first so their products reach the shed early; keep the plain order if that costs more than 2 turns."""
        plain = self._order(start, vs)
        an = [v for v in vs if v.tag == "A"]
        if not an or len(an) == len(vs):
            return plain
        a_ord = self._order(start, an)
        rest = self._order(a_ord[-1].pos, [v for v in vs if v.tag != "A"])
        mixed = a_ord + rest
        if self._rcost(start, mixed) <= min(cap, self._rcost(start, plain) + 2):
            return mixed
        return plain

    @staticmethod
    def _order(start, vs):
        if len(vs) <= 1:
            return list(vs)
        rem = list(vs); out = []; pos = start
        while rem:
            j = min(range(len(rem)), key=lambda i: abs(pos[0] - rem[i].pos[0]) + abs(pos[1] - rem[i].pos[1]))
            v = rem.pop(j); out.append(v); pos = v.pos
        n = len(out)
        # 2-opt on a path that returns to the shed area (so routes end near a delivery tile)
        end = (4.5, 4.5)
        improved = True; it = 0
        while improved and it < 8:
            improved = False; it += 1
            for i in range(0, n - 1):
                a = start if i == 0 else out[i - 1].pos
                b = out[i].pos
                for j in range(i + 1, n):
                    c = out[j].pos
                    d = out[j + 1].pos if j + 1 < n else end
                    old = abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(c[0] - d[0]) + abs(c[1] - d[1])
                    new = abs(a[0] - c[0]) + abs(a[1] - c[1]) + abs(b[0] - d[0]) + abs(b[1] - d[1])
                    if new < old - 1e-9:
                        out[i:j + 1] = out[i:j + 1][::-1]; improved = True
                        b = out[i].pos
        return out

    @staticmethod
    def _rcost(start, r):
        """Turns for one route: pickups at the spawn tile, then moves + actions (no return trip)."""
        t = 0
        if any(v.wheat for v in r): t += 1
        if any(v.fert for v in r): t += 1
        t += len({v.anim for v in r if v.anim})
        pos = start
        for v in r:
            t += abs(pos[0] - v.pos[0]) + abs(pos[1] - v.pos[1]) + len(v.acts)
            pos = v.pos
        return t

    def _vrp1(self, visits, h, order_key):
        n_units = 1 + h
        spawns = [(4, 4)] + self._spawns(h, (4, 4))
        s = GC_P["drop_slack"] if not self.final else 5
        n0 = getattr(self, "n0_hires", 9)
        caps = [23 - s] + [(23 if i < n0 else 22) - s for i in range(h)]
        routes = [[] for _ in range(n_units)]
        costs = [0] * n_units
        flags = [[False, False, set()] for _ in range(n_units)]   # has wheat, has fert, animal kinds

        unserved = []
        for v in sorted(visits, key=order_key):
            best = None
            for u in range(n_units):
                r = routes[u]; fl = flags[u]
                extra = (1 if v.wheat and not fl[0] else 0) + (1 if v.fert and not fl[1] else 0) + (1 if v.anim and v.anim not in fl[2] else 0)
                base = costs[u] + extra + len(v.acts)
                if base > caps[u]:
                    continue
                prev = spawns[u]
                for i in range(len(r) + 1):
                    nxt = r[i].pos if i < len(r) else None
                    dd = abs(prev[0] - v.pos[0]) + abs(prev[1] - v.pos[1])
                    if nxt is not None:
                        dd += abs(v.pos[0] - nxt[0]) + abs(v.pos[1] - nxt[1]) - abs(prev[0] - nxt[0]) - abs(prev[1] - nxt[1])
                    c = base + dd
                    if c <= caps[u] and (best is None or c - costs[u] < best[0]):
                        best = (c - costs[u], u, i, c)
                    if nxt is not None:
                        prev = nxt
            if best is None:
                unserved.append(v); continue
            _, u, i, c = best
            routes[u].insert(i, v); costs[u] = c
            fl = flags[u]
            if v.wheat: fl[0] = True
            if v.fert: fl[1] = True
            if v.anim: fl[2].add(v.anim)
        # local search: 2-opt inside each route (animal cluster first), then try to place unserved visits again
        for u in range(n_units):
            if len(routes[u]) > 2:
                routes[u] = self._order_anim_first(spawns[u], routes[u], caps[u])
                costs[u] = self._rcost(spawns[u], routes[u])
        if unserved:
            left = []
            for v in unserved:
                best = None
                for u in range(n_units):
                    r = routes[u]
                    for i in range(len(r) + 1):
                        c = self._rcost(spawns[u], r[:i] + [v] + r[i:])
                        if c <= caps[u] and (best is None or c < best[0]):
                            best = (c, u, i)
                if best is None:
                    left.append(v)
                else:
                    c, u, i = best
                    routes[u].insert(i, v); costs[u] = c
            unserved = left
        return routes, spawns, unserved

    @staticmethod
    def _order(start, vs):
        """Nearest neighbour then 2-opt for an open path starting at `start`."""
        if len(vs) <= 1:
            return list(vs)
        rem = list(vs); out = []; pos = start
        while rem:
            j = min(range(len(rem)), key=lambda i: abs(pos[0] - rem[i].pos[0]) + abs(pos[1] - rem[i].pos[1]))
            v = rem.pop(j); out.append(v); pos = v.pos
        n = len(out)
        P = [v.pos for v in out]
        improved = True; it = 0
        while improved and it < 8:
            improved = False; it += 1
            for i in range(0, n - 1):
                a = start if i == 0 else P[i - 1]
                for j in range(i + 1, n):
                    b = P[i]; c = P[j]
                    old = abs(a[0] - b[0]) + abs(a[1] - b[1])
                    new = abs(a[0] - c[0]) + abs(a[1] - c[1])
                    if j + 1 < n:
                        d = P[j + 1]
                        old += abs(c[0] - d[0]) + abs(c[1] - d[1])
                        new += abs(b[0] - d[0]) + abs(b[1] - d[1])
                    if new < old:
                        out[i:j + 1] = out[i:j + 1][::-1]; P[i:j + 1] = P[i:j + 1][::-1]; improved = True
        return out

    def _route_and_hire(self, visits, cash, final, day):
        best = None
        lo = 0 if (day == GC_P["start"] // 24 or final) else max(0, self.last_hires - 3)
        hi = GC_P["max_hands"]
        for h in range(lo, hi + 1):
            cost = sum(_gc_fib(q) for q in range(h))
            if cost > cash - 20:
                break
            routes, spawns, unserved = self._vrp(visits, h)
            pen = sum((v.value + (1e5 if v.must else 0.0)) for v in unserved)
            score = -pen - GC_P["hire_cost_w"] * cost
            if best is None or score > best[0]:
                best = (score, h, routes, spawns, sum(v.value for v in unserved))
                self._last_unserved = (sum(1 for v in unserved if v.must), len(unserved), sorted({v.tag for v in unserved}))
            if not unserved and best[1] < h:
                break
        _GC_REPORT["gc_unserved"] += int(best[4])
        return best[2], best[1], best[3]

    # ------------------------------------------------------------------ execution
    def _compile(self, routes, spawns):
        qs = []
        for u, r in enumerate(routes):
            q = []
            if u == 0:
                q.append((spawns[0], ["PASS"], None))   # keep the farmer on (4,4) at hour 0 so hires spawn where planned
            wheat = sum(v.wheat for v in r); fert = sum(v.fert for v in r)
            if wheat:
                q.append((spawns[u], ["PICKUP", "WHEAT", wheat], None))
            if fert:
                q.append((spawns[u], ["PICKUP", "FERTILIZER", fert], None))
            for an in ("COW", "SHEEP", "GOOSE"):
                n = sum(1 for v in r if v.anim == an)
                if n:
                    q.append((spawns[u], ["PICKUP", an, n], None))
            drop_at = self.drop_at.get(u)
            for k, v in enumerate(r):
                for a in v.acts:
                    q.append((v.pos, list(a), v))
                if drop_at is not None and k == drop_at:
                    q.append((_gc_near_access(v.pos), ["DROP"], None))
            qs.append(q)
        return qs

    def _is_premium_visit(self, v):
        t = self.tiles_today[v.pos[1]][v.pos[0]] if getattr(self, "tiles_today", None) else None
        if not isinstance(t, dict):
            return False
        if t.get("kind") == "PLANT":
            return t.get("crop") in ("STRAWBERRY", "TOMATO", "MELON") and any(a[0] == "HARVEST" for a in v.acts)
        if t.get("animal") in ("COW", "SHEEP"):
            return any(a[0] == "HARVEST" for a in v.acts)
        return False

    def _drop_best(self, spawn, r, cap):
        """(index, extra turns, goods delivered) of the best single shed stop in a route."""
        base = self._rcost(spawn, r)
        best = None; carried = 0
        for k, v in enumerate(r):
            carried += v.carry
            if carried < GC_P["deliver_min"]:
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
            prem = sum(x.carry for x in r[:k + 1] if x.tag == "A")
            sc = (carried + GC_P["prem_w"] * prem) / (extra + 0.5)
            if best is None or sc > best[0]:
                best = (sc, k, extra, carried)
        if best is None:
            return None, 0, 0
        return best[1], best[2], best[3]

    def _drop_point(self, spawn, r, cap):
        """Index after which a shed stop is inserted (None = rely on the end-of-day drop).
        Routes with animal goods stop right after their last animal (premium goods sell early);
        otherwise maximise goods delivered per extra turn, within the unit's turn budget."""
        if not r:
            return None
        base = self._rcost(spawn, r)
        last_a = max((k for k, v in enumerate(r) if v.tag == "A" and v.carry > 0), default=None)
        if last_a is not None and GC_P["drop_after_animals"]:
            v = r[last_a]
            a = _gc_near_access(v.pos)
            back = abs(v.pos[0] - a[0]) + abs(v.pos[1] - a[1])
            if last_a + 1 < len(r):
                nx = r[last_a + 1].pos
                extra = back + 1 + abs(a[0] - nx[0]) + abs(a[1] - nx[1]) - (abs(v.pos[0] - nx[0]) + abs(v.pos[1] - nx[1]))
            else:
                extra = back + 1
            if base + extra <= cap:
                return last_a
        best = None; carried = 0
        for k, v in enumerate(r):
            carried += v.carry
            if carried < GC_P["deliver_min"]:
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
            prem = sum(v.carry for v in r[:k + 1] if v.tag == "A")
            score = (carried + 2.0 * prem) / (extra + 0.5) - 0.15 * k
            if best is None or score > best[0]:
                best = (score, k)
        return None if best is None else best[1]

    def _useful(self, act, tile, inv, seeds, planting, shed, room):
        op = act[0]
        if op == "PASS":
            return True
        if op == "PICKUP":
            return shed.get(act[1], 0) > 0
        if op == "DROP":
            n = sum(int(x) for x in inv.values())
            return n > 0 and room[0] >= n
        if op == "PLACE":
            return inv.get(act[1], 0) > 0 and isinstance(tile, dict) and tile.get("kind") == _GC_ANIM[act[1]]["st"] and "animal" not in tile
        if tile == "LOCKED":
            return False
        if op == "PLANT":
            return tile is None and seeds.get(act[1], 0) - planting.get(act[1], 0) > 0
        if op == "DIG":
            return tile is not None and not (isinstance(tile, dict) and "animal" in tile)
        if op in ("BUILD_COOP", "BUILD_PASTURE"):
            return tile is None
        if not isinstance(tile, dict):
            return False
        k = tile.get("kind")
        if op == "WATER":
            return k == "PLANT" and not tile.get("watered_today")
        if op == "HARVEST":
            return int(tile.get("yield_units", 0) or 0) > 0 and (k == "PLANT" or "animal" in tile)
        if op == "FERTILIZE":
            return k == "PLANT" and inv.get("FERTILIZER", 0) > 0
        if op == "FEED":
            return "animal" in tile and not tile.get("fed_today") and inv.get("WHEAT", 0) > 0
        if op == "CARE":
            return "animal" in tile and not tile.get("cared_today")
        if op == "COLLECT_FERTILIZER":
            return "animal" in tile and bool(tile.get("fertilizer_available"))
        return True

    def _trim_queue(self, q, pos, turns_left):
        """Drop optional visits (latest, lowest value first) until the remaining queue fits the turns left."""
        def cost(qq):
            t = 0; p = pos
            for tgt, a, v in qq:
                t += abs(p[0] - tgt[0]) + abs(p[1] - tgt[1]) + 1
                p = tgt
            return t
        guard = 0
        while q and cost(q) > turns_left and guard < 30:
            guard += 1
            opt = {id(v): v for _, _, v in q if v is not None and not v.must}
            if not opt:
                break
            worst = min(opt.values(), key=lambda v: v.value / (len(v.acts) + 1.0))
            q[:] = [it for it in q if it[2] is not worst]
            _GC_REPORT["gc_trimmed"] = _GC_REPORT.get("gc_trimmed", 0) + 1

    def _dispatch(self, u, pos, inv, turns_left, tiles, sim, seeds, shed, claimed, day, hour):
        """Idle unit: queue the best remaining unclaimed job it can finish today (value per turn)."""
        if turns_left <= 1:
            return None
        cache = getattr(self, "_dcache", None)
        if cache is None or cache[0] != (day, hour):
            cands = []
            for y in range(10):
                for x in range(10):
                    key = (x, y)
                    t = sim[key] if key in sim else tiles[y][x]
                    if not isinstance(t, dict):
                        continue
                    if t.get("kind") == "PLANT":
                        v = self._plant_visit(key, t, day, self.val, self.final)
                    elif t.get("animal"):
                        v = self._animal_visit(key, t, day, self.val, self.final)
                    else:
                        v = None
                    if v is None:
                        continue
                    acts = []
                    for a in v.acts:
                        op = a[0]
                        if op == "WATER" and t.get("watered_today"): continue
                        if op == "FEED" and t.get("fed_today"): continue
                        if op == "CARE" and t.get("cared_today"): continue
                        if op == "COLLECT_FERTILIZER" and not t.get("fertilizer_available"): continue
                        if op == "HARVEST" and int(t.get("yield_units", 0) or 0) <= 0: continue
                        if op in ("PLANT", "DIG", "BUILD_COOP", "BUILD_PASTURE", "PLACE"): continue
                        acts.append(list(a))
                    if not acts:
                        continue
                    # value of the remaining actions only (rough: scale by the share of actions left)
                    val = v.value * len(acts) / max(1, len(v.acts))
                    if any(a[0] == "CARE" for a in acts) and not t.get("fed_today") and not any(a[0] == "FEED" for a in acts):
                        acts = [a for a in acts if a[0] != "CARE"]
                        if not acts:
                            continue
                    cands.append((key, acts, val, v.must))
            self._dcache = ((day, hour), cands)
            cache = self._dcache
        best = None
        for key, acts, val, must in cache[1]:
            if key in claimed:
                continue
            need_w = any(a[0] == "FEED" for a in acts) and inv.get("WHEAT", 0) <= 0
            need_f = any(a[0] == "FERTILIZE" for a in acts) and inv.get("FERTILIZER", 0) <= 0
            acts2 = acts
            if need_f:
                acts2 = [a for a in acts2 if a[0] != "FERTILIZE"]
            detour = 0; pick = None
            if need_w:
                if shed.get("WHEAT", 0) <= 0:
                    acts2 = [a for a in acts2 if a[0] not in ("FEED", "CARE")]
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
            if v2 < GC_P["dispatch_min_value"]:
                continue
            sc = (1e4 if must else 0) + v2 / (cost + 0.5)
            if best is None or sc > best[0]:
                best = (sc, key, acts2, pick)
        if best is None:
            return None
        _, key, acts2, pick = best
        q = []
        if pick is not None:
            q.append((pick, ["PICKUP", "WHEAT", 2], None))
        for a in acts2:
            q.append((key, a, None))
        _GC_REPORT["gc_dispatch"] = _GC_REPORT.get("gc_dispatch", 0) + 1
        return q

    def _step_unit(self, u, pos, tiles, inv, seeds, planting, sim, shed, room, hour=0):
        q = self.queues.get(u)
        if q and hour >= GC_P["trim_hour"]:
            self._trim_queue(q, pos, 23 - hour)
        while q:
            tgt, act, _v = q[0]
            if tuple(pos) != tuple(tgt):
                dx = tgt[0] - pos[0]; dy = tgt[1] - pos[1]
                if dx:
                    return ["EAST"] if dx > 0 else ["WEST"]
                return ["SOUTH"] if dy > 0 else ["NORTH"]
            key = (pos[0], pos[1])
            tile = sim[key] if key in sim else tiles[pos[1]][pos[0]]
            if act[0] == "DROP" and sum(int(x) for x in inv.values()) > room[0]:
                # the shed cannot take the load yet: wait a turn for the sale that makes room
                return ["PASS"]
            if self._useful(act, tile, inv, seeds, planting, shed, room):
                q.pop(0)
                if act[0] == "PLANT":
                    planting[act[1]] = planting.get(act[1], 0) + 1
                if act[0] == "PICKUP":
                    n = int(act[2]) if len(act) >= 3 else 1
                    shed[act[1]] = max(0, shed.get(act[1], 0) - n)
                if act[0] == "DROP":
                    n = sum(int(x) for x in inv.values())
                    room[0] -= n
                    for k2, n2 in inv.items():
                        shed[k2] = shed.get(k2, 0) + int(n2)
                return act
            q.pop(0)
            _GC_REPORT["gc_noops"] += 1
        return ["PASS"]

    def act(self, obs):
        hour = int(obs["hour"]); day = int(obs["day"])
        me = self.me
        farm = obs["farms"][me]
        priv = obs["private"]
        if self.day_plan != day:
            self.plan_day(obs)
            self.day_plan = day
            self.queues = {u: q for u, q in enumerate(self._compile(self.routes, self.spawns))}
        tiles = farm["tiles"]
        seeds = dict(priv["seeds"])
        shed = {k: int(v) for k, v in dict(priv["shed"]).items()}
        room = [100 - sum(shed.values())]
        invs = list(priv["inventories"])
        planting = {}
        sim = {}
        positions = [farm["farmer"]] + list(farm["hands"])
        units = []
        claimed = {tgt for qq in self.queues.values() for tgt, _a, _v in (qq or [])}
        for u, pos in enumerate(positions):
            inv = dict(invs[u]) if u < len(invs) else {}
            if GC_P["dispatch"] and not self.queues.get(u) and hour >= 1 and not (self.final and hour >= 18):
                nq = self._dispatch(u, pos, inv, 23 - hour + 1, tiles, sim, seeds, shed, claimed, day, hour)
                if nq:
                    self.queues[u] = nq
                    claimed.update(tgt for tgt, _a, _v in nq)
            a = self._step_unit(u, pos, tiles, inv, seeds, planting, sim, shed, room, hour)
            key = (pos[0], pos[1])
            if a[0] in ("WATER", "CARE", "FEED", "HARVEST", "COLLECT_FERTILIZER") and isinstance(tiles[pos[1]][pos[0]], dict):
                t2 = dict(sim[key] if key in sim else tiles[pos[1]][pos[0]])
                if a[0] == "WATER": t2["watered_today"] = True
                elif a[0] == "CARE": t2["cared_today"] = True
                elif a[0] == "FEED": t2["fed_today"] = True
                elif a[0] == "HARVEST": t2["yield_units"] = 0
                elif a[0] == "COLLECT_FERTILIZER": t2["fertilizer_available"] = False
                sim[key] = t2
            units.append(a)
        carried = 0
        self.carried_items = {}
        for u in range(len(positions)):
            if units[u][0] == "DROP":
                continue
            inv = dict(invs[u]) if u < len(invs) else {}
            carried += sum(int(x) for x in inv.values())
            for k2, n2 in inv.items():
                self.carried_items[k2] = self.carried_items.get(k2, 0) + int(n2)
        market = self._market(obs, shed, carried, hour, day)
        if hour == 23:
            left = [(u, len(q), sum(1 for _, a, _v in q if a[0] not in ("DROP",))) for u, q in self.queues.items() if q]
            _GC_REPORT["gc_unfinished_units"] = _GC_REPORT.get("gc_unfinished_units", 0) + len(left)
            _GC_REPORT["gc_unfinished_acts"] = _GC_REPORT.get("gc_unfinished_acts", 0) + sum(x[2] for x in left)
            _GC_REPORT["gc_units_seen"] = _GC_REPORT.get("gc_units_seen", 0) + len(positions)
            _GC_REPORT["gc_units_planned"] = _GC_REPORT.get("gc_units_planned", 0) + len(self.routes)
        return {"farmer": units[0], "hands": units[1:], "market": market[:10]}

    # ------------------------------------------------------------------ market
    def _market(self, obs, shed, carried, hour, day):
        step = int(obs["step"])
        sells = self._sell_orders(obs, shed, carried, hour, day, step)
        prem = [o for o in sells if o[1] in _GC_PREMIUM]
        rest = [o for o in sells if o[1] not in _GC_PREMIUM]
        if hour == 0:
            fixed = list(self.orders0)
            h0 = max(0, min(self.hires_planned, 10 - len(fixed)))
            self.hires_left = self.hires_planned - h0
            orders = fixed + [["HIRE"]] * h0
            return orders[:10]
        if hour == 1:
            h1 = min(self.hires_left, 10 - len(self.orders1))
            self.hires_left -= h1
            return ([["HIRE"]] * h1 + list(self.orders1) + prem + rest)[:10]
        if self.hires_left and hour == 2:
            h2 = min(self.hires_left, 10)
            self.hires_left = 0
            return ([["HIRE"]] * h2 + prem + rest)[:10]
        return prem + rest

    def _sell_orders(self, obs, shed, carried, hour, day, step):
        inv = obs["market"]["inventory"]
        out = []
        reserve = self.reserve
        last = step >= 716 or day >= 29
        ci = getattr(self, "carried_items", {})
        total_shed = sum(int(v) for v in shed.values())
        pressure = total_shed + carried > GC_P["drip_room"]
        for p in _GC_PRODUCTS:
            n = int(shed.get(p, 0))
            if not last:
                keep = int(reserve.get(p, 0))
                if hour >= GC_P["reserve_release_hour"]:
                    # what units carry now lands in the shed tonight and covers tomorrow's needs
                    keep = max(0, keep - int(ci.get(p, 0)))
                n -= keep
            if n <= 0:
                continue
            lot = GC_P["drip"].get(p) if GC_P["drip_on"] else None
            if lot and not last and not pressure and day < 29:
                n = min(n, lot)
            out.append(["SELL", p, n])
        # end-of-day room for carried goods: sell reserves too if the auto-drop would overflow
        if hour == 23 and not last:
            total = sum(int(v) for v in shed.values()) - sum(int(o[2]) for o in out)
            over = total + carried - 100
            if over > 0:
                _GC_REPORT["gc_room_sells"] += over
                for p in ("FERTILIZER", "WHEAT"):
                    k = min(over, int(shed.get(p, 0)) - sum(int(o[2]) for o in out if o[1] == p))
                    if k > 0:
                        out.append(["SELL", p, k]); over -= k
        return out


_GC = GoldCtl()
_GC_PARENT = agent


def agent(observation, configuration=None):
    step = int(observation["step"])
    if step == 0:
        _GC.reset()
    _GC.me = int(observation["player"])
    if step < GC_P["start"]:
        return _GC_PARENT(observation, configuration)
    try:
        return _GC.act(observation)
    except Exception as e:  # never forfeit a turn
        _GC_REPORT["gc_errors"] += 1
        _GC_REPORT["gc_last_error"] = repr(e)[:200]
        return {"farmer": ["PASS"], "hands": [], "market": []}


agent.telemetry = _GC_REPORT
globals().pop("kaggle_submission_agent", None)
kaggle_submission_agent = agent
