"""Kaggriculture agent.

Single-file, standard-library only.  The last callable in this file is `agent`.

Design
------
* Exact re-implementation of the environment's price curves, so every sale /
  investment is priced rather than guessed.
* Per-tile "job" generation (what does this tile need *today* and what is it worth).
* Zone-based dispatch of the farmer + hired hands, with shed logistics
  (pickup of feed / animals / fertilizer, delivery of produce).
* Strategy layer: opening book + valuation of tile uses against the projected
  shared market (town demand, my pipeline, the opponent's visible pipeline).
* Everything is wrapped so that an unexpected error can never forfeit a match.
"""
import math

# ----------------------------------------------------------------------------
# Game constants (mirrors kaggle_environments/envs/kaggriculture/kaggriculture.py)
# ----------------------------------------------------------------------------
CROPS = {
    "WHEAT":      {"seed": 10,  "fyd": 2,  "myd": 4,  "interval": 0, "max": 6, "ongoing": False},
    "CARROT":     {"seed": 20,  "fyd": 2,  "myd": 3,  "interval": 0, "max": 4, "ongoing": False},
    "TOMATO":     {"seed": 50,  "fyd": 8,  "myd": 8,  "interval": 1, "max": 4, "ongoing": True},
    "STRAWBERRY": {"seed": 100, "fyd": 10, "myd": 10, "interval": 2, "max": 4, "ongoing": True},
    "MELON":      {"seed": 80,  "fyd": 10, "myd": 12, "interval": 0, "max": 6, "ongoing": False},
}
ANIMALS = {
    "GOOSE": {"cost": 300, "structure": "COOP",    "fyd": 4, "interval": 1, "held": 4, "product": "EGG"},
    "COW":   {"cost": 400, "structure": "PASTURE", "fyd": 8, "interval": 2, "held": 6, "product": "MILK"},
    "SHEEP": {"cost": 500, "structure": "PASTURE", "fyd": 6, "interval": 3, "held": 6, "product": "WOOL"},
}
PRODUCT_ANIMAL = {"EGG": "GOOSE", "MILK": "COW", "WOOL": "SHEEP"}
PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]
MARKET_PARAMS = {
    "WHEAT":      {"base": 25,  "I0": 10000, "T": 400, "below_func": "sqrt",   "below_target": 0.80, "above_func": "log",    "above_target": 0.20},
    "CARROT":     {"base": 35,  "I0": 10000, "T": 450, "below_func": "hinge",  "below_target": 1.00, "above_func": "sqrt",   "above_target": 0.70},
    "TOMATO":     {"base": 60,  "I0": 10000, "T": 200, "below_func": "hinge",  "below_target": 0.40, "above_func": "sqrt",   "above_target": 0.60},
    "STRAWBERRY": {"base": 120, "I0": 10000, "T": 100, "below_func": "sqrt",   "below_target": 0.70, "above_func": "linear", "above_target": 1.60},
    "MELON":      {"base": 250, "I0": 10000, "T": 300, "below_func": "log",    "below_target": 0.20, "above_func": "sq",     "above_target": 3.60},
    "EGG":        {"base": 50,  "I0": 10000, "T": 332, "below_func": "hinge",  "below_target": 0.40, "above_func": "log",    "above_target": 0.20},
    "MILK":       {"base": 160, "I0": 10000, "T": 122, "below_func": "sqrt",   "below_target": 0.60, "above_func": "linear", "above_target": 1.60},
    "WOOL":       {"base": 200, "I0": 10000, "T": 105, "below_func": "log",    "below_target": 0.20, "above_func": "sq",     "above_target": 3.20},
    "FERTILIZER": {"base": 100, "I0": 10000, "T": 200, "below_func": "linear", "below_target": 0.40, "above_func": "linear", "above_target": 0.40},
}
SHOPS = {
    "BAKERY":         ["EGG", "WHEAT"],
    "PIZZA_SHOP":     ["MILK", "TOMATO", "WHEAT"],
    "BRUNCH_SPOT":    ["EGG", "WHEAT", "STRAWBERRY"],
    "YARN_STORE":     ["WOOL"],
    "ICE_CREAM_SHOP": ["STRAWBERRY", "MILK", "WHEAT"],
    "PET_CAFE":       ["CARROT"],
    "SMOOTHIE_SHOP":  ["STRAWBERRY", "MILK"],
    "FARMERS_MARKET": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"],
}
LAND_PRICES = [1000, 2000, 4000]
MAX_SHOPS = 8
HINGE_GAIN = 8.0
MOVES = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)}

# ----------------------------------------------------------------------------
# Tunables
# ----------------------------------------------------------------------------
PARAMS = {
    "melon0": 12,            # melon tiles planted on day 0
    "goose0": 3,             # animals bought on day 0 (opening book)
    "cow0": 1,
    "sheep0": 1,
    "use_valuation_day0": False,
    "max_hand_cost": 233,    # never pay more than this for the marginal hand
    "turn_value": 5.0,       # $ shadow price of one unit-turn
    "zone_pen": 4.0,
    "animal_reserve": 120,   # cash kept back when buying animals
    "land_reserve": 200,
    "care": True,
    "disc": 1.0,             # per-day discount of future cash while capital is scarce
    "disc_until": 8,
    "hold_from_day": 12,     # before this day premium goods are sold at once (cash is king)
    "hold_cap": 45,          # max units of one premium product held back in the shed
    "min_v": 4.0,            # minimum $/tile/day for an investment to be made
    "land0": 1,              # buy the NE quadrant on day 0
    "exp_shop_w": 0.5,       # weight of demand from shops that have not unlocked yet
    "roi_hurdle": 0.8,       # cash-bound: an investment must return this multiple of its cost (net)
    "land_bonus": 4.0,       # $/tile/day added to the filler value when pricing new land
}

# ----------------------------------------------------------------------------
# Price model
# ----------------------------------------------------------------------------
def _shape(func, x, T):
    if x < 0.0:
        x = 0.0
    if func == "linear":
        return x
    if func == "sq":
        return x * x
    if func == "sqrt":
        return math.sqrt(x)
    if func == "log":
        return math.log(1.0 + x)
    if func == "log10":
        return math.log10(1.0 + x)
    if func == "hinge":
        if not T or T <= 0:
            return x
        u = x / T
        e = u - 1.0
        return u + HINGE_GAIN * (e * e if e > 0 else 0.0)
    return x


def price_at(item, inv, params):
    p = params[item]
    base, I0, T = p["base"], p["I0"], p["T"]
    if inv < I0:
        f = p["below_func"]
        amp = p["below_target"] * base / _shape(f, T, T)
        pr = base + amp * _shape(f, I0 - inv, T)
    else:
        f = p["above_func"]
        amp = p["above_target"] * base / _shape(f, T, T)
        pr = base - amp * _shape(f, inv - I0, T)
    return max(1, int(round(pr)))


def sell_revenue(item, inv, n, params):
    """Revenue from selling n units alone, starting at market inventory inv."""
    rev = 0
    for _ in range(int(n)):
        pr = price_at(item, inv, params)
        rev += pr
        if pr > 1:
            inv += 1
    return rev


def buy_cost(item, inv, n, params):
    cost = 0
    for _ in range(int(n)):
        cost += price_at(item, inv - 1, params)
        inv -= 1
    return cost


def _fib(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


# ----------------------------------------------------------------------------
# Per-episode memory
# ----------------------------------------------------------------------------
_MEM = {}


def _memory(player, step):
    m = _MEM.get(player)
    if m is None or step == 0 or step < m.get("last_step", -1):
        m = {"plan": {}, "zone": {}, "zone_key": None, "targets": {}, "log": []}
        _MEM[player] = m
    m["last_step"] = step
    return m


# ----------------------------------------------------------------------------
# State
# ----------------------------------------------------------------------------
class State(object):
    pass


def _cfg(config, key, default):
    try:
        if config is None:
            return default
        if isinstance(config, dict):
            v = config.get(key, default)
        else:
            v = getattr(config, key, default)
        return default if v is None else v
    except Exception:
        return default


def parse(obs, config):
    S = State()
    S.player = int(obs["player"])
    S.B = int(_cfg(config, "boardSize", 10))
    S.half = S.B // 2
    S.tpd = max(1, int(_cfg(config, "turnsPerDay", 24)))
    S.total_steps = int(_cfg(config, "episodeSteps", 720))
    S.shed_cap = int(_cfg(config, "shedCapacity", 100))
    S.max_orders = max(1, int(_cfg(config, "maxMarketOrdersPerTurn", 10)))
    S.hire_mult = int(_cfg(config, "farmHandCostMult", 1))
    S.shop_interval = max(1, int(_cfg(config, "townShopUnlockInterval", 3)))
    S.shop_sell_interval = max(1, int(_cfg(config, "townShopSellInterval", 4)))
    S.center_interval = max(1, int(_cfg(config, "townCenterSellInterval", 24)))

    params = {k: dict(v) for k, v in MARKET_PARAMS.items()}
    ov = _cfg(config, "marketParams", None)
    if isinstance(ov, dict):
        for item, patch in ov.items():
            if item in params and isinstance(patch, dict):
                params[item].update(patch)
    S.params = params

    day = obs.get("day", None)
    hour = obs.get("hour", None)
    step = obs.get("step", None)
    if step is None:
        step = (day or 0) * S.tpd + (hour or 0)
    S.step = int(step)
    S.day = int(day) if day is not None else S.step // S.tpd
    S.hour = int(hour) if hour is not None else S.step % S.tpd
    # The last step on which submitted actions are processed is total_steps - 2.
    S.last_act_step = S.total_steps - 2
    S.n_days = (S.total_steps + S.tpd - 1) // S.tpd
    S.last_day = S.n_days - 1
    S.turns_left_today = S.tpd - S.hour              # including this turn
    S.steps_left = S.last_act_step - S.step + 1      # actions still to be processed, incl. this one

    farms = obs["farms"]
    S.me = farms[S.player]
    S.opp = farms[1 - S.player] if len(farms) > 1 else None
    S.money = float(S.me["money"])
    S.tiles = S.me["tiles"]
    S.unlocked = list(S.me.get("unlocked_quadrants", ["NW"]))
    S.hires_today = int(S.me.get("hires_today", 0))

    priv = obs.get("private", {}) or {}
    S.shed = {k: int(v) for k, v in (priv.get("shed", {}) or {}).items() if v}
    S.seeds = {k: int(v) for k, v in (priv.get("seeds", {}) or {}).items() if v}
    invs = priv.get("inventories", [{}]) or [{}]

    units = []
    pos = [list(S.me["farmer"])] + [list(p) for p in S.me.get("hands", [])]
    for i, p in enumerate(pos):
        inv = dict(invs[i]) if i < len(invs) and invs[i] else {}
        units.append({"idx": i, "x": int(p[0]), "y": int(p[1]), "inv": inv})
    S.units = units

    market = obs.get("market", {}) or {}
    S.minv = dict(market.get("inventory", {}) or {})
    for it in PRODUCTS:
        S.minv.setdefault(it, params[it]["I0"])
    S.price = {it: price_at(it, S.minv[it], params) for it in PRODUCTS}
    S.shops = list((obs.get("town", {}) or {}).get("unlocked_shops", []) or [])

    h = S.half
    S.shed_tiles = [(h - 1, h - 1), (h, h - 1), (h - 1, h), (h, h)]
    S.shed_set = set(S.shed_tiles)
    return S


def shed_dist(S, x, y):
    return min(abs(x - sx) + abs(y - sy) for sx, sy in S.shed_tiles)


def nearest_shed_tile(S, x, y):
    return min(S.shed_tiles, key=lambda t: (abs(x - t[0]) + abs(y - t[1]), t[1], t[0]))


def town_rate(S, item, shops=None):
    """Units of `item` the town removes from the market per day."""
    shops = S.shops if shops is None else shops
    per_day_ticks = S.tpd / float(S.shop_sell_interval)
    r = 0.0
    for s in shops:
        prods = SHOPS.get(s, [])
        if item in prods:
            r += (2 if len(prods) == 1 else 1) * per_day_ticks
    if item != "FERTILIZER":
        r += S.tpd / float(S.center_interval)
    return r


def expected_future_shop_rate(item, S):
    """Expected per-day demand contributed by ONE yet-to-unlock random shop."""
    per_day_ticks = S.tpd / float(S.shop_sell_interval)
    tot = 0.0
    for s, prods in SHOPS.items():
        if item in prods:
            tot += (2 if len(prods) == 1 else 1) * per_day_ticks
    return tot / len(SHOPS)


# ----------------------------------------------------------------------------
# Tile classification helpers
# ----------------------------------------------------------------------------
def is_plant(t):
    return isinstance(t, dict) and t.get("kind") == "PLANT"


def is_animal(t):
    return isinstance(t, dict) and "animal" in t and t.get("animal")


def is_structure(t):
    return isinstance(t, dict) and t.get("kind") in ("COOP", "PASTURE")


def is_weed(t):
    return isinstance(t, dict) and t.get("kind") == "WEED"


def all_tiles(S):
    for y in range(S.B):
        row = S.tiles[y]
        for x in range(S.B):
            yield x, y, row[x]


def ongoing_schedule(crop, planted_day):
    """Days D at whose END the ongoing crop produces (harvestable on D+1)."""
    cd = CROPS[crop]
    first = planted_day + cd["fyd"] - 1
    return [first + k * cd["interval"] for k in range(cd["max"])]


def animal_prod_tonight(animal, placed_day, day):
    a = ANIMALS[animal]
    k = day + 1 - placed_day - a["fyd"]
    return k >= 0 and k % a["interval"] == 0


def animal_next_prod_after(animal, placed_day, day):
    """First day D' > day at whose end the animal produces."""
    a = ANIMALS[animal]
    d = day + 1
    first = placed_day + a["fyd"] - 1
    if d <= first:
        return first
    k = d - first
    r = k % a["interval"]
    return d if r == 0 else d + (a["interval"] - r)


# ----------------------------------------------------------------------------
# Jobs: what does each tile need right now, and what is it worth?
# ----------------------------------------------------------------------------
def J(op, value, need=None, crit=False):
    return {"op": op, "value": float(value), "need": need, "crit": crit}


def plant_jobs(S, M, t):
    crop = t["crop"]
    cd = CROPS[crop]
    age = S.day - t["planted_day"]
    yu = int(t.get("yield_units", 0))
    watered = bool(t.get("watered_today"))
    cu = int(t.get("consecutive_unwatered", 0))
    fert_active = int(t.get("fertilized_until_day", -1)) >= S.day
    price = S.price[crop]
    final_day = S.day >= S.last_day
    jobs = []
    if not cd["ongoing"]:
        ws = (cd["myd"] + 1) // 2
        in_win = ws <= age <= cd["myd"]
        gain = 0
        if (not watered) and in_win and yu < cd["max"]:
            gain = min(cd["max"] - yu, 2 if fert_active else 1)
        harvestable = age >= cd["fyd"]
        mls = int(t.get("max_lifespan_step", -1))
        decaying = mls >= 0 and S.step >= mls
        days_left = S.last_day - S.day
        want_fert = M.get("fert_use", {}).get(crop, False) and not fert_active and not watered
        fert_job = None
        if want_fert and not final_day:
            if crop == "WHEAT" and in_win and age <= cd["myd"] - 1 and yu < cd["max"] - 2:
                fert_job = J(["FERTILIZE"], 2.0 * price, need=("item", "FERTILIZER"))
            elif crop == "MELON" and 6 <= age <= 9 and yu < cd["max"] - (10 - age):
                fert_job = J(["FERTILIZE"], price, need=("item", "FERTILIZER"))
        # can the plant still grow on a later day?
        can_gain_later = (age < cd["myd"]) and (yu + gain < cd["max"]) and days_left > 0
        if can_gain_later and crop == "WHEAT" and fert_active and harvestable:
            # a fertilized field is better restarted than kept for a last +1
            nxt_fert = int(t.get("fertilized_until_day", -1)) >= S.day + 1
            g_next = min(cd["max"] - (yu + gain), 2 if nxt_fert else 1)
            if g_next < 1.4 and days_left >= 4:
                can_gain_later = False
        harvest_now = harvestable and (not can_gain_later or decaying or final_day)
        if fert_job is not None and not harvest_now:
            jobs.append(fert_job)
        if harvest_now:
            if gain > 0 and not decaying:
                jobs.append(J(["WATER"], gain * price))
            jobs.append(J(["HARVEST"], max(1, yu + gain) * price, crit=final_day or decaying))
            return jobs
        # not harvesting today: water for growth / survival
        reach_age = age + days_left
        if reach_age < cd["fyd"]:
            return jobs  # can never be harvested; abandon
        if not watered:
            if cu >= 1:
                future_units = min(cd["max"], 4 if crop == "WHEAT" else (3 if crop == "CARROT" else 6))
                jobs.append(J(["WATER"], max(gain, 1) * price + 0.5 * future_units * price, crit=True))
            elif gain > 0:
                jobs.append(J(["WATER"], gain * price))
        return jobs

    # ---- ongoing crops
    sched = ongoing_schedule(crop, t["planted_day"])
    last_prod = sched[-1]
    done = S.day > last_prod
    remaining = [d for d in sched if d >= S.day and d <= S.last_day - 1]
    prod_today = S.day in sched
    if yu > 0:
        if done or yu >= 2 or final_day or not remaining:
            jobs.append(J(["HARVEST"], yu * price, crit=final_day or done))
    if done or not remaining:
        if yu == 0 and not final_day and (S.last_day - S.day) >= 3:
            jobs.append(J(["DIG"], 20.0))
        return jobs
    want_fert = M.get("fert_use", {}).get(crop, False)
    if want_fert and not fert_active:
        covered = [d for d in remaining if S.day <= d <= S.day + 2]
        if covered and (prod_today or cu >= 1):
            jobs.append(J(["FERTILIZE"], len(covered) * price, need=("item", "FERTILIZER")))
            fert_soon = True
        else:
            fert_soon = False
    else:
        fert_soon = False
    if not watered:
        if cu >= 1:
            jobs.append(J(["WATER"], len(remaining) * price * 0.7, crit=True))
        elif prod_today and (fert_active or fert_soon):
            jobs.append(J(["WATER"], price))
    return jobs


def animal_jobs(S, M, t):
    an = t["animal"]
    a = ANIMALS[an]
    prod = a["product"]
    price = S.price[prod]
    pd = int(t.get("placed_day", 0))
    fed = bool(t.get("fed_today"))
    cared = bool(t.get("cared_today"))
    cuf = int(t.get("consecutive_unfed", 0))
    yu = int(t.get("yield_units", 0))
    pending = int(t.get("pending_care_bonus", 0) or 0)
    final_day = S.day >= S.last_day
    last_useful = S.last_day - 1      # production at the end of this day can still be sold
    tonight = animal_prod_tonight(an, pd, S.day) and S.day <= last_useful
    nxt = animal_next_prod_after(an, pd, S.day)
    future_after_today = nxt <= last_useful
    any_future = tonight or future_after_today
    jobs = []
    care_on = M.get("care", {}).get(an, True)
    # CARE today is paid out at the first production strictly after today (if fed then).
    room = a["held"] - 1 - pending
    want_care = care_on and (not cared) and future_after_today and room > 0 and not final_day
    if not fed and any_future and not final_day:
        need = False
        val = 0.0
        if cuf >= 1:
            need = True
            val += 3.0 * price
        if want_care or (cared and future_after_today):
            need = True
            val += price
        if tonight and pending > 0:
            need = True
            val += pending * price
        if need:
            jobs.append(J(["FEED"], val, need=("item", "WHEAT"), crit=cuf >= 1))
    if want_care:
        jobs.append(J(["CARE"], price))
    if yu > 0:
        visit_anyway = len(jobs) > 0
        per = 1 + (a["interval"] if care_on else 0)
        near_cap = yu + per > a["held"]
        if visit_anyway or near_cap or final_day or yu >= 2:
            jobs.append(J(["HARVEST"], yu * price, crit=final_day))
    if t.get("fertilizer_available") and M.get("collect_fert", True):
        fv = M.get("fert_value", S.price["FERTILIZER"])
        if fv >= 3 and (jobs or fv >= 12):
            jobs.append(J(["COLLECT_FERTILIZER"], fv))
    return jobs


def build_jobs(S, M):
    """tile -> ordered list of jobs."""
    jobs = {}
    plan = M["plan"]
    final_day = S.day >= S.last_day
    days_left = S.last_day - S.day
    for x, y, t in all_tiles(S):
        if t == "LOCKED":
            continue
        key = (x, y)
        lst = []
        if t is None:
            des = plan.get(key)
            if des in CROPS:
                cd = CROPS[des]
                if days_left >= cd["fyd"] and not final_day:
                    val = 0.5 * S.price[des] * (4 if des == "WHEAT" else 3 if des == "CARROT" else cd["max"])
                    lst.append(J(["PLANT", des], val, need=("seed", des)))
                    lst.append(J(["WATER"], val, crit=True))
            elif des in ANIMALS:
                a = ANIMALS[des]
                lst.append(J(["BUILD_" + a["structure"]], 60.0, need=("item", des)))
                lst.append(J(["PLACE", des], 120.0, need=("item", des)))
                if M.get("care", {}).get(des, True) and days_left > a["fyd"]:
                    lst.append(J(["FEED"], S.price[a["product"]], need=("item", "WHEAT")))
                    lst.append(J(["CARE"], S.price[a["product"]]))
        elif is_weed(t):
            if days_left >= 3:
                lst.append(J(["DIG"], 15.0))
        elif is_plant(t):
            if plan.get(key) == "DIG":
                lst.append(J(["DIG"], 30.0))
            else:
                lst = plant_jobs(S, M, t)
        elif is_animal(t):
            lst = animal_jobs(S, M, t)
        elif is_structure(t):
            des = plan.get(key)
            if des in ANIMALS and ANIMALS[des]["structure"] == t.get("kind"):
                a = ANIMALS[des]
                lst.append(J(["PLACE", des], 120.0, need=("item", des)))
                if M.get("care", {}).get(des, True) and days_left > a["fyd"]:
                    lst.append(J(["FEED"], S.price[a["product"]], need=("item", "WHEAT")))
                    lst.append(J(["CARE"], S.price[a["product"]]))
            elif days_left >= 3:
                lst.append(J(["DIG"], 10.0))
        if lst:
            jobs[key] = lst
    return jobs


# ----------------------------------------------------------------------------
# Farm census helpers
# ----------------------------------------------------------------------------
def count_farm(S, M):
    c = {"empty": 0, "weed": 0, "unlocked": 0}
    for k in list(CROPS) + list(ANIMALS):
        c[k] = 0
    for x, y, t in all_tiles(S):
        if t == "LOCKED":
            continue
        c["unlocked"] += 1
        if t is None:
            c["empty"] += 1
        elif is_weed(t):
            c["weed"] += 1
        elif is_plant(t):
            c[t["crop"]] += 1
        elif is_animal(t):
            c[t["animal"]] += 1
    return c


def pending_animal_tiles(S, M):
    """Animal-designated tiles that do not yet hold an animal."""
    out = {a: 0 for a in ANIMALS}
    for (x, y), des in M["plan"].items():
        if des in ANIMALS:
            t = S.tiles[y][x]
            if t != "LOCKED" and not is_animal(t):
                out[des] += 1
    return out


def animals_in_hand(S):
    out = {a: S.shed.get(a, 0) for a in ANIMALS}
    for u in S.units:
        for a in ANIMALS:
            out[a] += u["inv"].get(a, 0)
    return out


# ----------------------------------------------------------------------------
# Market projection + valuation of tile uses
# ----------------------------------------------------------------------------
def approx_revenue(item, inv, n, params):
    """Fast estimate of selling n units starting at inventory inv (midpoint sampling)."""
    if n <= 0:
        return 0.0
    k = 1 if n <= 1 else (3 if n <= 6 else 6)
    tot = 0.0
    for j in range(k):
        tot += price_at(item, inv + (j + 0.5) * n / k, params)
    return tot * n / k


def animal_schedule(an, placed_day, day, last_day, care, pending):
    """sale_day -> units, for productions at the end of days >= `day`."""
    a = ANIMALS[an]
    out = {}
    pend = pending
    for D in range(day, last_day):
        k = D + 1 - placed_day - a["fyd"]
        if k >= 0 and k % a["interval"] == 0:
            out[D + 1] = out.get(D + 1, 0) + min(a["held"], 1 + pend)
            pend = 0
        if care:
            pend += 1
    return out


CROP_TARGET = {"WHEAT": (4, 4), "CARROT": (3, 3), "MELON": (10, 6)}   # (harvest age, units)


def plant_schedule(t, day, last_day, fert):
    crop = t["crop"]
    cd = CROPS[crop]
    out = {}
    pd = int(t.get("planted_day", day))
    if not cd["ongoing"]:
        age_h, units = CROP_TARGET[crop]
        hd = pd + age_h
        if hd > last_day:
            units = max(1, units - (hd - last_day))
            hd = last_day
        if pd + cd["fyd"] > last_day:
            return out
        hd = max(hd, day)
        out[hd] = units
        return out
    per = 2 if fert else 1
    for D in ongoing_schedule(crop, pd):
        if D >= day and D + 1 <= last_day:
            out[D + 1] = out.get(D + 1, 0) + per
    return out


def farm_pipeline(S, farm, mine, M):
    """item -> [units sold on day D] for D in 0..n_days, from what is visible on a farm."""
    nd = S.n_days + 1
    pipe = {it: [0.0] * nd for it in PRODUCTS}
    n_animals = 0
    if farm is None:
        return pipe, 0
    for row in farm["tiles"]:
        for t in row:
            if not isinstance(t, dict):
                continue
            if t.get("kind") == "PLANT":
                crop = t["crop"]
                if mine:
                    fert = M.get("fert_use", {}).get(crop, False)
                else:
                    fert = int(t.get("fertilized_until_day", -1)) >= S.day
                sch = plant_schedule(t, S.day, S.last_day, fert)
                for D, u in sch.items():
                    pipe[crop][D] += u
                yu = int(t.get("yield_units", 0))
                if CROPS[crop]["ongoing"] and yu > 0:
                    pipe[crop][S.day] += yu
            elif t.get("animal"):
                an = t["animal"]
                n_animals += 1
                pend = int(t.get("pending_care_bonus", 0) or 0)
                if mine:
                    care = M.get("care", {}).get(an, True)
                else:
                    care = pend > 0 or bool(t.get("cared_today"))
                sch = animal_schedule(an, int(t.get("placed_day", 0)), S.day, S.last_day, care, pend)
                prod = ANIMALS[an]["product"]
                for D, u in sch.items():
                    pipe[prod][D] += u
                yu = int(t.get("yield_units", 0))
                if yu > 0:
                    pipe[prod][S.day] += yu
    return pipe, n_animals


def future_shop_days(S):
    """Days on which a new (random) shop will still unlock."""
    out = []
    n = len(S.shops)
    d = (S.day // S.shop_interval + 1) * S.shop_interval
    while n < MAX_SHOPS and d <= S.last_day:
        out.append(d)
        n += 1
        d += S.shop_interval
    return out


def build_context(S, M):
    ctx = {}
    pipe_me, n_me = farm_pipeline(S, S.me, True, M)
    pipe_opp, n_opp = farm_pipeline(S, S.opp, False, M)
    ctx["pipe_me"], ctx["pipe_opp"] = pipe_me, pipe_opp
    ctx["n_animals_me"], ctx["n_animals_opp"] = n_me, n_opp
    fdays = future_shop_days(S)
    base = {}
    for it in PRODUCTS:
        known = town_rate(S, it)
        exp1 = expected_future_shop_rate(it, S) if it != "FERTILIZER" else 0.0
        path = [0.0] * (S.n_days + 2)
        inv = float(S.minv[it])
        # remaining fraction of today
        frac_today = S.turns_left_today / float(S.tpd)
        for D in range(S.day, S.last_day + 1):
            path[D] = inv
            rate = known + PARAMS["exp_shop_w"] * exp1 * sum(1 for fd in fdays if fd <= D)
            f = frac_today if D == S.day else 1.0
            inv = inv - rate * f + pipe_opp[it][D] * (f if D == S.day else 1.0)
        base[it] = path
    # fertilizer: both farms' animals keep adding supply
    fpath = [0.0] * (S.n_days + 2)
    inv = float(S.minv["FERTILIZER"])
    sell_frac = M.get("fert_sell_frac", 1.0)
    for D in range(S.day, S.last_day + 1):
        fpath[D] = inv
        inv += n_opp * 0.8 + n_me * sell_frac
    base["FERTILIZER"] = fpath
    ctx["base"] = base
    # wheat balance -> effective wheat price
    wheat_tiles = sum(1 for _, _, t in all_tiles(S) if is_plant(t) and t["crop"] == "WHEAT")
    per_tile = 1.4 if M.get("fert_use", {}).get("WHEAT") else 1.0
    net = wheat_tiles * per_tile - n_me
    ctx["wheat_net"] = net
    horizon = max(1, min(8, S.last_day - S.day))
    ctx["pw"] = float(price_at("WHEAT", S.minv["WHEAT"] + net * horizon * 0.5, S.params))
    ctx["added"] = {it: [0.0] * (S.n_days + 2) for it in PRODUCTS}
    return ctx


def my_revenue(S, ctx, item, extra=None):
    """Revenue of my whole pipeline for `item` (+ optional extra schedule), selling on production."""
    base = ctx["base"][item]
    mine = ctx["pipe_me"][item]
    add = ctx["added"][item]
    cum = 0.0
    rev = 0.0
    P = PARAMS
    for D in range(S.day, S.last_day + 1):
        u = mine[D] + add[D] + (extra.get(D, 0) if extra else 0)
        if u > 0:
            r = approx_revenue(item, base[D] + cum, u, S.params)
            if P["disc"] < 1.0 and S.day < P["disc_until"]:
                r *= P["disc"] ** min(D - S.day, P["disc_until"] - S.day)
            rev += r
            cum += u
    return rev


def marginal_revenue(S, ctx, item, sched):
    if not sched:
        return 0.0
    return my_revenue(S, ctx, item, sched) - my_revenue(S, ctx, item, None)


def fert_value_on(S, ctx, D):
    base = ctx["base"]["FERTILIZER"]
    pr = price_at("FERTILIZER", base[min(D, S.last_day)], S.params)
    use = 2.0 * ctx["pw"] - 8.0          # +2 wheat for one fertilizer and one action
    return max(float(pr), use if D < S.last_day - 3 else 0.0)


def evaluate_uses(S, M, ctx, fillers_only=False):
    """Rows: dict(use, v [$ per tile-day], npv, cost, life, item, sched)."""
    P = PARAMS
    tau = P["turn_value"]
    R = S.last_day - S.day
    out = []
    pw = ctx["pw"]
    if R <= 0:
        return out

    def row(use, npv, cost, life, item, sched):
        out.append({"use": use, "v": npv / float(max(1, life)), "npv": npv, "cost": cost,
                    "life": life, "item": item, "sched": sched})

    # ---- filler crops (short cycle; re-decided at every harvest)
    for crop, labor in (("WHEAT", 2.5), ("CARROT", 2.7)):
        cd = CROPS[crop]
        age_h, units = CROP_TARGET[crop]
        if R < cd["fyd"]:
            continue
        life = age_h
        if R < age_h:
            units = max(1, units - (age_h - R))
            life = R
        sched = {S.day + life: units}
        if crop == "WHEAT":
            u_eff = units + (2 if (M.get("fert_use", {}).get("WHEAT") and R >= 4) else 0)
            rev = u_eff * pw
        else:
            rev = marginal_revenue(S, ctx, crop, sched)
        row(crop, rev - cd["seed"] - labor * tau * life, cd["seed"], life, crop, sched)
    if fillers_only:
        return out
    # ---- melon
    cd = CROPS["MELON"]
    if R >= 10:
        sched = {S.day + 10: 6}
        rev = marginal_revenue(S, ctx, "MELON", sched)
        row("MELON", rev - cd["seed"] - 18 * tau, cd["seed"], 10, "MELON", sched)
    # ---- ongoing crops
    for crop in ("STRAWBERRY", "TOMATO"):
        cd = CROPS[crop]
        fert = M.get("fert_use", {}).get(crop, False)
        sched = {}
        for D in ongoing_schedule(crop, S.day):
            if D + 1 <= S.last_day:
                sched[D + 1] = (2 if fert else 1)
        if len(sched) < 2:
            continue
        life = max(sched) - S.day
        rev = marginal_revenue(S, ctx, crop, sched)
        labor = (life * 0.6 + 6) * tau
        fert_cost = 2 * fert_value_on(S, ctx, min(S.last_day, S.day + cd["fyd"])) if fert else 0.0
        row(crop, rev - cd["seed"] - labor - fert_cost, cd["seed"], life, crop, sched)
    # ---- animals
    for an in ("SHEEP", "COW", "GOOSE"):
        a = ANIMALS[an]
        sched = animal_schedule(an, S.day, S.day, S.last_day, True, 0)
        if not sched:
            continue
        prod = a["product"]
        rev = marginal_revenue(S, ctx, prod, sched)
        fert_rev = 0.0
        for D in range(S.day + 1, S.last_day + 1):
            fv = fert_value_on(S, ctx, D) - tau
            if fv > 0:
                if P["disc"] < 1.0 and S.day < P["disc_until"]:
                    fv *= P["disc"] ** min(D - S.day, P["disc_until"] - S.day)
                fert_rev += fv
        feed_days = max(0, max(sched) - S.day)
        npv = rev + fert_rev - a["cost"] - feed_days * pw - feed_days * 3.5 * tau
        row(an, npv, a["cost"], R, prod, sched)
    return out


def add_to_pipeline(S, ctx, use):
    if use in ANIMALS:
        for D, u in animal_schedule(use, S.day, S.day, S.last_day, True, 0).items():
            ctx["added"][ANIMALS[use]["product"]][D] += u
    elif use in CROPS and use != "WHEAT":
        if CROPS[use]["ongoing"]:
            for D in ongoing_schedule(use, S.day):
                if D + 1 <= S.last_day:
                    ctx["added"][use][D + 1] += 1
        else:
            age_h, units = CROP_TARGET[use]
            if S.day + age_h <= S.last_day:
                ctx["added"][use][S.day + age_h] += units


def plan_tiles(S, M, ctx, budget, seed_budget):
    """Decide what every empty tile should become.  Sticky within a day.
    `budget` is money for investments, `seed_budget` for cheap filler seeds."""
    P = PARAMS
    plan = M["plan"]
    pday = M.setdefault("plan_day", {})
    empties = []
    for x, y, t in all_tiles(S):
        if t == "LOCKED":
            continue
        key = (x, y)
        if t is None:
            empties.append(key)
        elif is_plant(t):
            if plan.get(key) != "DIG":
                plan[key] = t["crop"]
        elif is_animal(t):
            plan[key] = t["animal"]
        elif is_weed(t):
            plan.pop(key, None)
    empties.sort(key=lambda k: (shed_dist(S, k[0], k[1]), k[1], k[0]))
    inhand = animals_in_hand(S)
    pend = pending_animal_tiles(S, M)

    committed = 0.0
    for an in ANIMALS:
        committed += max(0, pend[an] - inhand[an]) * ANIMALS[an]["cost"]

    todo = []
    for key in empties:
        des = plan.get(key)
        fresh = pday.get(key) == S.day
        if des in ANIMALS:
            if fresh or inhand[des] > 0 or S.money >= ANIMALS[des]["cost"]:
                add_to_pipeline(S, ctx, des)
                continue
            plan.pop(key, None)
            todo.append(key)
        elif des in CROPS and fresh:
            if des != "WHEAT":
                add_to_pipeline(S, ctx, des)
            continue
        else:
            todo.append(key)
    budget -= committed

    # ---- opening book (day 0): explicit counts, the rest by valuation of fillers
    book = []
    if S.day == 0:
        counts = count_farm(S, M)
        n_mel = counts["MELON"] + sum(1 for k in empties if plan.get(k) == "MELON" and k not in todo)
        book += ["MELON"] * max(0, P["melon0"] - n_mel)
        for an, pk in (("SHEEP", "sheep0"), ("COW", "cow0"), ("GOOSE", "goose0")):
            book += [an] * max(0, P[pk] - counts[an] - pend[an])

    best_v_seen = 0.0
    bi = 0
    rows = None
    invest_open = True
    for n_done, key in enumerate(todo):
        choice = None
        while bi < len(book):
            w = book[bi]
            bi += 1
            cost = ANIMALS[w]["cost"] if w in ANIMALS else CROPS[w]["seed"]
            if cost <= budget:
                choice = (w, cost, True)
                break
        if choice is None:
            n_left = len(todo) - n_done
            if invest_open and S.day > 0:
                if rows is None:
                    rows = evaluate_uses(S, M, ctx)
                fill_v = max([r["v"] for r in rows if r["use"] in ("WHEAT", "CARROT")] + [0.0])
                cash_rich = budget >= 350.0 * n_left
                cands = []
                for r in rows:
                    if r["use"] in ("WHEAT", "CARROT"):
                        continue
                    cost = r["cost"]
                    if r["use"] in ANIMALS and inhand[r["use"]] - pend[r["use"]] > 0:
                        cost = 0
                    if cost > budget or r["npv"] <= 0 or r["v"] < max(P["min_v"], fill_v):
                        continue
                    roi = r["npv"] / float(max(1, r["cost"]))
                    if not cash_rich and roi < P["roi_hurdle"]:
                        continue
                    cands.append((r["v"] if cash_rich else roi, r["use"], cost, r["v"]))
                if cands:
                    cands.sort(reverse=True)
                    _, use, cost, v = cands[0]
                    choice = (use, cost, True)
                    best_v_seen = max(best_v_seen, v)
                else:
                    invest_open = False
            if choice is None:
                frows = evaluate_uses(S, M, ctx, fillers_only=True)
                frows = [r for r in frows if r["cost"] <= seed_budget and r["v"] > -3.0]
                if frows:
                    r = max(frows, key=lambda r: r["v"])
                    choice = (r["use"], r["cost"], False)
        if choice is None:
            plan.pop(key, None)
            continue
        use, cost, invest = choice
        plan[key] = use
        pday[key] = S.day
        if invest:
            budget -= cost
            rows = None
        else:
            seed_budget -= cost
        if use in ANIMALS:
            pend[use] += 1
        add_to_pipeline(S, ctx, use)
    M["best_v"] = best_v_seen
    return budget


# ----------------------------------------------------------------------------
# Labor: hire only while the marginal hand pays for itself
# ----------------------------------------------------------------------------
def work_bundles(S, M, jobs):
    out = []
    for key, lst in jobs.items():
        n = len(lst)
        val = sum(j["value"] for j in lst)
        t = S.tiles[key[1]][key[0]]
        if is_plant(t) and not CROPS[t["crop"]]["ongoing"] and any(j["op"][0] == "HARVEST" for j in lst):
            if S.last_day - S.day >= 2:
                n += 2
                val += 60.0
        out.append((val / (n + 1.0), n + 1.0, val))
    out.sort(reverse=True)
    return out


def decide_hires(S, M, jobs):
    P = PARAMS
    bundles = work_bundles(S, M, jobs)
    total_turns = sum(b[1] for b in bundles)
    eff_now = max(0.0, S.turns_left_today - 2.0)           # existing units
    eff_new = max(0.0, S.turns_left_today - 1.0 - 3.0)     # a new hand: arrives next turn, deploys
    if eff_new < 3:
        return 0
    cap = len(S.units) * eff_now * 0.9
    hires = 0
    money = S.money
    # walk down the value-sorted work list
    idx = 0
    acc = 0.0
    n = len(bundles)
    while idx < n and acc + bundles[idx][1] <= cap:
        acc += bundles[idx][1]
        idx += 1
    while idx < n and hires < 24:
        slice_turns = 0.0
        slice_val = 0.0
        j = idx
        while j < n and slice_turns < eff_new:
            slice_turns += bundles[j][1]
            slice_val += bundles[j][2]
            j += 1
        if slice_turns < 4:
            break
        cost = S.hire_mult * _fib(S.hires_today + hires)
        frac = min(1.0, eff_new / slice_turns)
        if cost > P["max_hand_cost"] or cost > slice_val * frac * 0.7 or cost > money - 2:
            break
        money -= cost
        hires += 1
        idx = j
    return hires


# ----------------------------------------------------------------------------
# Zones
# ----------------------------------------------------------------------------
def compute_zones(S, M, jobs, k_units):
    cx = cy = (S.B - 1) / 2.0
    items = []
    for key, lst in jobs.items():
        w = len(lst) + 1.0
        ang = math.atan2(key[1] - cy, key[0] - cx)
        items.append((ang, key, w))
    items.sort()
    total = sum(w for _, _, w in items)
    zone = {}
    if k_units <= 0 or total <= 0:
        return zone
    per = total / float(k_units)
    acc = 0.0
    z = 0
    for ang, key, w in items:
        if acc + w / 2.0 > per * (z + 1) and z < k_units - 1:
            z += 1
        zone[key] = z
        acc += w
    return zone


# ----------------------------------------------------------------------------
# Dispatch
# ----------------------------------------------------------------------------
def step_toward(ux, uy, tx, ty):
    dx, dy = tx - ux, ty - uy
    if dx == 0 and dy == 0:
        return ["PASS"]
    if abs(dx) >= abs(dy):
        return ["EAST"] if dx > 0 else ["WEST"]
    return ["SOUTH"] if dy > 0 else ["NORTH"]


def doable(i, job, seeds_left, inv_left):
    need = job["need"]
    if need is None:
        return True
    kind, name = need
    if kind == "seed":
        return seeds_left.get(name, 0) > 0
    return inv_left[i].get(name, 0) > 0


BLOCKING = ("PLANT", "BUILD_COOP", "BUILD_PASTURE", "PLACE")


def tile_offer(i, lst, seeds_left, inv_left):
    """(first doable op, total value, n actions, crit, feed_blocked) for unit i on a tile."""
    first = None
    val = 0.0
    nact = 0
    crit = False
    feed_blocked = False
    for j in lst:
        op = j["op"][0]
        if doable(i, j, seeds_left, inv_left):
            if op == "CARE" and feed_blocked:
                continue
            if first is None:
                first = j
            val += j["value"]
            nact += 1
            crit = crit or j["crit"]
        else:
            if op == "FEED":
                feed_blocked = True
                continue
            if op == "FERTILIZE":
                continue
            if op in BLOCKING:
                break
    return first, val, nact, crit, feed_blocked


def dispatch(S, M, jobs):
    P = PARAMS
    units = S.units
    n = len(units)
    actions = [["PASS"] for _ in range(n)]
    decided = [False] * n
    seeds_left = dict(S.seeds)
    inv_left = [dict(u["inv"]) for u in units]
    claimed = set()
    zone = M.get("zone", {})
    final_day = S.day >= S.last_day

    # ---- demand for shed-supplied items
    demand = {}
    zone_need = {}
    for key, lst in jobs.items():
        z = zone.get(key)
        for j in lst:
            if j["need"] and j["need"][0] == "item":
                if j["op"][0] in ("BUILD_COOP", "BUILD_PASTURE"):
                    continue
                nm = j["need"][1]
                demand[nm] = demand.get(nm, 0) + 1
                d = zone_need.setdefault(z, {})
                d[nm] = d.get(nm, 0) + 1
    carried = {}
    for u in units:
        for k, v in u["inv"].items():
            carried[k] = carried.get(k, 0) + v
    uncovered = {k: max(0, v - carried.get(k, 0)) for k, v in demand.items()}
    shed_left = dict(S.shed)
    wheat_obtainable = (shed_left.get("WHEAT", 0) + carried.get("WHEAT", 0)) > 0

    # ---- 1. pickups at the shed
    at_shed = [u for u in units if (u["x"], u["y"]) in S.shed_set]
    n_at = len(at_shed)
    for u in at_shed:
        i = u["idx"]
        best = None
        for item, unc in uncovered.items():
            if unc <= 0 or shed_left.get(item, 0) <= 0:
                continue
            zn = zone_need.get(i, {}).get(item, 0) - inv_left[i].get(item, 0)
            if zn <= 0:
                # my zone is covered; take a fair share of what nobody's zone covers
                zoned_total = sum(d.get(item, 0) for z, d in zone_need.items() if z is not None and z < len(units))
                orphan = demand.get(item, 0) - zoned_total
                if orphan <= 0 and zone_need.get(i) is not None:
                    continue
                zn = int(math.ceil(min(unc, max(orphan, 1)) / float(max(1, n_at))))
                if inv_left[i].get(item, 0) >= zn:
                    continue
            amt = int(min(shed_left[item], unc, max(1, zn), 12))
            score = amt * (3 if item in ANIMALS else 1)
            if amt > 0 and (best is None or score > best[2]):
                best = (item, amt, score)
        if best:
            item, amt, _ = best
            actions[i] = ["PICKUP", item, amt]
            decided[i] = True
            shed_left[item] -= amt
            uncovered[item] -= amt
            inv_left[i][item] = inv_left[i].get(item, 0) + amt

    # ---- 2. units standing on a tile with doable work
    for u in units:
        i = u["idx"]
        if decided[i]:
            continue
        key = (u["x"], u["y"])
        if key in jobs and key not in claimed:
            first, val, nact, crit, fb = tile_offer(i, jobs[key], seeds_left, inv_left)
            if first is not None:
                actions[i] = list(first["op"])
                decided[i] = True
                claimed.add(key)
                if first["need"] and first["need"][0] == "seed":
                    seeds_left[first["need"][1]] -= 1

    # ---- 3. who must deliver cargo now?
    def sellable_load(u):
        load = 0
        for k, v in u["inv"].items():
            if k not in PRODUCTS:
                continue
            if k == "WHEAT" and demand.get("WHEAT", 0) > 0:
                continue
            if k == "FERTILIZER" and demand.get("FERTILIZER", 0) > 0:
                continue
            load += v
        return load

    total_carried = sum(sum(v.values()) for v in inv_left)
    room = S.shed_cap - sum(S.shed.values())
    must_deliver = set()
    if final_day:
        for u in units:
            d = shed_dist(S, u["x"], u["y"])
            if sellable_load(u) > 0 and S.steps_left <= d + 3:
                must_deliver.add(u["idx"])
    else:
        if total_carried > 0.7 * room or (S.turns_left_today <= 9 and total_carried > 0.55 * room):
            excess = total_carried - 0.45 * room
            for load, i in sorted(((sellable_load(u), u["idx"]) for u in units), reverse=True):
                if excess <= 0 or load <= 0:
                    break
                must_deliver.add(i)
                excess -= load
        rush = M.get("rush_items", ())
        if rush:
            batch = M.get("rush_batch", 12)
            for u in units:
                q = sum(u["inv"].get(k, 0) for k in rush)
                if q >= batch:
                    must_deliver.add(u["idx"])

    def deliver(u):
        key = (u["x"], u["y"])
        if key in S.shed_set:
            keep = [k for k in u["inv"] if (k in ANIMALS) or
                    (k == "WHEAT" and demand.get("WHEAT", 0) > 0) or
                    (k == "FERTILIZER" and demand.get("FERTILIZER", 0) > 0)]
            if not keep:
                return ["DROP"]
            best = None
            for k, v in u["inv"].items():
                if k in keep or k not in PRODUCTS:
                    continue
                sc = v * S.price.get(k, 1)
                if best is None or sc > best[1]:
                    best = (k, sc, v)
            if best:
                return ["PLACE", best[0], int(best[2])]
            return None
        tx, ty = nearest_shed_tile(S, u["x"], u["y"])
        return step_toward(u["x"], u["y"], tx, ty)

    for u in units:
        i = u["idx"]
        if decided[i] or i not in must_deliver:
            continue
        a = deliver(u)
        if a:
            actions[i] = a
            decided[i] = True

    # ---- 4. match free units to tiles
    late = S.turns_left_today <= 8
    pairs = []
    prev_target = M.get("targets", {})
    for u in units:
        i = u["idx"]
        if decided[i]:
            continue
        for key, lst in jobs.items():
            if key in claimed:
                continue
            first, val, nact, crit, fb = tile_offer(i, lst, seeds_left, inv_left)
            if first is None:
                continue
            if fb and lst[0]["op"][0] == "FEED" and wheat_obtainable:
                continue        # leave animal tiles to somebody carrying feed
            d = abs(u["x"] - key[0]) + abs(u["y"] - key[1])
            if d + 1 > S.turns_left_today:
                continue
            cost = float(d)
            z = zone.get(key)
            if z is not None and z != i:
                cost += P["zone_pen"]
            cost -= min(6.0, val / 40.0)
            if crit and late:
                cost -= 30.0
            if prev_target.get(i) == key:
                cost -= 0.6
            pairs.append((cost, i, key))
    pairs.sort()
    taken = set()
    targets = {}
    by_idx = {u["idx"]: u for u in units}
    for cost, i, key in pairs:
        if i in taken or key in claimed:
            continue
        taken.add(i)
        claimed.add(key)
        u = by_idx[i]
        actions[i] = step_toward(u["x"], u["y"], key[0], key[1])
        decided[i] = True
        targets[i] = key
    M["targets"] = targets

    # ---- 5. idle units: fetch supplies, or bring cargo home
    for u in units:
        i = u["idx"]
        if decided[i]:
            continue
        need_supply = any(unc > 0 and shed_left.get(item, 0) > 0 for item, unc in uncovered.items())
        if need_supply and (u["x"], u["y"]) not in S.shed_set:
            tx, ty = nearest_shed_tile(S, u["x"], u["y"])
            d = abs(u["x"] - tx) + abs(u["y"] - ty)
            if d + 3 <= S.turns_left_today:
                actions[i] = step_toward(u["x"], u["y"], tx, ty)
                decided[i] = True
                continue
        if sellable_load(u) > 0:
            a = deliver(u)
            if a:
                actions[i] = a
                decided[i] = True
    return actions


# ----------------------------------------------------------------------------
# Market
# ----------------------------------------------------------------------------
PREMIUM = ("MILK", "WOOL", "STRAWBERRY", "TOMATO", "CARROT")


def n_my_animals(S, M):
    n = sum(1 for _, _, t in all_tiles(S) if is_animal(t))
    return n + sum(pending_animal_tiles(S, M).values())


def fert_jobs_soon(S, M):
    """Fertilizer wanted today + tomorrow morning (so it is not sold off)."""
    fu = M.get("fert_use", {})
    n = 0
    for _, _, t in all_tiles(S):
        if not is_plant(t):
            continue
        crop = t["crop"]
        if not fu.get(crop):
            continue
        age = S.day - t["planted_day"]
        active = int(t.get("fertilized_until_day", -1)) >= S.day + 1
        if active:
            continue
        if crop == "WHEAT" and age in (1, 2):
            n += 1
        elif crop == "MELON" and 5 <= age <= 8:
            n += 1
        elif CROPS[crop]["ongoing"]:
            sch = ongoing_schedule(crop, t["planted_day"])
            if any(S.day <= d <= S.day + 1 for d in sch):
                n += 1
    return n


def sell_orders(S, M, ctx, jobs):
    P = PARAMS
    final = S.steps_left <= 8
    feed_today = sum(1 for lst in jobs.values() for j in lst if j["op"][0] == "FEED")
    carried_wheat = sum(u["inv"].get("WHEAT", 0) for u in S.units)
    reserve = {}
    if S.day < S.last_day:
        r = max(0, feed_today - carried_wheat)
        if S.day < S.last_day - 1:
            r += n_my_animals(S, M)
        reserve["WHEAT"] = r
        reserve["FERTILIZER"] = fert_jobs_soon(S, M)
    out = []
    shed_total = sum(S.shed.values())
    for item, n in S.shed.items():
        if item not in PRODUCTS or n <= 0:
            continue
        avail = n if final else n - reserve.get(item, 0)
        if avail <= 0:
            continue
        q = avail
        if item in PREMIUM and not final and S.day >= P["hold_from_day"]:
            opp_cap = sum(ctx["pipe_opp"][item][S.day:]) > 0
            if not opp_cap:
                rate_turn = town_rate(S, item) / float(S.tpd)
                c_rem = rate_turn * S.steps_left
                for fd in future_shop_days(S):
                    c_rem += expected_future_shop_rate(item, S) * max(0, S.last_day - fd + 1)
                stock = n + sum(u["inv"].get(item, 0) for u in S.units)
                s_rem = stock + sum(ctx["pipe_me"][item][S.day + 1:])
                target_extra = s_rem - c_rem
                q = int(max(0, min(avail, target_extra)))
                q = max(q, avail - P["hold_cap"])
                if shed_total > 75:
                    q = max(q, min(avail, shed_total - 75))
        if item == "FERTILIZER" and S.price[item] < 2 and not final:
            continue
        if q > 0:
            out.append((S.price[item] * q, ["SELL", item, int(q)]))
    out.sort(key=lambda r: -r[0])
    return [o for _, o in out]


def decide_market(S, M, ctx):
    P = PARAMS
    days_left = S.last_day - S.day
    jobs0 = build_jobs(S, M)
    sells = sell_orders(S, M, ctx, jobs0)
    cash = S.money
    for o in sells:
        cash += 0.9 * approx_revenue(o[1], S.minv[o[1]], o[2], S.params)

    buys = []
    # ---- money that must never be touched by investments: feed, seeds, tomorrow's crew
    n_anim = n_my_animals(S, M)
    have_wheat = S.shed.get("WHEAT", 0) + sum(u["inv"].get("WHEAT", 0) for u in S.units)
    feed_reserve = max(0, 2 * n_anim - have_wheat) * (S.price["WHEAT"] + 2.0)
    counts = count_farm(S, M)
    n_tiles = counts["unlocked"]
    seed_reserve = 12.0 * min(n_tiles, 30) * 0.5
    crew_reserve = 60.0 if S.day > 0 else 25.0
    protected = feed_reserve + seed_reserve + crew_reserve
    if S.day == 0:
        protected = 60.0

    # ---- land, priced like any other investment
    n_extra = len(S.unlocked) - 1
    if n_extra < len(LAND_PRICES) and days_left > 4:
        lp = LAND_PRICES[n_extra]
        frows = evaluate_uses(S, M, ctx, fillers_only=True)
        fill_v = max([r["v"] for r in frows] + [0.0]) + P["turn_value"] * 2.5   # labor is elastic
        land_v = fill_v + P["land_bonus"]
        worth = 25.0 * land_v * max(0, days_left - 3)
        want = worth > 1.3 * lp and cash >= lp + protected
        if S.day == 0:
            want = bool(P["land0"]) and n_extra == 0
        if want:
            buys.append(["BUY_LAND"])
            cash -= lp

    # ---- tile plan (investment decisions)
    plan_tiles(S, M, ctx, cash - protected, max(0.0, cash - feed_reserve * 0.5))
    jobs = build_jobs(S, M)
    room = S.shed_cap - sum(S.shed.values())

    # ---- feed wheat comes first
    if S.day < S.last_day:
        feed_today = sum(1 for lst in jobs.values() for j in lst if j["op"][0] == "FEED")
        short = feed_today - have_wheat
        if short > 0 and room > 0:
            k = int(min(short, room, 80))
            while k > 0 and buy_cost("WHEAT", S.minv["WHEAT"], k, S.params) > cash:
                k -= 1
            if k > 0:
                buys.append(["BUY_PRODUCT", "WHEAT", k])
                cash -= buy_cost("WHEAT", S.minv["WHEAT"], k, S.params)
                room -= k

    # ---- animals
    pend = pending_animal_tiles(S, M)
    inhand = animals_in_hand(S)
    for an in ("SHEEP", "COW", "GOOSE"):
        k = pend[an] - inhand[an]
        if k > 0:
            k = int(min(k, cash // ANIMALS[an]["cost"], max(0, room)))
            if k > 0:
                buys.append(["BUY_ANIMAL", an, k])
                cash -= k * ANIMALS[an]["cost"]
                room -= k

    # ---- seeds (incl. replanting of what gets harvested today)
    need_seed = {}
    for (x, y), des in M["plan"].items():
        if des not in CROPS:
            continue
        t = S.tiles[y][x]
        if t is None:
            need_seed[des] = need_seed.get(des, 0) + 1
        elif is_plant(t) and not CROPS[t["crop"]]["ongoing"] and days_left >= 2:
            if any(j["op"][0] == "HARVEST" for j in jobs.get((x, y), [])):
                need_seed["WHEAT"] = need_seed.get("WHEAT", 0) + 1
    for crop, k in sorted(need_seed.items(), key=lambda kv: -CROPS[kv[0]]["seed"]):
        k -= S.seeds.get(crop, 0)
        if k > 0:
            k = int(min(k, cash // CROPS[crop]["seed"]))
            if k > 0:
                buys.append(["BUY_SEED", crop, k])
                cash -= k * CROPS[crop]["seed"]

    # ---- fertilizer for high-value uses
    fert_need = 0
    fert_val = 0.0
    for lst in jobs.values():
        for j in lst:
            if j["op"][0] == "FERTILIZE":
                fert_need += 1
                fert_val = max(fert_val, j["value"])
    have_f = S.shed.get("FERTILIZER", 0) + sum(u["inv"].get("FERTILIZER", 0) for u in S.units)
    if fert_need > have_f and room > 0:
        k = int(min(fert_need - have_f, room, 30))
        pf = price_at("FERTILIZER", S.minv["FERTILIZER"] - k, S.params)
        if fert_val > pf * 1.3 + 10 and pf * k <= cash:
            buys.append(["BUY_PRODUCT", "FERTILIZER", k])
            cash -= pf * k

    # ---- hires
    n_hire = decide_hires(S, M, jobs)
    M["planned_units"] = len(S.units) + n_hire
    hires = [["HIRE"] for _ in range(n_hire)]

    if n_hire > 0:
        orders = sells[:3] + buys + hires + sells[3:]
    else:
        orders = sells + buys
    return orders[:S.max_orders], jobs


# ----------------------------------------------------------------------------
# Policies that depend on the market
# ----------------------------------------------------------------------------
def set_policies(S, M):
    P = PARAMS
    pf = S.price["FERTILIZER"]
    pw = S.price["WHEAT"]
    fu = {}
    late_ok = S.day <= S.last_day - 3
    fu["WHEAT"] = late_ok and pf < 2.0 * pw - 10.0
    fu["MELON"] = True
    fu["STRAWBERRY"] = 2.0 * S.price["STRAWBERRY"] > pf + 15
    fu["TOMATO"] = 3.0 * S.price["TOMATO"] > pf + 15
    fu["CARROT"] = False
    M["fert_use"] = fu
    M["fert_value"] = max(float(pf), (2.0 * pw - 8.0) if fu["WHEAT"] else 0.0)
    M["collect_fert"] = True
    care = {}
    for an, a in ANIMALS.items():
        care[an] = bool(P["care"]) and S.price[a["product"]] > 0.6 * pw
    M["care"] = care
    # melon race: deliver in batches as soon as the opponent is also ripening melons
    rush = ()
    if S.opp is not None:
        for row in S.opp["tiles"]:
            for t in row:
                if is_plant(t) and t["crop"] == "MELON" and S.day - t["planted_day"] >= 9:
                    rush = ("MELON",)
    M["rush_items"] = rush
    M["rush_batch"] = 11


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def _agent(obs, config):
    S = parse(obs, config)
    M = _memory(S.player, S.step)
    set_policies(S, M)
    ctx = build_context(S, M)
    orders, jobs = decide_market(S, M, ctx)

    k_units = max(len(S.units), M.get("planned_units", len(S.units)))
    zkey = (S.day, k_units)
    if M.get("zone_key") != zkey:
        M["zone"] = compute_zones(S, M, jobs, k_units)
        M["zone_key"] = zkey

    acts = dispatch(S, M, jobs)
    return {"farmer": acts[0], "hands": acts[1:], "market": orders}


def _fallback(obs):
    """Minimal safe behaviour if anything unexpected happens."""
    try:
        player = obs["player"]
        farm = obs["farms"][player]
        priv = obs.get("private", {}) or {}
        shed = priv.get("shed", {}) or {}
        market = [["SELL", k, int(v)] for k, v in shed.items() if k in PRODUCTS and v > 0][:10]
        fx, fy = farm["farmer"]
        t = farm["tiles"][fy][fx]
        act = ["PASS"]
        if isinstance(t, dict) and t.get("kind") == "PLANT":
            if not t.get("watered_today"):
                act = ["WATER"]
            elif t.get("yield_units", 0) > 0:
                act = ["HARVEST"]
        return {"farmer": act, "hands": [["PASS"] for _ in farm.get("hands", [])], "market": market}
    except Exception:
        return {"farmer": ["PASS"], "hands": [], "market": []}


DEBUG = False


def agent(obs, config=None):
    if DEBUG:
        return _agent(obs, config)
    try:
        return _agent(obs, config)
    except Exception:
        return _fallback(obs)
