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
        """shed_skip: tonight's projected shed load minus the shed capacity (the _courier projection: reserves kept in the
        shed, goods carried by units with no drop left in their queue, harvests and collects after each last drop)."""
        res = sum(int(v) for v in self.reserve.values())
        total = min(sum(int(v) for v in shed.values()), res)
        for u, pos in enumerate(positions):
            inv = invs[u] if u < len(invs) else {}
            q = self.queues.get(u) or []
            last_drop = max((i for i, it in enumerate(q) if it[1][0] == "DROP"), default=-1)
            if last_drop < 0:
                total += sum(int(x) for x in inv.values())
            for i, (tgt, a, v) in enumerate(q):
                if i <= last_drop:
                    continue
                if a[0] == "HARVEST":
                    t = tiles[tgt[1]][tgt[0]]
                    total += int(t.get("yield_units", 0) or 0) if isinstance(t, dict) else 0
                elif a[0] == "COLLECT_FERTILIZER":
                    total += 1
        return total - 100

    def _shed_keeps(self, t, day):
        """shed_skip: True when the tile keeps its harvestable units until tomorrow without losing any (engine rules:
        animal production is capped at max_held, ongoing crops at max_yield, finished plants decay from
        max_lifespan_step, a plant unwatered two nights running becomes a weed)."""
        if not isinstance(t, dict) or int(t.get("yield_units", 0) or 0) <= 0:
            return False
        y = int(t["yield_units"]); cls = GC_P.get("shed_skip_cls", ())
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
                    and not any(a2[0] == "DROP" for _t2, a2, _v2 in q[1:]) and self._shed_keeps(tile, self.day)):
                # shed_skip: tonight's drop would discard units; this tile keeps them for tomorrow
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
