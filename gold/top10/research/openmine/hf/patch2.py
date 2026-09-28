"""Patch 2 on gold/top10/full/ctl_hf.py: herd-first executor fixes.
(a) lean cash: the hour-0 sale of the shed's goods funds the morning plan, reserve = cash_keep only
(b) crew rule floor on the hire search (elite OLS: 3.3 + .045 tiles + .18 animals + .38 shed animals + .13 plantings/builds)
(c) forced animal/premium-first route order with a shed stop right after the animal cluster (the day's cash), trimming
    the tail visits into unserved (the hire search then prices them)
(d) hour 1: the plan's hour-1 orders and hires are merged with the mid-day orders (the mid-day replan used to swallow them)
(e) mid-day animal purchases limited to the tiles/structures that can take them today
"""
import os
F = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'full', 'ctl_hf.py')
src = open(F, encoding='utf-8').read()


def rep(old, new, count=1):
    global src
    n = src.count(old)
    assert n == count, (n, old[:160])
    src = src.replace(old, new)


rep('''    anim_round=0.5,            # targets: int(t + anim_round)
)''', '''    anim_round=0.5,            # targets: int(t + anim_round)
    lean=False,                # cash: the hour-0 sale of the shed's goods funds the plan; reserve = cash_keep only
    crew=None,                 # {"a": 3.3, "tiles": .045, "anim": .18, "shed": .38, "plant": .13, "lo": 4, "hi": 12, "below": 0}
    force_first=False,         # routes: premium harvests, then animals, then a shed stop, then the rest (tail trimmed)
    mid_tiles=True,            # mid-day animal purchases only up to the tiles/structures free for them today
)''')

# (a) lean cash
rep('''            keep = max(opn["cash_keep"], sum(_gc_fib(k) for k in range(min(self.last_hires, 11))) + n_an_k * (self.pnow.get("WHEAT", 30) + 3) + 40)
            self._open_keep = keep
''', '''            keep = max(opn["cash_keep"], sum(_gc_fib(k) for k in range(min(self.last_hires, 11))) + n_an_k * (self.pnow.get("WHEAT", 30) + 3) + 40)
            if opn.get("lean"):
                keep = float(opn["cash_keep"])
                # the hour-0 list sells the shed's goods ahead of every purchase and hire: count them as cash
                inv_ = obs["market"]["inventory"]
                s0 = 0.0
                for p_ in _GC_PRODUCTS:
                    n_ = int(shed.get(p_, 0))
                    if p_ == "WHEAT":
                        n_ -= n_an_k + 2
                    if n_ > 0:
                        # the lot's average price (each unit sold lowers the quote)
                        s0 += sum(float(_gc_price(p_, int(inv_[p_]) + k_)) for k_ in range(min(n_, 40)))
                money = money + 0.97 * s0
                self._open_s0 = s0
                _GC_REPORT["gc_open_s0"] = _GC_REPORT.get("gc_open_s0", 0) + int(s0)
            self._open_keep = keep
''')

# (b) crew floor: computed before the hire search
rep('''        self.sell0 = sell0
        self.n0_hires = 10 - len(buys0) - len(sell0)
''', '''        self.sell0 = sell0
        self.n0_hires = 10 - len(buys0) - len(sell0)
        self._crew_n = None
        if opn is not None and opn.get("crew"):
            cw = opn["crew"]
            n_tiles = len(plants) + sum(1 for v in visits if any(a[0] == "PLANT" for a in v.acts) and v.tag == "P")
            n_pl = sum(1 for v in visits for a in v.acts if a[0] in ("PLANT", "BUILD_COOP", "BUILD_PASTURE"))
            n_sh = sum(int(shed.get(a_, 0)) for a_ in ("COW", "SHEEP", "GOOSE")) + sum(herd_new.values())
            cn = cw.get("a", 3.3) + cw.get("tiles", 0.045) * len(plants) + cw.get("anim", 0.18) * len(animals) + \\
                cw.get("shed", 0.38) * n_sh + cw.get("plant", 0.13) * n_pl
            cn = int(max(cw.get("lo", 4), min(cw.get("hi", 12), round(cn))))
            self._crew_n = max(0, cn - 1 - int(cw.get("below", 0)))   # hands = crew - farmer
            _GC_REPORT["gc_open_crew"] = _GC_REPORT.get("gc_open_crew", "") + "%d:%d " % (day, cn)
''')
rep('''        lo = 0 if (first or final) else max(0, self.last_hires - 3)
        hi = GC_P["max_hands_final"] if final else GC_P["max_hands"]
''', '''        lo = 0 if (first or final) else max(0, self.last_hires - 3)
        hi = GC_P["max_hands_final"] if final else GC_P["max_hands"]
        if getattr(self, "_crew_n", None) is not None and not final:
            lo = max(0, self._crew_n)
            if self.open.get("crew", {}).get("cap"):
                hi = min(hi, self._crew_n + int(self.open["crew"]["cap"]))
''')

# (c) forced animal/premium-first order with a shed stop after the animal cluster
rep('''        routes, spawns, unserved = best[1], best[2], best[3]
        if float(GC_P["deliver_prem"] or 0.0) > 0:''', '''        routes, spawns, unserved = best[1], best[2], best[3]
        if self.open is not None and self._open_on(getattr(self, "day", 0)) and self.open.get("force_first") and not self.final:
            unserved = list(unserved)
            for u, r in enumerate(routes):
                if not r:
                    continue
                cap = caps[u] if caps is not None else self._cap(u)
                new, over = self._force_first(spawns[u], r, cap)
                routes[u] = new
                unserved += over
            return routes, spawns, unserved
        if float(GC_P["deliver_prem"] or 0.0) > 0:''')
rep('''    def _order_anim_first(self, start, vs, cap):''', '''    def _force_first(self, start, vs, cap):
        """Opening route: premium harvests first, then the other animals, a shed stop (the day's fertilizer and premium
        goods sell at once: the herd-first cash cycle), then the rest by nearest neighbour; the tail beyond the cap is
        returned as overflow (lowest value per turn first, must visits kept)."""
        dprem = float(GC_P["deliver_prem"] or 0.0)
        body = [v for v in vs if v.tag != "S"]
        pr = [v for v in body if self._prem_value(v) > 0 and any(a[0] == "HARVEST" for a in v.acts)]
        an = [v for v in body if v.tag in ("A", "L") and v not in pr]
        rest = [v for v in body if v not in pr and v not in an]
        head = self._order(start, pr) if pr else []
        pos = head[-1].pos if head else start
        a_ord = self._order(pos, an) if an else []
        carry = sum(v.carry for v in head + a_ord)
        mid = []
        if head or carry >= int(self.open.get("stop_min", 1)):
            last = (head + a_ord)[-1]
            mid = [self._stop_visit(last.pos)]
            pos = mid[0].pos
        else:
            pos = a_ord[-1].pos if a_ord else pos
        r_ord = self._order(pos, rest) if rest else []
        out = head + a_ord + mid + r_ord
        over = []
        while self._rcost(start, out) > cap:
            cands = [v for v in r_ord if not v.must]
            if not cands:
                cands = [v for v in r_ord]
            if not cands:
                break
            v = min(cands, key=lambda v: v.value / (len(v.acts) + 1.0))
            r_ord.remove(v); over.append(v)
            out = head + a_ord + mid + r_ord
        return out, over

    def _order_anim_first(self, start, vs, cap):''')

# (d) hour 1: merge the plan's hour-1 orders with the mid-day orders
rep('''        mid = list(getattr(self, "_mid_orders", []) or [])
        if mid:
            return (mid + prem + rest)[:10]
        if hour == 1:''', '''        mid = list(getattr(self, "_mid_orders", []) or [])
        if mid and hour == 1:
            h1 = max(0, min(self.hires_left, 10 - len(self.orders1)))
            self.hires_left -= h1
            return ([["HIRE"]] * h1 + list(self.orders1) + mid + prem + rest)[:10]
        if mid:
            return (mid + prem + rest)[:10]
        if hour == 1:''')

# (e) mid-day animal purchases limited by the tiles/structures free for them
rep('''        for an, t_ in sorted(targets, key=lambda x: opn["anim_order"].index(x[0]) if x[0] in opn["anim_order"] else 9):
            have = animals_n.get(an, 0) + shed.get(an, 0) + pending_place.get(an, 0)
            k_ = min(max(0, t_ - have), int(cash // _GC_ANIM[an]["cost"]))''', '''        room_t = len(free) if opn.get("mid_tiles", True) else 999
        fst = {"COOP": 0, "PASTURE": 0}
        for y in range(10):
            for x in range(10):
                t = tiles[y][x]
                if isinstance(t, dict) and t.get("kind") in ("COOP", "PASTURE") and "animal" not in t and (x, y) not in claimed:
                    fst[t["kind"]] += 1
        for an, t_ in sorted(targets, key=lambda x: opn["anim_order"].index(x[0]) if x[0] in opn["anim_order"] else 9):
            have = animals_n.get(an, 0) + shed.get(an, 0) + pending_place.get(an, 0)
            k_ = min(max(0, t_ - have), int(cash // _GC_ANIM[an]["cost"]))
            if opn.get("mid_tiles", True):
                k_ = min(k_, room_t + fst[_GC_ANIM[an]["st"]])''')
rep('''            if k_ > 0:
                orders.append(["BUY_ANIMAL", an, k_]); cash -= k_ * _GC_ANIM[an]["cost"]; herd_new[an] = k_
''', '''            if k_ > 0:
                orders.append(["BUY_ANIMAL", an, k_]); cash -= k_ * _GC_ANIM[an]["cost"]; herd_new[an] = k_
                st_ = _GC_ANIM[an]["st"]
                use_ = min(k_, fst[st_]); fst[st_] -= use_; room_t -= (k_ - use_)
''')
open(F, 'w', encoding='utf-8', newline='').write(src)
print('patched')

# (e2) mid-day placement: empty structures first (the plan's placement does this already)
src = open(F, encoding='utf-8').read()
rep('''        taken = set()
        for an, k_ in herd_new.items():
            st = _GC_ANIM[an]["st"]
            for _ in range(k_):
                cand = [p for p in free if p not in taken]
                if not cand:
                    break
                pos = min(cand, key=lambda p: _gc_dist(p, (4.5, 4.5)))
                taken.add(pos)
                fc = [["FEED"], ["CARE"]] if opn["feed_place"] else []
                # the animal lands in the shed after this step: a PASS keeps the pickup from firing too early
                visits.append(_GcVisit(pos, [["BUILD_" + st], ["PLACE", an]] + fc, value=300.0, must=True, anim=an, tag="L", wheat=1 if fc else 0))''', '''        taken = set()
        est = {"COOP": [], "PASTURE": []}
        for y in range(10):
            for x in range(10):
                t = tiles[y][x]
                if isinstance(t, dict) and t.get("kind") in ("COOP", "PASTURE") and "animal" not in t and (x, y) not in claimed:
                    est[t["kind"]].append((x, y))
        for an, k_ in herd_new.items():
            st = _GC_ANIM[an]["st"]
            for _ in range(k_):
                fc = [["FEED"], ["CARE"]] if opn["feed_place"] else []
                if est[st]:
                    pos = min(est[st], key=lambda p: _gc_dist(p, (4.5, 4.5)))
                    est[st].remove(pos)
                    visits.append(_GcVisit(pos, [["PLACE", an]] + fc, value=300.0, must=True, anim=an, tag="L", wheat=1 if fc else 0))
                    continue
                cand = [p for p in free if p not in taken]
                if not cand:
                    break
                pos = min(cand, key=lambda p: _gc_dist(p, (4.5, 4.5)))
                taken.add(pos)
                # the animal lands in the shed after this step: a PASS keeps the pickup from firing too early
                visits.append(_GcVisit(pos, [["BUILD_" + st], ["PLACE", an]] + fc, value=300.0, must=True, anim=an, tag="L", wheat=1 if fc else 0))''')
open(F, 'w', encoding='utf-8', newline='').write(src)
print('patched e2')
