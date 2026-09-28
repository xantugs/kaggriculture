"""Patch 6 on gold/top10/full/ctl_hf.py: herd purchases paced (per-day cap, total cap), mid-day wheat on free tiles
once the cash is in (days >= mid_wheat_from), the opening VRP trims optional visits before must ones."""
import os
F = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'full', 'ctl_hf.py')
src = open(F, encoding='utf-8').read()


def rep(old, new, count=1):
    global src
    n = src.count(old)
    assert n == count, (n, old[:160])
    src = src.replace(old, new)


rep('''    melon_first=False,         # melons ahead of strawberries on the melon days
)''', '''    melon_first=False,         # melons ahead of strawberries on the melon days
    anim_day_max=99,           # animals bought per day at most (plan + mid-day)
    herd_cap=99,               # herd (placed + shed) at most
    mid_wheat_from=99,         # from this day the mid-day replan plants wheat on free tiles when the cash is in
    mid_wheat_max=8,           # ... at most this many plots per replan
)''')

# plan-day animal purchases: pace
rep('''                k_ = min(n_, int(budget_ // cost_)) if cost_ > 0 else 0
''', '''                k_ = min(n_, int(budget_ // cost_)) if cost_ > 0 else 0
                _nb = sum(herd_new.values())
                _nh = len(animals) + sum(int(shed.get(a_, 0)) for a_ in ("COW", "SHEEP", "GOOSE")) + _nb
                k_ = max(0, min(k_, int(opn.get("anim_day_max", 99)) - _nb, int(opn.get("herd_cap", 99)) - _nh))
''')
rep('''        if not hasattr(self, "_open_land_day"):
            self._open_land_day = {}
        for q_ in quads:
            if q_ != "NW" and q_ not in self._open_land_day:
                self._open_land_day[q_] = (day, sum(1 for s in shops if s in _OPEN_BUYERS["straw"]))''', '''        if not hasattr(self, "_open_land_day"):
            self._open_land_day = {}
        for q_ in quads:
            if q_ != "NW" and q_ not in self._open_land_day:
                self._open_land_day[q_] = (day, sum(1 for s in shops if s in _OPEN_BUYERS["straw"]))
        if getattr(self, "_open_bought_day", None) != day:
            self._open_bought_day = day; self._open_bought_n = 0''')
rep('''            if opn.get("mid_tiles", True):
                k_ = min(k_, room_t + fst[_GC_ANIM[an]["st"]])''', '''            if opn.get("mid_tiles", True):
                k_ = min(k_, room_t + fst[_GC_ANIM[an]["st"]])
            _nh = sum(animals_n.values()) + sum(shed.get(a_, 0) for a_ in _GC_ANIM) + sum(pending_place.values()) + sum(herd_new.values())
            k_ = max(0, min(k_, int(opn.get("anim_day_max", 99)) - self._open_bought_n, int(opn.get("herd_cap", 99)) - _nh))''')
rep('''            if k_ > 0:
                orders.append(["BUY_ANIMAL", an, k_]); cash -= k_ * _GC_ANIM[an]["cost"]; herd_new[an] = k_
''', '''            if k_ > 0:
                orders.append(["BUY_ANIMAL", an, k_]); cash -= k_ * _GC_ANIM[an]["cost"]; herd_new[an] = k_
                self._open_bought_n += k_
''')
# plan-day purchases count toward the day's cap too
rep('''                if k_ > 0 and len(orders0) < 7:
                    orders0.append(["BUY_ANIMAL", an, k_]); spend += k_ * cost_''', '''                if k_ > 0 and len(orders0) < 7:
                    orders0.append(["BUY_ANIMAL", an, k_]); spend += k_ * cost_
                    if getattr(self, "_open_bought_day", None) != day:
                        self._open_bought_day = day; self._open_bought_n = 0
                    self._open_bought_n += k_''')

# mid-day wheat on free tiles
rep('''        if new_q is not None and opn["wheat_fill"]:
            # the rest of the new land: wheat, as far as the seeds are affordable
            n_w = 0
            for p in slots[k:]:''', '''        mid_w = new_q is None and day >= int(opn.get("mid_wheat_from", 99)) and opn["wheat_fill"]
        if (new_q is not None and opn["wheat_fill"]) or mid_w:
            # the rest of the new land: wheat, as far as the seeds are affordable
            n_w = 0
            for p in (slots[k:k + int(opn.get("mid_wheat_max", 8))] if mid_w else slots[k:]):''')

# the opening VRP: over-cap trimming drops optional visits first
rep('''        for u in range(n_units):
            while self._rcost(spawns[u], routes[u]) > caps[u] and len(routes[u]) > plen[u]:
                unserved.append(routes[u].pop())
        return routes, spawns, unserved''', '''        for u in range(n_units):
            while self._rcost(spawns[u], routes[u]) > caps[u] and len(routes[u]) > plen[u]:
                tail = routes[u][plen[u]:]
                opt = [i for i, v in enumerate(tail) if not v.must]
                i = (plen[u] + opt[-1]) if opt else len(routes[u]) - 1
                unserved.append(routes[u].pop(i))
        return routes, spawns, unserved''')
open(F, 'w', encoding='utf-8', newline='').write(src)
print('patched 6')
