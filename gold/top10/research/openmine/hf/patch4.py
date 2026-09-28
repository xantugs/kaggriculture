"""Patch 4 on gold/top10/full/ctl_hf.py: tiles for the animals due today (kept free nearest the shed, early wheat
harvest counts them, empty structures kept, not dug) + lean mid-day cash (no reserve for tomorrow's feed; animals
before strawberry seeds when anim_before_straw)."""
import os
F = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'full', 'ctl_hf.py')
src = open(F, encoding='utf-8').read()


def rep(old, new, count=1):
    global src
    n = src.count(old)
    assert n == count, (n, old[:160])
    src = src.replace(old, new)


rep('''    anim_split=None,           # {"budget": 8}: opening VRP, animal chores split over the crew in short segments + shed stop
)''', '''    anim_split=None,           # {"budget": 8}: opening VRP, animal chores split over the crew in short segments + shed stop
    anim_tiles=False,          # keep free tiles (nearest the shed) for the animals still due today; keep empty structures
    anim_tiles_max=4,
)''')

rep('''        if GC_P["dig_structs"] and not final:
            for st in ("COOP", "PASTURE"):
                for pos in free_struct[st]:
                    weeds.append(pos)''', '''        if GC_P["dig_structs"] and not final and not (opn is not None and opn.get("anim_tiles")):
            for st in ("COOP", "PASTURE"):
                for pos in free_struct[st]:
                    weeds.append(pos)''')

rep('''            free = [p for p in empties if p not in taken] + list(weeds)
            if opn is not None:
                # early wheat harvest: free the tiles the due strawberries need (oldest wheat first, age >= 2)
                eh0, eh1 = opn["early_harvest"]
                due = max(0, self._open_straw_target(day, shops) - counts.get("STRAWBERRY", 0))''', '''            free = [p for p in empties if p not in taken] + list(weeds)
            anim_due = 0
            if opn is not None and opn.get("anim_tiles"):
                # animals still due today (bought mid-day as the cash comes in): their tiles stay free, nearest the shed
                have_ = {}
                for _p, t in animals:
                    have_[t["animal"]] = have_.get(t["animal"], 0) + 1
                for an_, t_ in _open_targets(opn, day, shops):
                    anim_due += max(0, t_ - have_.get(an_, 0) - int(shed.get(an_, 0)) - herd_new.get(an_, 0))
                anim_due -= len(free_struct["COOP"]) + len(free_struct["PASTURE"])
                anim_due = max(0, min(anim_due, int(opn.get("anim_tiles_max", 4))))
                if anim_due:
                    resv = sorted([p for p in free if p not in weeds], key=lambda q: _gc_dist(q, (4.5, 4.5)))[:anim_due]
                    free = [p for p in free if p not in resv]
                    anim_due -= len(resv)
                    _GC_REPORT["gc_open_resv"] = _GC_REPORT.get("gc_open_resv", 0) + len(resv)
            if opn is not None:
                # early wheat harvest: free the tiles the due strawberries need (oldest wheat first, age >= 2)
                eh0, eh1 = opn["early_harvest"]
                due = max(0, self._open_straw_target(day, shops) - counts.get("STRAWBERRY", 0))''')
rep('''                    due += int(getattr(self, "_unplaced_n", 0))   # animals with no tile today (placed tomorrow)
                short = due - len(free) - sum(1 for v in replant)''', '''                    due += int(getattr(self, "_unplaced_n", 0))   # animals with no tile today (placed tomorrow)
                    due += anim_due   # animals due today with no free tile yet
                short = due - len(free) - sum(1 for v in replant)''')
# the harvested tiles kept empty for the animals due (not replanted): the last `anim_due` replant tiles
rep('''            for v in replant:
                crop = crop_for.get(v.pos)
                if not crop:
                    continue
                if opn is not None and GC_P["deliver_prem"]''', '''            keep_empty = set()
            if opn is not None and anim_due > 0:
                keep_empty = set(v.pos for v in sorted(replant, key=lambda v: _gc_dist(v.pos, (4.5, 4.5)))[:anim_due])
            for v in replant:
                crop = crop_for.get(v.pos)
                if not crop or v.pos in keep_empty:
                    continue
                if opn is not None and GC_P["deliver_prem"]''')

# mid-day: lean cash (no reserve for tomorrow's feed), animals before strawberry seeds when anim_before_straw
rep('''        feed0 = max(0, n_an_tot - shed.get("WHEAT", 0)) * (self.pnow.get("WHEAT", 30) + 3)
        cash -= feed0
        n_s_due = max(0, self._open_straw_target(day, shops) - counts.get("STRAWBERRY", 0))
        s_res = 100.0 * max(0, min(n_s_due, len(free)) - seeds.get("STRAWBERRY", 0))''', '''        feed0 = max(0, n_an_tot - shed.get("WHEAT", 0)) * (self.pnow.get("WHEAT", 30) + 3)
        if not opn.get("lean"):
            cash -= feed0
        n_s_due = max(0, self._open_straw_target(day, shops) - counts.get("STRAWBERRY", 0))
        s_res = 100.0 * max(0, min(n_s_due, len(free)) - seeds.get("STRAWBERRY", 0))
        if opn.get("anim_before_straw"):
            s_res = 0.0''')
open(F, 'w', encoding='utf-8', newline='').write(src)
print('patched 4')
