# =====================================================================================
# MOON: season planner that takes over every unit and the market from step MOON_START.
# Appended after the chassis; before MOON_START the chassis agent plays unchanged.
# Each day at hour 0 it values every tile job, routes all units by cheapest insertion,
# and hires hands only while the marginal hand earns its Fibonacci wage.
# =====================================================================================
import math as _m_math

MOON_START = 144
MOON_P = dict(
    land_ne_money=1100, land_sw_money=2400, land_sw_day=8, land_se=False,
    straw_last_day=12, straw_d6=16, straw_d7=20, straw_d10=33,
    tom_first_day=9, tom_last_day=18, tom_per_shop=6, tom_cap=30,
    carrot_pet=8, carrot_fm=4, carrot_first_day=9, wheat_extra=6, fill_wheat_day=24, fill_carrot_day=26,
    shed_credit=0.7, sell_drop=0.8,
    cows_base=6, cows_per_shop=1, sheep_base=2, sheep_per_yarn=5, geese_base=0, geese_per_shop=2,
    melon_deadline=8, og_harvest=2, route_cap=23, drop_reserve=3, h0_sells=0, turn_cost=5.0, fert_gate=1.0, care_gate=1.0, hot_price=60, drop_value=2000, herd_scarce=1.1, load_limit=24, load_limit_final=16, fert_keep=6, fert_floor=25, shed_target=92,
    herd_last_day=14, herd_per_day=4, max_hires=13, care=True, sell_margin=1.0, labor_turn=2.0,
)

_M_CROPS = {
    "WHEAT": dict(seed=10, fy=2, my=4, iv=0, mx=6, on=False),
    "CARROT": dict(seed=20, fy=2, my=3, iv=0, mx=4, on=False),
    "TOMATO": dict(seed=50, fy=8, my=8, iv=1, mx=4, on=True),
    "STRAWBERRY": dict(seed=100, fy=10, my=10, iv=2, mx=4, on=True),
    "MELON": dict(seed=80, fy=10, my=12, iv=0, mx=6, on=False),
}
_M_ANIM = {
    "GOOSE": dict(cost=300, st="COOP", fy=4, iv=1, held=4, prod="EGG"),
    "COW": dict(cost=400, st="PASTURE", fy=8, iv=2, held=6, prod="MILK"),
    "SHEEP": dict(cost=500, st="PASTURE", fy=6, iv=3, held=6, prod="WOOL"),
}
_M_MKT = {
    "WHEAT": (25, 400, "sqrt", 0.80, "log", 0.20), "CARROT": (35, 450, "hinge", 1.00, "sqrt", 0.70),
    "TOMATO": (60, 200, "hinge", 0.40, "sqrt", 0.60), "STRAWBERRY": (120, 100, "sqrt", 0.70, "linear", 1.60),
    "MELON": (250, 300, "log", 0.20, "sq", 3.60), "EGG": (50, 332, "hinge", 0.40, "log", 0.20),
    "MILK": (160, 122, "sqrt", 0.60, "linear", 1.60), "WOOL": (200, 105, "log", 0.20, "sq", 3.20),
    "FERTILIZER": (100, 200, "linear", 0.40, "linear", 0.40),
}
_M_SHOPS = {
    "BAKERY": ["EGG", "WHEAT"], "PIZZA_SHOP": ["MILK", "TOMATO", "WHEAT"],
    "BRUNCH_SPOT": ["EGG", "WHEAT", "STRAWBERRY"], "YARN_STORE": ["WOOL"],
    "ICE_CREAM_SHOP": ["STRAWBERRY", "MILK", "WHEAT"], "PET_CAFE": ["CARROT"],
    "SMOOTHIE_SHOP": ["STRAWBERRY", "MILK"], "FARMERS_MARKET": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"],
}
_M_PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]
_M_ACCESS = [(4, 4), (5, 4), (4, 5), (5, 5)]
_M_MOVES = {(0, -1): "NORTH", (0, 1): "SOUTH", (1, 0): "EAST", (-1, 0): "WEST"}
_M_REPORT = dict(days=0, hires=0, errors=0, dropped_jobs=0, planted=0, bought_animals=0)


def _m_shape(f, x, T):
    x = max(0.0, x)
    if f == "linear": return x
    if f == "sq": return x * x
    if f == "sqrt": return _m_math.sqrt(x)
    if f == "log": return _m_math.log(1.0 + x)
    if f == "hinge":
        u = x / T
        return u + 8.0 * max(0.0, u - 1.0) ** 2
    return x


def _m_price(item, inv):
    base, T, bf, bt, af, at = _M_MKT[item]
    if inv < 10000:
        amp = bt * base / _m_shape(bf, T, T)
        p = base + amp * _m_shape(bf, 10000 - inv, T)
    else:
        amp = at * base / _m_shape(af, T, T)
        p = base - amp * _m_shape(af, inv - 10000, T)
    return max(1, int(round(p)))


def _m_fib(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def _m_quad(x, y):
    return ("N" if y < 5 else "S") + ("W" if x < 5 else "E")


def _m_dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _m_g(d, k, default=None):
    if isinstance(d, dict): return d.get(k, default)
    return getattr(d, k, default)


class _MoonNode:
    __slots__ = ("pos", "acts", "need", "value", "prio", "tag", "earliest", "deadline", "units")

    def __init__(self, pos, acts, need=None, value=0.0, prio=1, tag="", earliest=0, deadline=99):
        self.pos = pos; self.acts = acts; self.need = need or {}
        self.value = value; self.prio = prio; self.tag = tag; self.earliest = earliest
        self.deadline = deadline
        self.units = 0


class _MoonRoute:
    """A unit's day: optional wait, pickups at its shed spawn, then tile visits in order.
    Time is the hour at which the next action executes; `cap` is the last usable hour + 1."""
    __slots__ = ("unit", "start", "cap", "nodes", "hour0", "bought")

    def __init__(self, unit, start, cap, hour0, bought=()):
        self.unit = unit; self.start = start; self.cap = cap; self.nodes = []; self.hour0 = hour0
        self.bought = set(bought)

    def needs(self, nodes=None):
        n = {}
        for nd in (self.nodes if nodes is None else nodes):
            for k, v in nd.need.items():
                n[k] = n.get(k, 0) + v
        return n

    def pick_start(self, need):
        # items bought at hour 0 reach the shed after that hour's unit actions
        if self.hour0 == 0 and any(k in self.bought for k in need):
            return 1
        return self.hour0

    def end(self, nodes=None):
        nodes = self.nodes if nodes is None else nodes
        need = self.needs(nodes)
        t = self.pick_start(need) + len(need)
        p = self.start
        for nd in nodes:
            t += _m_dist(p, nd.pos)
            if t < nd.earliest:
                t = nd.earliest
            t += len(nd.acts)
            if t > nd.deadline:
                return 999
            p = nd.pos
        return t

    def cost(self, nodes=None):
        return self.end(nodes) - self.hour0

    def fits(self, nodes=None):
        return self.end(nodes) <= self.cap


class Moon:
    def __init__(self):
        self.day = -1
        self.queues = {}
        self.planned_start = {}
        self.hires_h0 = 0
        self.hires_h1 = 0
        self.sched = {}
        self.carry = []
        self.exp_pos = {}
        self.last_hires = 8
        self.reserve = {}
        self.me = 0
        self.plant_plan = {}
        self.herd_buy = []

    # ------------------------------------------------------------------ helpers
    def _demand(self, shops):
        d = {p: 1.0 for p in _M_PRODUCTS if p != "FERTILIZER"}
        d["FERTILIZER"] = 0.0
        for s in shops:
            prods = _M_SHOPS.get(s, [])
            mult = 12.0 if len(prods) == 1 else 6.0
            for p in prods:
                d[p] += mult
        return d

    def _future_demand(self, shops, day, horizon_end=29):
        """Expected units consumed per product from `day` to the end, with unrevealed shops at 1/8 each."""
        d_now = self._demand(shops)
        tot = {p: d_now[p] * max(0, horizon_end - day) for p in d_now}
        nshops = len(shops)
        for k in range(nshops, 8):
            unlock_day = 3 * (k + 1)
            if unlock_day <= day or unlock_day > horizon_end:
                continue
            days_left = horizon_end - unlock_day
            for s, prods in _M_SHOPS.items():
                mult = 12.0 if len(prods) == 1 else 6.0
                for p in prods:
                    tot[p] += mult * days_left / 8.0
        return tot

    def _pstar(self, obs, item, extra_supply=0.0):
        """Marginal value of one more unit of `item`: price at the projected end-of-season stock."""
        inv = obs["market"]["inventory"][item]
        return _m_price(item, inv + extra_supply)

    # ------------------------------------------------------------------ main
    def act(self, obs):
        step = obs["step"]; day = step // 24; hour = step % 24
        self.me = int(obs["player"])
        self.day_hour = hour
        farm = obs["farms"][self.me]
        if day != self.day:
            try:
                self.plan_day(obs)
            except Exception:
                _M_REPORT["errors"] += 1
                self.queues = {}
                self.sched = {}; self.carry = []
            self.day = day
        hands = farm["hands"]
        out = []
        for u in range(len(hands) + 1):
            pos = tuple(farm["farmer"]) if u == 0 else tuple(hands[u - 1])
            exp = self.exp_pos.get(u)
            if exp is None:
                exp = self.planned_start.get(u, (pos, 0))[0]
            if tuple(exp) != pos and self.queues.get(u):
                try:
                    self._reroute(u, pos)
                except Exception:
                    _M_REPORT["errors"] += 1
                    self.queues[u] = []
                _M_REPORT["reroutes"] = _M_REPORT.get("reroutes", 0) + 1
            a = self._pop(u)
            if a[0] in ("NORTH", "SOUTH", "EAST", "WEST"):
                dx, dy = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)}[a[0]]
                pos = (min(9, max(0, pos[0] + dx)), min(9, max(0, pos[1] + dy)))
            self.exp_pos[u] = pos
            out.append(a)
        out_f = out[0]
        out_h = out[1:]
        sched = list(self.carry) + list(self.sched.get(hour, []))
        sells = []
        try:
            sells = self.sell_orders(obs, max(MOON_P["h0_sells"], 10 - len(sched)) if hour <= 1 else max(4, 10 - len(sched)))
        except Exception:
            _M_REPORT["errors"] += 1
        room = 10 - len(sells)
        self.carry = sched[room:]
        market = sells + sched[:room]
        return {"farmer": out_f, "hands": out_h, "market": market[:10]}

    def _pop(self, u):
        q = self.queues.get(u)
        if q:
            return q.pop(0)[0]
        return ["PASS"]

    # ------------------------------------------------------------------ planning
    def _next_prod_day(self, t, day):
        """First day D >= day whose end-of-day refresh produces for this animal."""
        a = _M_ANIM[t["animal"]]
        D = day
        while D <= 29:
            k = D + 1 - t["placed_day"] - a["fy"]
            if k >= 0 and k % a["iv"] == 0:
                return D
            D += 1
        return 99

    def plan_day(self, obs):
        _M_REPORT["days"] += 1
        step = obs["step"]; day = step // 24
        me = self.me
        farm = obs["farms"][me]
        priv = obs["private"]
        shed = dict(priv["shed"]); seeds = dict(priv["seeds"])
        money = float(farm["money"])
        shops = list(_m_g(obs["town"], "unlocked_shops", []) or [])
        tiles = farm["tiles"]
        self.tiles_today = tiles
        P = MOON_P
        final = day >= 29
        orders0 = []
        bought = set()
        n_est = max(6, getattr(self, "last_hires", 8))
        reserve = sum(_m_fib(k) for k in range(n_est)) + 50
        inv_m = obs["market"]["inventory"]
        shed_val = sum(shed.get(p, 0) * _m_price(p, inv_m[p]) for p in ("CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL"))
        money += P["shed_credit"] * min(shed_val, 4000) - reserve
        # --- land
        quads = list(farm["unlocked_quadrants"])
        new_quads = []
        if not final:
            if "NE" not in quads and day >= 6 and money >= P["land_ne_money"] - 1000 + 1000:
                orders0.append(["BUY_LAND"]); money -= 1000; new_quads.append("NE")
            elif "NE" in quads and "SW" not in quads and day >= P["land_sw_day"] and money >= P["land_sw_money"] and day <= 16:
                orders0.append(["BUY_LAND"]); money -= 2000; new_quads.append("SW")
            elif P["land_se"] and "SW" in quads and "SE" not in quads and money >= 9000 and day <= 14:
                orders0.append(["BUY_LAND"]); money -= 4000; new_quads.append("SE")
        owned = set(quads) | set(new_quads)

        # --- values
        fut = self._future_demand(shops, day)
        val = {}
        for p in _M_PRODUCTS:
            val[p] = float(_m_price(p, obs["market"]["inventory"][p]))
        for p in ("STRAWBERRY", "TOMATO", "CARROT", "MILK", "WOOL", "EGG", "WHEAT"):
            base = _M_MKT[p][0]
            val[p] = 0.5 * val[p] + 0.5 * base * min(1.3, 0.5 + fut[p] / 250.0)
        val["FERTILIZER"] = max(20.0, float(_m_price("FERTILIZER", obs["market"]["inventory"]["FERTILIZER"])))
        wheat_cost = float(_m_price("WHEAT", obs["market"]["inventory"]["WHEAT"] - 1))
        self.val = val
        pnow = {p: float(_m_price(p, obs["market"]["inventory"][p])) for p in _M_PRODUCTS}
        turn = P["turn_cost"]
        fert_v = pnow["FERTILIZER"] + turn

        # --- scan farm
        plants = []; animals = []; empties = []; weeds = []; structs = []
        newland = set()
        for y in range(10):
            for x in range(10):
                t = tiles[y][x]
                if t == "LOCKED":
                    if _m_quad(x, y) in owned:
                        empties.append((x, y)); newland.add((x, y))
                    continue
                if t is None:
                    empties.append((x, y)); continue
                k = t.get("kind")
                if k == "PLANT": plants.append(((x, y), t))
                elif k == "WEED": weeds.append((x, y))
                elif "animal" in t: animals.append(((x, y), t))
                elif k in ("COOP", "PASTURE"): structs.append(((x, y), k))

        nodes = []
        # --- plant jobs
        harvest_free = []
        for pos, t in plants:
            crop = t["crop"]; cd = _M_CROPS[crop]
            age = day - t["planted_day"]
            cu = t["consecutive_unwatered"]
            fert_active = t.get("fertilized_until_day", -1) >= day
            acts = []; need = {}; value = 0.0
            yu = t["yield_units"]
            if not cd["on"]:
                ws = (cd["my"] + 1) // 2
                ready = age >= cd["fy"]
                in_window = ws <= age <= cd["my"]
                if final:
                    if ready and yu > 0:
                        nodes.append(_MoonNode(pos, [["HARVEST"]], value=yu * val[crop], prio=0, tag="H"))
                    continue
                want_fert = crop in ("WHEAT", "CARROT") and age == ws and not fert_active and yu < cd["mx"]                     and (2 if crop == "WHEAT" else 1) * pnow[crop] > fert_v * P["fert_gate"]
                yu2 = yu
                if in_window and yu < cd["mx"]:
                    gain = min(2 if (fert_active or want_fert) else 1, cd["mx"] - yu)
                    if want_fert:
                        acts.append(["FERTILIZE"]); need["FERTILIZER"] = 1
                    acts.append(["WATER"]); value += gain * val[crop]
                    yu2 = yu + gain
                elif cu >= 1:
                    acts.append(["WATER"]); value += 3 * val[crop]
                harvest_now = ready and (age >= cd["my"] or yu2 >= cd["mx"])
                if crop == "MELON":
                    harvest_now = age >= 10 and yu2 > 0 and (yu2 >= 6 or age >= 12 or day >= 28)
                if day == 28 and ready and yu2 > 0 and age + 1 > cd["my"] + 1:
                    harvest_now = True
                if harvest_now and crop == "MELON":
                    acts.append(["HARVEST"]); value += yu2 * val[crop] * 0.5
                    nd = _MoonNode(pos, acts, need, value, 0, "M", deadline=MOON_P["melon_deadline"])
                    nodes.append(nd)
                    continue
                if harvest_now:
                    acts.append(["HARVEST"]); value += yu2 * val[crop] * 0.5
                    harvest_free.append((pos, acts, need, value, MOON_P["melon_deadline"] if crop == "MELON" else 99))
                    continue
                if acts:
                    nodes.append(_MoonNode(pos, acts, need, value, 1 if cu >= 1 or in_window else 2, "C"))
            else:
                k_next = age + 1 - cd["fy"]
                eve = k_next >= 0 and k_next % cd["iv"] == 0 and (k_next // cd["iv"] + 1) <= cd["mx"] and day <= 28
                done = t["max_lifespan_step"] >= 0
                if final:
                    if yu > 0:
                        nodes.append(_MoonNode(pos, [["HARVEST"]], value=yu * val[crop], prio=0, tag="H"))
                    continue
                if yu > 0 and (yu >= MOON_P["og_harvest"] or (eve and yu + 2 > 4) or done or day >= 28 or cu >= 1 or eve):
                    acts.append(["HARVEST"]); value += yu * val[crop] * 0.5
                if eve:
                    covered = 2 if crop == "STRAWBERRY" else 3
                    if not fert_active and covered * pnow[crop] > fert_v * P["fert_gate"]:
                        acts.append(["FERTILIZE"]); need["FERTILIZER"] = 1
                    acts.append(["WATER"]); value += val[crop]
                elif cu >= 1 and not done:
                    acts.append(["WATER"]); value += 4 * val[crop]
                if done and yu == 0 and not acts:
                    continue
                if acts:
                    hot = yu >= 1 and val[crop] >= MOON_P["hot_price"]
                    nodes.append(_MoonNode(pos, acts, need, value, 1 if (cu >= 1 or eve or yu >= 3 or hot) else 2, "O"))

        # --- animal jobs
        n_anim = {"GOOSE": 0, "COW": 0, "SHEEP": 0}
        for pos, t in animals:
            a = _M_ANIM[t["animal"]]; n_anim[t["animal"]] += 1
            acts = []; need = {}; value = 0.0
            yu = t["yield_units"]
            pv = val[a["prod"]]
            if final:
                if yu > 0:
                    nodes.append(_MoonNode(pos, [["HARVEST"]], value=yu * pv, prio=0, tag="H"))
                continue
            nprod = self._next_prod_day(t, day)
            pend = t.get("pending_care_bonus", 0)
            must_feed = t["consecutive_unfed"] >= 1 and day <= 28
            care_cost = turn if must_feed else (wheat_cost + 2 * turn)
            care = P["care"] and nprod <= 28 and (yu + 1 + pend) < a["held"] and pnow[a["prod"]] > care_cost * P["care_gate"]
            feed_for_bonus = nprod == day and pend > 0
            if must_feed or care or feed_for_bonus:
                acts.append(["FEED"]); need["WHEAT"] = 1
                value += 300.0 if must_feed else pv * 0.3
            if care:
                acts.append(["CARE"]); value += pv * 0.9
            if yu > 0 and (yu + 1 + pend >= a["held"] or day >= 27 or acts):
                acts.append(["HARVEST"]); value += yu * pv * 0.3
            if t["fertilizer_available"] and day <= 28:
                acts.append(["COLLECT_FERTILIZER"]); value += val["FERTILIZER"] * 0.8
            if acts:
                nodes.append(_MoonNode(pos, acts, need, value, 1 if (must_feed or yu >= a["held"] - 2) else 2, "A"))

        # --- herd: animals waiting in the shed first, then purchases; both reserve their tiles
        free_tiles = sorted(set(empties) | set(weeds), key=lambda p: _m_dist(p, (4.5, 4.5)))
        free_struct = {"COOP": [p for p, k in structs if k == "COOP"], "PASTURE": [p for p, k in structs if k == "PASTURE"]}
        herd_tiles = set()
        placements = []
        for animal in ("COW", "SHEEP", "GOOSE"):
            for _ in range(int(shed.get(animal, 0))):
                st = _M_ANIM[animal]["st"]
                if free_struct[st]:
                    placements.append((animal, free_struct[st].pop(0), False, False))
                else:
                    pool = [p for p in free_tiles if p not in herd_tiles]
                    if not pool:
                        break
                    placements.append((animal, pool[0], True, False)); herd_tiles.add(pool[0])
                n_anim[animal] += 1
        herd = self._choose_herd(obs, day, n_anim, shops, fut, val, money, free_struct, [p for p in free_tiles if p not in herd_tiles])
        for animal, pos, build in herd:
            if money < _M_ANIM[animal]["cost"] + 50:
                continue
            orders0.append(["BUY_ANIMAL", animal, 1]); money -= _M_ANIM[animal]["cost"]; bought.add(animal)
            _M_REPORT["bought_animals"] += 1
            placements.append((animal, pos, build, True))
            if build:
                herd_tiles.add(pos)
        for animal, pos, build, new in placements:
            acts = []
            if build:
                if pos in weeds: acts.append(["DIG"])
                acts.append(["BUILD_COOP" if _M_ANIM[animal]["st"] == "COOP" else "BUILD_PASTURE"])
            acts.append(["PLACE", animal])
            nodes.append(_MoonNode(pos, acts, {animal: 1}, 900.0, 0, "N", earliest=1 if new else 0))

        # --- new plantings on free tiles (after the herd took its tiles)
        hf_map = {p: (acts, need, value, dl) for p, acts, need, value, dl in harvest_free}
        cand = [p for p in free_tiles if p not in herd_tiles] + [p for p in hf_map]
        plan = self._choose_crops(obs, day, cand, plants, n_anim, shops, fut, val, money)
        # seeds are bought just in time by the compiled routes; only cap plantings by cash
        kept = {}
        spend = 0
        for pos, crop in sorted(plan.items(), key=lambda kv: -_M_CROPS[kv[1]]["seed"]):
            c = _M_CROPS[crop]["seed"]
            if seeds.get(crop, 0) > 0:
                seeds[crop] -= 1; kept[pos] = crop
            elif spend + c <= money + 200:
                spend += c; kept[pos] = crop
        plan = kept
        money -= spend
        _M_REPORT["planted"] += len(plan)
        weed_set = set(weeds)
        for pos, (acts, need, value, dl) in hf_map.items():
            acts = list(acts)
            e = 0
            if pos in plan:
                acts += [["PLANT", plan[pos]], ["WATER"]]
                value += 60.0
                e = 1
            nodes.append(_MoonNode(pos, acts, need, value, 0 if dl < 99 else 1, "HP", earliest=e, deadline=dl))
        for pos, crop in plan.items():
            if pos in hf_map:
                continue
            acts = ([["DIG"]] if pos in weed_set else []) + [["PLANT", crop], ["WATER"]]
            nodes.append(_MoonNode(pos, acts, {}, 80.0, 1, "P", earliest=1))
        for nd in nodes:
            if nd.pos in newland:
                nd.earliest = max(nd.earliest, 1)

        # --- wheat / fertilizer supply
        need_w = sum(n.need.get("WHEAT", 0) for n in nodes)
        need_f = sum(n.need.get("FERTILIZER", 0) for n in nodes)
        have_w = shed.get("WHEAT", 0); have_f = shed.get("FERTILIZER", 0)
        if need_w > have_w:
            buy_w = need_w - have_w
            orders0.append(["BUY_PRODUCT", "WHEAT", buy_w]); money -= buy_w * wheat_cost; bought.add("WHEAT")
        if need_f > have_f:
            short = need_f - have_f
            fprice = _m_price("FERTILIZER", obs["market"]["inventory"]["FERTILIZER"] - 1)
            lo = [n for n in nodes if n.need.get("FERTILIZER") and n.tag != "O"]
            hi = [n for n in nodes if n.need.get("FERTILIZER") and n.tag == "O"]
            for n in lo:
                if short <= 0: break
                n.acts = [a for a in n.acts if a[0] != "FERTILIZE"]; n.need = {}
                short -= 1
            if short > 0 and fprice < val["STRAWBERRY"] and money > short * fprice + 300:
                orders0.append(["BUY_PRODUCT", "FERTILIZER", short]); money -= short * fprice; bought.add("FERTILIZER")
                short = 0
            for n in hi:
                if short <= 0: break
                n.acts = [a for a in n.acts if a[0] != "FERTILIZE"]; n.need = {}
                short -= 1
        self.need_today = {"WHEAT": need_w, "FERTILIZER": need_f}
        for nd in nodes:
            if any(a[0] == "HARVEST" for a in nd.acts):
                t = tiles[nd.pos[1]][nd.pos[0]]
                u = t.get("yield_units", 0) if isinstance(t, dict) else 0
                if isinstance(t, dict) and t.get("kind") == "PLANT" and not _M_CROPS[t["crop"]]["on"] and any(a[0] == "WATER" for a in nd.acts):
                    u = min(_M_CROPS[t["crop"]]["mx"], u + 2)
                nd.units = u
        self.herd_size = len(animals) + len(herd)
        self._route_and_hire(obs, day, nodes, orders0, money, final, bought)

    # ------------------------------------------------------------------ strategy
    def _choose_crops(self, obs, day, free_tiles, plants, n_anim, shops, fut, val, money):
        P = MOON_P
        if day >= 27:
            return {}
        cur = {"WHEAT": 0, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 0}
        for pos, t in plants:
            if t["max_lifespan_step"] < 0 or t["yield_units"] > 0 or not _M_CROPS[t["crop"]]["on"]:
                cur[t["crop"]] += 1
        tom_shops = sum(1 for s in shops if "TOMATO" in _M_SHOPS[s])
        pet = shops.count("PET_CAFE"); fm = shops.count("FARMERS_MARKET")
        target = {}
        if day <= 6: ts = P["straw_d6"]
        elif day <= 9: ts = P["straw_d7"]
        elif day <= P["straw_last_day"]: ts = P["straw_d10"]
        else: ts = 0
        target["STRAWBERRY"] = ts
        target["TOMATO"] = min(P["tom_cap"], P["tom_per_shop"] * tom_shops) if P["tom_first_day"] <= day <= P["tom_last_day"] else 0
        target["CARROT"] = (P["carrot_pet"] * pet + P["carrot_fm"] * fm) if P["carrot_first_day"] <= day <= P["fill_carrot_day"] else 0
        herd = sum(n_anim.values())
        target["WHEAT"] = (herd + P["wheat_extra"]) if day <= P["fill_wheat_day"] else 0
        tiles = sorted(set(free_tiles), key=lambda p: _m_dist(p, (4.5, 4.5)))
        plan = {}
        budget = money
        for crop in ("WHEAT", "STRAWBERRY", "TOMATO", "CARROT"):
            want = target.get(crop, 0) - cur[crop]
            while want > 0 and tiles and budget >= _M_CROPS[crop]["seed"]:
                pos = tiles.pop() if crop == "WHEAT" else tiles.pop(0)
                plan[pos] = crop; want -= 1; budget -= _M_CROPS[crop]["seed"]
        fill = "WHEAT" if day <= P["fill_wheat_day"] else ("CARROT" if day <= P["fill_carrot_day"] else None)
        if fill and day >= 10:
            while tiles and budget >= _M_CROPS[fill]["seed"]:
                plan[tiles.pop()] = fill; budget -= _M_CROPS[fill]["seed"]
        if MOON_P.get("debug"):
            _M_REPORT.setdefault("log", []).append((day, len(tiles) + len(plan), dict(cur), {k: v for k, v in target.items()}, {c: sum(1 for v in plan.values() if v == c) for c in set(plan.values())}, int(budget)))
        return plan

    def _choose_herd(self, obs, day, n_anim, shops, fut, val, money, free_struct, free_tiles):
        P = MOON_P
        if day < 6:
            return []
        if day > P["herd_last_day"]:
            inv_m = obs["market"]["inventory"]
            scarce = [a for a in _M_ANIM if _m_price(_M_ANIM[a]["prod"], inv_m[_M_ANIM[a]["prod"]]) >= _M_MKT[_M_ANIM[a]["prod"]][0] * P["herd_scarce"]]
            if day > 20 or not scarce:
                return []
        milk_shops = sum(1 for s in shops if "MILK" in _M_SHOPS[s])
        yarn = shops.count("YARN_STORE")
        egg_shops = sum(1 for s in shops if "EGG" in _M_SHOPS[s])
        tgt = {"COW": P["cows_base"] + P["cows_per_shop"] * milk_shops,
               "SHEEP": P["sheep_base"] + P["sheep_per_yarn"] * yarn,
               "GOOSE": P["geese_base"] + P["geese_per_shop"] * egg_shops}
        pool = list(free_tiles)
        out = []
        budget = money
        while len(out) < P.get("herd_per_day", 4):
            gaps = [(n_anim[a] / max(1, tgt[a]), a) for a in ("SHEEP", "COW", "GOOSE") if n_anim[a] < tgt[a] and budget >= _M_ANIM[a]["cost"] + 50]
            if not gaps:
                break
            _, animal = min(gaps)
            st = _M_ANIM[animal]["st"]
            if free_struct[st]:
                pos = free_struct[st].pop(0); build = False
            elif pool:
                pos = pool.pop(0); build = True
            else:
                break
            out.append((animal, pos, build)); n_anim[animal] += 1; budget -= _M_ANIM[animal]["cost"]
        return out

    # ------------------------------------------------------------------ routing
    def _route_and_hire(self, obs, day, nodes, orders0, money, final, bought):
        P = MOON_P
        farm = obs["farms"][self.me]
        fpos = tuple(farm["farmer"])
        cap = 22 if final else P["route_cap"]
        slots0 = 10 - len(orders0)
        max_h = P["max_hires"]
        dl_saved = {id(n): n.deadline for n in nodes if n.deadline < 99}
        for n in nodes:
            n.deadline = 99
        mand = [n for n in nodes if n.prio <= 1]
        opt = sorted([n for n in nodes if n.prio > 1], key=lambda n: -n.value)

        def ang(n):
            return _m_math.atan2(n.pos[1] - 4.5, n.pos[0] - 4.5)

        def radial(ns):
            return sorted(ns, key=lambda n: _m_dist(n.pos, (4.5, 4.5)))

        probe = _MoonRoute(-1, (4, 4), cap, 1, bought)

        def group_cost(ns):
            if not ns:
                return 0
            rs = radial(ns)
            probe.start = min(_M_ACCESS, key=lambda a: _m_dist(a, rs[0].pos))
            return probe.end(rs)

        # sweep: angular order, cut greedily, try every rotation
        seq0 = sorted(mand, key=ang)
        best = None
        n = len(seq0)
        step = 1 if n <= 60 else 2
        for s0 in range(0, max(1, n), step):
            seq = seq0[s0:] + seq0[:s0]
            groups = []; cur = []
            for nd in seq:
                if group_cost(cur + [nd]) <= cap - P["drop_reserve"]:
                    cur.append(nd)
                else:
                    if cur:
                        groups.append(cur)
                    cur = [nd]
            if cur:
                groups.append(cur)
            score = (len(groups), sum(group_cost(g) for g in groups))
            if best is None or score < best[0]:
                best = (score, groups)
        groups = best[1] if best else []
        n_units = max(1, len(groups))
        hires = min(max_h, n_units - 1)
        occ = {a: 0 for a in _M_ACCESS}
        if fpos in occ:
            occ[fpos] += 1
        units = [(0, fpos, 0)]
        for k in range(1, hires + 1):
            sp = sorted(occ.items(), key=lambda kv: (kv[1], _M_ACCESS.index(kv[0])))[0][0]
            occ[sp] += 1
            units.append((k, sp, 1 if k <= slots0 else 2))
        routes = [_MoonRoute(u, sp, cap, h0, bought) for u, sp, h0 in units]
        groups.sort(key=lambda g: -group_cost(g))
        free = list(routes)
        dropped = []
        for g in groups:
            if not free:
                dropped.extend(g); continue
            rg = radial(g)
            r = min(free, key=lambda rr: (rr.hour0, _m_dist(rr.start, rg[0].pos)))
            free.remove(r)
            r.nodes = rg
            r.nodes = self._improve(r)
            while r.nodes and r.end() > r.cap:
                dropped.append(r.nodes.pop())

        def best_insert(nd, rs):
            bi = None
            for r in rs:
                base = r.end()
                for i in range(len(r.nodes) + 1):
                    e = r.end(r.nodes[:i] + [nd] + r.nodes[i:])
                    if e <= r.cap:
                        d = e - base
                        if bi is None or d < bi[0]:
                            bi = (d, r, i)
            return bi

        still = []
        for nd in dropped:
            b = best_insert(nd, routes)
            if b is None:
                still.append(nd)
            else:
                b[1].nodes.insert(b[2], nd)
        dropped = still
        # try to empty the lightest hand's route into the others
        while len(routes) > 1:
            light = min(routes[1:], key=lambda r: sum(len(x.acts) for x in r.nodes))
            others = [r for r in routes if r is not light]
            saved = [(r, list(r.nodes)) for r in others]
            ok = True
            for nd in list(light.nodes):
                b = best_insert(nd, others)
                if b is None:
                    ok = False; break
                b[1].nodes.insert(b[2], nd)
            if ok:
                routes = others
                hires -= 1
            else:
                for r, ns in saved:
                    r.nodes = ns
                break
        # unit indices must be 0..hires in hire order; spawn tiles follow the hire order
        routes.sort(key=lambda r: r.unit)
        occ = {a: 0 for a in _M_ACCESS}
        if fpos in occ:
            occ[fpos] += 1
        for k, r in enumerate(routes):
            r.unit = k
            if k > 0:
                sp = sorted(occ.items(), key=lambda kv: (kv[1], _M_ACCESS.index(kv[0])))[0][0]
                occ[sp] += 1
                r.start = sp
                r.hour0 = 1 if k <= slots0 else 2
        for nd in opt:
            b = best_insert(nd, routes)
            if b is None:
                dropped.append(nd)
            else:
                b[1].nodes.insert(b[2], nd)
        while dropped and hires < max_h and not final:
            wage = _m_fib(hires)
            k = hires + 1
            sp = sorted(occ.items(), key=lambda kv: (kv[1], _M_ACCESS.index(kv[0])))[0][0]
            trial = _MoonRoute(k, sp, cap, 1 if k <= slots0 else 2, bought)
            gain = 0.0; placed = []
            for nd in sorted(dropped, key=lambda x: -x.value):
                b = best_insert(nd, [trial])
                if b is not None:
                    trial.nodes.insert(b[2], nd); gain += nd.value; placed.append(nd)
            if placed and gain > wage * 1.3 + P["labor_turn"] * trial.cost():
                occ[sp] += 1
                hires = k
                routes.append(trial)
                dropped = [x for x in dropped if x not in placed]
            else:
                break
        _M_REPORT["dropped_jobs"] += len(dropped)
        _M_REPORT["dropped_mand"] = _M_REPORT.get("dropped_mand", 0) + sum(1 for x in dropped if x.prio <= 1)
        _M_REPORT["hires"] += hires
        for r in routes:
            ds = [x for x in r.nodes if id(x) in dl_saved]
            if ds:
                rest = [x for x in r.nodes if id(x) not in dl_saved]
                for x in ds:
                    x.deadline = dl_saved[id(x)]
                r.nodes = sorted(ds, key=lambda x: _m_dist(x.pos, r.start)) + rest
                for x in reversed(r.nodes[:len(ds)]):
                    if r.end() < 999:
                        break
                    x.deadline = 99
            r.nodes = self._improve(r)
            while r.nodes and r.end() > r.cap:
                r.nodes.pop()
            self._ensure_drops(r, MOON_P["load_limit"] if not final else MOON_P["load_limit_final"])
        for r in routes:
            _M_REPORT["turns"] = _M_REPORT.get("turns", 0) + (r.end() - r.hour0)
            _M_REPORT["acts"] = _M_REPORT.get("acts", 0) + sum(len(x.acts) for x in r.nodes)
            _M_REPORT["cap_left"] = _M_REPORT.get("cap_left", 0) + max(0, r.cap - r.end())
        _M_REPORT["units"] = _M_REPORT.get("units", 0) + len(routes)
        n0 = min(hires, max(0, slots0))
        self.last_hires = hires
        sched = {0: [["HIRE"]] * n0 + orders0}
        if hires > n0:
            sched[1] = [["HIRE"]] * (hires - n0)
        self.queues = {}
        self.planned_start = {}
        self.exp_pos = {}
        plant_at = {}
        for r in routes:
            q = self._compile(r, final)
            self.queues[r.unit] = q
            if r.unit > 0:
                self.planned_start[r.unit] = (r.start, r.hour0)
            for k, (a, _) in enumerate(q):
                if a[0] == "PLANT":
                    plant_at.setdefault(a[1], []).append(r.hour0 + k)
        seeds = dict(obs["private"]["seeds"])
        for crop, hours in plant_at.items():
            hours.sort()
            have = seeds.get(crop, 0)
            per = {}
            for h in hours[have:]:
                per[h - 1] = per.get(h - 1, 0) + 1
            for h, n in per.items():
                sched.setdefault(max(0, h), []).append(["BUY_SEED", crop, n])
        self.sched = sched
        self.routes = routes

    def _unit_val(self, nd):
        t = self.tiles_today[nd.pos[1]][nd.pos[0]] if getattr(self, "tiles_today", None) else None
        if not isinstance(t, dict):
            return 0.0
        item = t.get("crop") or (_M_ANIM[t["animal"]]["prod"] if "animal" in t else None)
        return float(getattr(self, "val", {}).get(item, 0.0)) if item else 0.0

    def _ensure_drops(self, r, limit):
        """Insert shed visits so a unit never carries more than `limit` harvested units at once.
        Goods then reach the shed during the day and are sold before the nightly drop overflows."""
        if not r.nodes:
            return
        out = []
        load = 0; lval = 0.0
        for nd in r.nodes:
            if nd.tag == "D":
                load = 0; lval = 0.0
                out.append(nd)
                continue
            if nd.units and (load + nd.units > limit or lval > MOON_P["drop_value"]) and load > 0:
                prev = out[-1].pos if out else r.start
                acc = min(_M_ACCESS, key=lambda a: _m_dist(prev, a) + _m_dist(a, nd.pos))
                out.append(_MoonNode(acc, [["DROP"]], {}, 0.0, 1, "D"))
                load = 0; lval = 0.0
            out.append(nd)
            load += nd.units
            lval += nd.units * self._unit_val(nd)
        # the day's last load also has to arrive before night when it is large
        if load > limit // 2:
            prev = out[-1].pos
            acc = min(_M_ACCESS, key=lambda a: _m_dist(prev, a))
            out.append(_MoonNode(acc, [["DROP"]], {}, 0.0, 1, "D"))
        r.nodes = out
        # make room: optional work first, then shed visits; mandatory jobs are never cut here
        while r.end() > r.cap:
            idx = None
            for i in range(len(r.nodes) - 1, -1, -1):
                if r.nodes[i].prio > 1 and r.nodes[i].tag != "D":
                    idx = i; break
            if idx is None:
                for i in range(len(r.nodes) - 1, -1, -1):
                    if r.nodes[i].tag == "D":
                        idx = i; break
            if idx is None:
                _M_REPORT["over_cap"] = _M_REPORT.get("over_cap", 0) + 1
                break
            r.nodes.pop(idx)

    def _insert_drop(self, r):
        """Deliver harvested goods mid-route where the detour is cheap, so they sell today."""
        if not r.nodes:
            return
        val = getattr(self, "val", {})
        best = None
        carried = 0.0
        base = r.end()
        for i in range(1, len(r.nodes) + 1):
            nd = r.nodes[i - 1]
            for a in nd.acts:
                if a[0] == "HARVEST":
                    carried += nd.value
            if carried <= 0:
                continue
            p = nd.pos
            acc = min(_M_ACCESS, key=lambda a: _m_dist(p, a))
            drop = _MoonNode(acc, [["DROP"]], {}, 0.0, 1, "D")
            trial = r.nodes[:i] + [drop] + r.nodes[i:]
            e = r.end(trial)
            if e > r.cap:
                continue
            hours_early = max(0, 24 - r.end(trial[:i + 1]))
            score = carried * min(1.0, hours_early / 12.0) * 0.08 - (e - base) * 6.0
            if best is None or score > best[0]:
                best = (score, trial)
        if best is not None and best[0] > 0:
            r.nodes = best[1]

    def _improve(self, r):
        nodes = list(r.nodes)
        if len(nodes) < 3:
            return nodes
        best = r.end(nodes)
        improved = True
        it = 0
        while improved and it < 20:
            improved = False; it += 1
            n = len(nodes)
            for i in range(n - 1):
                for j in range(i + 1, n):
                    cand = nodes[:i] + nodes[i:j + 1][::-1] + nodes[j + 1:]
                    c = r.end(cand)
                    if c < best:
                        nodes, best, improved = cand, c, True
        return nodes

    def _compile(self, r, final, with_pick=True):
        q = []
        need = r.needs()
        t = r.hour0
        if with_pick:
            ps = r.pick_start(need)
            while t < ps:
                q.append((["PASS"], -1)); t += 1
            for item in ("WHEAT", "FERTILIZER", "GOOSE", "COW", "SHEEP"):
                n = need.get(item, 0)
                if n > 0:
                    q.append((["PICKUP", item, n], -1)); t += 1
        p = r.start
        for k, nd in enumerate(r.nodes):
            steps = []
            p = self._walk(steps, p, nd.pos)
            q.extend((a, k) for a in steps); t += len(steps)
            while t < nd.earliest:
                q.append((["PASS"], k)); t += 1
            q.extend((list(a), k) for a in nd.acts); t += len(nd.acts)
        if final:
            tgt = min(_M_ACCESS, key=lambda a: _m_dist(p, a))
            steps = []
            p = self._walk(steps, p, tgt)
            q.extend((a, len(r.nodes)) for a in steps)
            q.append((["DROP"], len(r.nodes)))
        return q

    def _walk(self, q, p, tgt):
        x, y = p
        while x != tgt[0]:
            dx = 1 if tgt[0] > x else -1
            q.append([_M_MOVES[(dx, 0)]]); x += dx
        while y != tgt[1]:
            dy = 1 if tgt[1] > y else -1
            q.append([_M_MOVES[(0, dy)]]); y += dy
        return (x, y)

    def _reroute(self, u, pos):
        r = None
        for rr in getattr(self, "routes", []):
            if rr.unit == u:
                r = rr
        if r is None:
            self.queues[u] = []
            return
        q = self.queues.get(u) or []
        if not q:
            return
        k0 = q[0][1]
        with_pick = k0 < 0 and any(e[0][0] == "PICKUP" for e in q if e[1] < 0)
        rest = r.nodes[max(0, k0):] if k0 >= 0 else list(r.nodes)
        nr = _MoonRoute(u, pos, r.cap, (self.day_hour if hasattr(self, "day_hour") else r.hour0), r.bought)
        nr.nodes = rest
        nr.nodes = self._improve(nr)
        r.nodes = nr.nodes; r.start = pos
        self.queues[u] = self._compile(nr, self.day >= 29, with_pick)

    # ------------------------------------------------------------------ market
    def sell_orders(self, obs, slots):
        if slots <= 0:
            return []
        step = obs["step"]; day = step // 24; hour = step % 24
        priv = obs["private"]
        shed = priv["shed"]
        inv = obs["market"]["inventory"]
        final = day >= 29
        if final and step >= 712:
            return [["SELL", it, 999] for it in _M_PRODUCTS][:slots]
        herd = getattr(self, "herd_size", 0)
        today = getattr(self, "need_today", {}) if hour <= 1 else {}
        keep = {"WHEAT": 0 if final else herd + 2 + today.get("WHEAT", 0),
                "FERTILIZER": 0 if final else MOON_P["fert_keep"] + today.get("FERTILIZER", 0)}
        carried = 0
        for u_inv in priv.get("inventories", []) or []:
            for k, v in u_inv.items():
                if k not in _M_ANIM:
                    carried += v
        # harvests still to come today (rough: 3 units per remaining HARVEST)
        more = 0
        for r in getattr(self, "routes", []):
            q = self.queues.get(r.unit) or []
            ks = set(k for _, k in q if k >= 0)
            for k in ks:
                if k < len(r.nodes):
                    more += r.nodes[k].units
        total = sum(v for k, v in shed.items() if k not in _M_ANIM)
        sell = {}
        for item in _M_PRODUCTS:
            q = shed.get(item, 0) - keep.get(item, 0)
            if q <= 0:
                continue
            p0 = _m_price(item, inv[item])
            base = _M_MKT[item][0]
            if item == "FERTILIZER":
                floor = MOON_P["fert_floor"]
            elif final or day >= 28:
                floor = 1
            else:
                floor = max(1, min(p0 * MOON_P["sell_drop"], base * 0.35))
            n = 0; iv = inv[item]
            while n < q and _m_price(item, iv) >= floor:
                n += 1; iv += 1
            if n > 0:
                sell[item] = n
        # capacity: everything in the shed plus what units bring home tonight must fit
        over = total - sum(sell.values()) + carried + (more if hour < 22 else 0) - MOON_P["shed_target"]
        if over > 0:
            cands = []
            for item in _M_PRODUCTS:
                left = shed.get(item, 0) - sell.get(item, 0)
                hard = 0 if item not in keep else min(keep[item], herd if item == "WHEAT" else 2)
                for k in range(max(0, left - hard)):
                    iv = inv[item] + sell.get(item, 0) + k
                    cands.append((_m_price(item, iv) / _M_MKT[item][0], item))
            cands.sort()
            for _, item in cands[:over]:
                sell[item] = sell.get(item, 0) + 1
        out = [["SELL", it, n] for it, n in sell.items() if n > 0]
        return out[:slots]


_MOON = Moon()
_MOON_BASE_AGENT = globals().pop("agent")
globals().pop("kaggle_submission_agent", None)


def agent(obs, config=None):
    if obs["step"] < MOON_START:
        return _MOON_BASE_AGENT(obs, config)
    try:
        return _MOON.act(obs)
    except Exception:
        _M_REPORT["errors"] += 1
        return {"farmer": ["PASS"], "hands": [], "market": []}


agent.telemetry = _M_REPORT
agent = globals().pop("agent")
globals().pop("kaggle_submission_agent", None)
kaggle_submission_agent = agent
