"""Patch 1 on gold/top10/full/ctl_hf.py: herd-first opening knobs (shop-conditional herd targets, strawberry rule,
early harvest for every due placement, div_over at the handover)."""
import sys, os
F = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'full', 'ctl_hf.py')
src = open(F, encoding='utf-8').read()


def rep(old, new, count=1):
    global src
    n = src.count(old)
    assert n == count, (n, old[:120])
    src = src.replace(old, new)


# ---- defaults
rep('''    replan_hours=(5, 9, 13),   # hours at which affordable scheduled purchases are made and the routes redone
)''', '''    replan_hours=(5, 9, 13),   # hours at which affordable scheduled purchases are made and the routes redone
    anim_cond=None,            # herd-first: {kind: [buyers, {day: [target with 0, 1, 2+ buyers known]}]}, buyers in
                               # milk / yarn / egg / none (cumulative targets incl. the day's purchases; replaces anim)
    straw_hf=None,             # herd-first strawberries: {"early": {day: cum}, "ne": [a, b] (a + b * straw buyers on the NE day),
                               # "sw": [a, b, c] (a + b * buyers + c * NE plots, from the SW day), "late": [a, b, day]}
    eh_all=False,              # early harvest frees tiles for every due placement (strawberries, melons, animal structures)
    div_at_until=False,        # apply GC_P["div_over"] when the opening ends (the controller's divergent-rival rules)
    land_hold=True,            # a due land purchase holds the cash (nothing else bought until it is paid)
    anim_round=0.5,            # targets: int(t + anim_round)
)''')

# ---- helpers: targets
rep('''def _open_target(table, day):''', '''_OPEN_BUYERS = {"milk": ("PIZZA_SHOP", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP"), "yarn": ("YARN_STORE",),
                "egg": ("BAKERY", "BRUNCH_SPOT"), "straw": ("BRUNCH_SPOT", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP", "FARMERS_MARKET"),
                "none": ()}


def _open_targets(opn, day, shops):
    """Cumulative herd targets for the day: the herd-first conditional tables when set, else the plain day tables."""
    out = []
    if opn.get("anim_cond"):
        for an, spec in opn["anim_cond"].items():
            buyers, tab = spec[0], spec[1]
            k = sum(1 for s in shops if s in _OPEN_BUYERS.get(buyers, ()))
            row = None
            for d in sorted(int(x) for x in tab):
                if d <= day:
                    row = tab[d] if d in tab else tab[str(d)]
            if row is None:
                t = 0
            elif isinstance(row, (list, tuple)):
                t = float(row[min(k, len(row) - 1)])
            else:
                t = float(row)
            out.append((an, int(t + float(opn.get("anim_round", 0.5)))))
        return out
    for an, tab in opn["anim"].items():
        t_ = _open_target({int(k): v for k, v in tab.items()}, day)
        if an == "SHEEP" and day >= 6 and "YARN_STORE" in shops:
            t_ = max(t_, opn["sheep_yarn"])
        out.append((an, t_))
    return out


def _open_target(table, day):''')

rep('''            targets = []
            for an, tab in opn["anim"].items():
                t_ = _open_target({int(k): v for k, v in tab.items()}, day)
                if an == "SHEEP" and day >= 6 and "YARN_STORE" in shops:
                    t_ = max(t_, opn["sheep_yarn"])
                targets.append((an, t_))
''', '''            targets = _open_targets(opn, day, shops)
''')
rep('''        targets = []
        for an, tab in opn["anim"].items():
            t_ = _open_target({int(k): v for k, v in tab.items()}, day)
            if an == "SHEEP" and day >= 6 and "YARN_STORE" in shops:
                t_ = max(t_, opn["sheep_yarn"])
            targets.append((an, t_))
''', '''        targets = _open_targets(opn, day, shops)
''')
rep('''                for an, tab in opn["anim"].items():
                    t_ = _open_target({int(k): v for k, v in tab.items()}, day)
                    have_ = sum(''', '''                for an, t_ in _open_targets(opn, day, shops):
                    have_ = sum(''')

# ---- strawberry rule
rep('''    def _open_straw_target(self, day, shops):
        op = self.open
        if day > op["straw_last"]:
            return 0
''', '''    def _open_straw_target(self, day, shops):
        op = self.open
        if day > op["straw_last"]:
            return 0
        sh = op.get("straw_hf")
        if sh:
            # herd-first: NW plots on days 2-4, NE plots on the NE day by the strawberry buyers known then, SW plots
            # from the SW day by the buyers known then less the NE plots (cumulative plots incl. harvested/rotten ones
            # are not tracked: the target is on standing plants, which only grow before day 12)
            t = _open_target({int(k): v for k, v in sh.get("early", {}).items()}, day)
            st = getattr(self, "_open_land_day", {})
            if "NE" in st and day >= st["NE"][0]:
                b = st["NE"][1]
                a_, b_ = sh.get("ne", [7, 7])
                self._open_ne_n = int(round(a_ + b_ * b))
                t += self._open_ne_n
            if "SW" in st and day >= st["SW"][0]:
                b = st["SW"][1]
                sw = sh.get("sw", [4, 6, -0.4])
                t += max(0, int(round(sw[0] + sw[1] * b + sw[2] * getattr(self, "_open_ne_n", 0))))
            lt = sh.get("late")
            if lt and day >= int(lt[2]):
                b = sum(1 for s in shops if s in _OPEN_BUYERS["straw"])
                t += max(0, int(round(lt[0] + lt[1] * b)))
            return min(op["straw_max"], t)
''')

# ---- remember the land days and the strawberry buyers known then (plan-time and mid-day purchases)
rep('''        # ---- land (a due purchase the cash cannot cover yet holds the cash: nothing below it is bought)
        new_q = None''', '''        # ---- land (a due purchase the cash cannot cover yet holds the cash: nothing below it is bought)
        new_q = None
        if not hasattr(self, "_open_land_day"):
            self._open_land_day = {}
        for q_ in quads:
            if q_ != "NW" and q_ not in self._open_land_day:
                self._open_land_day[q_] = (day, sum(1 for s in shops if s in _OPEN_BUYERS["straw"]))''')
rep('''                    orders.append(["BUY_LAND"]); cash -= price_; new_q = q_''', '''                    orders.append(["BUY_LAND"]); cash -= price_; new_q = q_
                    self._open_land_day[q_] = (day, sum(1 for s in shops if s in _OPEN_BUYERS["straw"]))''')
rep('''                else:
                    return []
                break''', '''                elif opn.get("land_hold", True):
                    return []
                break''')
rep('''                if q_ not in quads and not new_quads and d_ is not None and day >= int(d_) and money - spend - hire_budget - keep >= price_:
                    orders0.append(["BUY_LAND"]); spend += price_; new_quads.append(q_)''', '''                if q_ not in quads and not new_quads and d_ is not None and day >= int(d_) and money - spend - hire_budget - keep >= price_:
                    orders0.append(["BUY_LAND"]); spend += price_; new_quads.append(q_)
                    if not hasattr(self, "_open_land_day"):
                        self._open_land_day = {}
                    self._open_land_day[q_] = (day, sum(1 for s in shops if s in _OPEN_BUYERS["straw"]))''')
# the plan-day record of land bought mid-day on earlier days
rep('''        if opn is not None:
            if day == opn["from_day"]:''', '''        if opn is not None:
            if not hasattr(self, "_open_land_day"):
                self._open_land_day = {}
            for q_ in quads:
                if q_ != "NW" and q_ not in self._open_land_day:
                    self._open_land_day[q_] = (day, sum(1 for s in shops if s in _OPEN_BUYERS["straw"]))
            if day == opn["from_day"]:''')
rep('''        self._open_over = None
        if GC_P["open"] is not None:''', '''        self._open_over = None
        self._open_land_day = {}
        self._open_ne_n = 0
        if GC_P["open"] is not None:''')

# ---- early harvest for every due placement
rep('''                due = max(0, self._open_straw_target(day, shops) - counts.get("STRAWBERRY", 0))
                short = due - len(free) - sum(1 for v in replant)''', '''                due = max(0, self._open_straw_target(day, shops) - counts.get("STRAWBERRY", 0))
                if opn.get("eh_all"):
                    if day <= opn["melon_last"]:
                        due += max(0, opn["melon"] - counts.get("MELON", 0))
                    due += int(getattr(self, "_unplaced_n", 0))   # animals with no tile today (placed tomorrow)
                short = due - len(free) - sum(1 for v in replant)''')
rep('''        taken = set()
        for an in ("COW", "SHEEP", "GOOSE"):
            for _ in range(shed.get(an, 0) + herd_new.get(an, 0)):''', '''        taken = set()
        self._unplaced_n = 0
        for an in ("COW", "SHEEP", "GOOSE"):
            for _ in range(shed.get(an, 0) + herd_new.get(an, 0)):''')
rep('''                    cand = [p for p in empties if p not in taken]
                    if not cand:
                        break''', '''                    cand = [p for p in empties if p not in taken]
                    if not cand:
                        self._unplaced_n += 1
                        continue''')
open(F, 'w', encoding='utf-8', newline='').write(src)
print('patched', F)
