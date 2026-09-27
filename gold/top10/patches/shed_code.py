"""Shared source of the shed_skip feature (night-drop overflow: skip harvests the tile keeps for tomorrow).
Imported by lean_patch_shed.py (lean build) and ctl_patch_shed.py (full controller gold/top10/full/ctl.py).
The code reads its knobs with GC_P.get(), so it runs unchanged in both builds; every knob defaults OFF."""

KNOBS_CTL = '''    shed_skip=False,      # night drop: while tonight's projected shed load (reserves kept + goods carried into the night +
                          # harvests queued after each unit's last drop) exceeds the shed, a HARVEST after the unit's last
                          # queued drop is skipped when the tile keeps its units for tomorrow without loss (shed_skip_cls)
    shed_skip_cls=("A", "O", "G"),  # A: animal whose product stays under max_held after tonight's production; O: ongoing
                          # crop under max_yield after tonight, not decaying tomorrow; G: one-time crop before its last
                          # window day (watered or not thirsty: it keeps its units and may still grow)
    shed_skip_hour=0,     # skip only from this hour on
    shed_skip_d28=True,   # also on day 28 (the final day harvests and delivers what is left)
    shed_skip_margin=0,   # skip only while the projected load exceeds the shed by more than this many units
'''

METHODS = '''    def _shed_over(self, positions, invs, tiles, shed):
        """shed_skip: tonight's projected shed load minus the shed capacity. Goods carried into the night: the inventory of
        each unit with no drop left in its queue (less the wheat/fertilizer/animals the queue still uses) plus the harvests
        and fertilizer collects queued after its last drop. Kept in the shed: per product, the reserve not covered by
        those goods (from reserve_release_hour the market sells the reserve that the night's goods replace)."""
        carry = {}
        for u, pos in enumerate(positions):
            inv = invs[u] if u < len(invs) else {}
            q = self.queues.get(u) or []
            last_drop = max((i for i, it in enumerate(q) if it[1][0] == "DROP"), default=-1)
            if last_drop < 0:
                use = {}
                for _t, a, _v in q:
                    it = "WHEAT" if a[0] == "FEED" else ("FERTILIZER" if a[0] == "FERTILIZE" else (a[1] if a[0] == "PLACE" and len(a) > 1 else None))
                    if it:
                        use[it] = use.get(it, 0) + 1
                for k, x in inv.items():
                    carry[k] = carry.get(k, 0) + max(0, int(x) - use.get(k, 0))
            for i, (tgt, a, v) in enumerate(q):
                if i <= last_drop:
                    continue
                if a[0] == "HARVEST":
                    t = tiles[tgt[1]][tgt[0]]
                    if isinstance(t, dict) and int(t.get("yield_units", 0) or 0) > 0:
                        p = _GC_ANIM[t["animal"]]["prod"] if "animal" in t else t.get("crop")
                        carry[p] = carry.get(p, 0) + int(t["yield_units"])
                elif a[0] == "COLLECT_FERTILIZER":
                    carry["FERTILIZER"] = carry.get("FERTILIZER", 0) + 1
        kept = sum(min(int(shed.get(p, 0)), max(0, int(r) - carry.get(p, 0))) for p, r in self.reserve.items())
        return kept + sum(carry.values()) - 100

    def _shed_keeps(self, t, day):
        """shed_skip: True when the tile keeps its harvestable units until tomorrow without losing any (engine rules:
        animal production is capped at max_held, ongoing crops at max_yield, finished plants decay from
        max_lifespan_step, a plant unwatered two nights running becomes a weed)."""
        if not isinstance(t, dict) or int(t.get("yield_units", 0) or 0) <= 0:
            return False
        y = int(t["yield_units"]); cls = GC_P.get("shed_skip_cls", ("A", "O", "G"))
        if "animal" in t:
            a = _GC_ANIM[t["animal"]]
            k = day + 1 - int(t.get("placed_day", 0)) - a["fy"]
            add = (1 + (int(t.get("pending_care_bonus", 0) or 0) if t.get("fed_today") else 0)) if (k >= 0 and k % a["iv"] == 0) else 0
            return "A" in cls and y + add <= a["held"]
        if t.get("kind") != "PLANT" or t.get("crop") not in _GC_CROPS:
            return False
        cd = _GC_CROPS[t["crop"]]; age = day - int(t["planted_day"])
        if age < cd["fy"] or not (t.get("watered_today") or int(t.get("consecutive_unwatered", 1)) == 0):
            return False
        if cd["on"]:
            k = age + 1 - cd["fy"]
            eve = k >= 0 and k % cd["iv"] == 0 and k // cd["iv"] + 1 <= cd["mx"]
            add = (2 if (t.get("watered_today") and int(t.get("fertilized_until_day", -1)) >= day) else 1) if eve else 0
            mls = int(t.get("max_lifespan_step", -1))
            return "O" in cls and y + add <= cd["mx"] and (mls < 0 or mls >= (day + 2) * 24)
        return "G" in cls and age < cd["my"]

'''

STEP_SKIP = '''            if (act[0] == "HARVEST" and getattr(self, "_skip_over", 0) > GC_P.get("shed_skip_margin", 0)
                    and not any(a2[0] == "DROP" or (a2[0] in ("PLANT", "DIG") and tuple(t2) == tuple(tgt)) for t2, a2, _v2 in q[1:])
                    and self._shed_keeps(tile, self.day)):
                # shed_skip: tonight's drop would discard units; this tile keeps them for tomorrow (not when the same
                # visit replants or digs the tile: the harvest frees it)
                q.pop(0)
                self._skip_over -= int(tile.get("yield_units", 0) or 0)
                _GC_REPORT["gc_shed_skip"] = _GC_REPORT.get("gc_shed_skip", 0) + 1
                _GC_REPORT["gc_shed_skip_u"] = _GC_REPORT.get("gc_shed_skip_u", 0) + int(tile.get("yield_units", 0) or 0)
                continue
'''

ACT_OVER = '''        self._skip_over = 0
        if GC_P.get("shed_skip") and not self.final and hour >= GC_P.get("shed_skip_hour", 0) and (day < 28 or GC_P.get("shed_skip_d28", True)):
            self._skip_over = self._shed_over(positions, invs, tiles, shed)
'''

KNOBS_CTL_PERM = '''    shed_perm=False,      # night drop order: the engine fills the shed from the farmer, then hand 1, 2, ... and discards
                          # the rest; among units with the same spawn tile and turn cap (interchangeable routes) the routes
                          # whose goods reach the night drop with the highest value go to the lowest unit indices
    shed_perm_min=60,     # only on days whose planned night load (units carried after each route's last stop) is this big
'''

PERM_METHOD = '''    def _shed_perm(self, routes, spawns):
        """shed_perm: permute interchangeable routes (same spawn tile, same turn cap) so that the goods carried into the
        night drop are worth more on lower unit indices (the engine discards the tail of farmer, hand 1, 2, ...)."""
        val = getattr(self, "val", None) or {}
        fert = float(self.pnow.get("FERTILIZER", 0)) if getattr(self, "pnow", None) else 0.0
        eod = []
        for u, r in enumerate(routes):
            k0 = max((i for i, v in enumerate(r) if v.tag == "S"), default=-1)
            if self.drop_at.get(u) is not None:
                k0 = max(k0, self.drop_at[u])
            units = 0; value = 0.0
            for v in r[k0 + 1:]:
                c = int(v.carry or 0)
                if c <= 0:
                    continue
                g = v.gain or {}
                p = g.get("prod")
                pv = float(g.get("pv", val.get(p, 0.0))) if p else 0.0
                if v.tag == "A":
                    k = int(g.get("units", 0) or 0) if p else 0
                    value += k * pv + (c - k) * fert
                else:
                    value += c * pv
                units += c
            eod.append((units, value))
        if sum(x[0] for x in eod) < GC_P.get("shed_perm_min", 60):
            return
        groups = {}
        for u in range(len(routes)):
            groups.setdefault((tuple(spawns[u]), self._cap(u)), []).append(u)
        new = list(routes); new_da = {}; moved = 0
        for key, us in groups.items():
            order = sorted(us, key=lambda u: (-eod[u][1], u))
            for dst, src in zip(sorted(us), order):
                new[dst] = routes[src]
                if src in self.drop_at:
                    new_da[dst] = self.drop_at[src]
                moved += dst != src
        if moved:
            routes[:] = new
            self.drop_at = new_da
            _GC_REPORT["gc_shed_perm"] = _GC_REPORT.get("gc_shed_perm", 0) + 1

'''

PERM_CALL = '''        if GC_P.get("shed_perm") and not final:
            self._shed_perm(routes, spawns)
'''
