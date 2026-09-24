"""Add imitation-planner (IL) mode to moon.py: learned per-tile job probabilities drive plantings, herd placement and
optional jobs; moon keeps survival constraints, routing, hiring, capacity and selling."""
s = open('moon.py', encoding='utf-8').read()


def rep(a, b):
    global s
    assert a in s, a[:80]
    s = s.replace(a, b, 1)


rep("import math as _m_math\n", '''import math as _m_math
import json as _m_json
import zlib as _m_zlib
import base64 as _m_b64
_IL_SRC = globals().get("_IL_SRC", "")
_IL_MODEL_BLOB = globals().get("_IL_MODEL_BLOB", "")
''')

rep('''class Moon:
    def __init__(self):''', '''def _moon_il_load():
    """Model code runs in its own namespace so its constants never shadow the chassis globals."""
    if not MOON_P.get("il") or not _IL_SRC or not _IL_MODEL_BLOB:
        return None
    ns = {}
    exec(compile(_IL_SRC, "il_model", "exec"), ns)
    model = _m_json.loads(_m_zlib.decompress(_m_b64.b85decode(_IL_MODEL_BLOB)))
    return dict(model=ns["ILModel"](model), features=ns["features"], tile_inputs=ns["tile_inputs"], L=ns["LABEL_I"])


class Moon:
    def __init__(self):''')

# per-day probabilities at plan time
rep('''        self.tiles_today = tiles
        P = MOON_P
        final = day >= 29''', '''        self.tiles_today = tiles
        P = MOON_P
        final = day >= 29
        self.ilp = None
        if P.get("il"):
            if not hasattr(self, "_il"):
                try:
                    self._il = _moon_il_load()
                except Exception:
                    self._il = None; _M_REPORT["il_errors"] = _M_REPORT.get("il_errors", 0) + 1
            if self._il:
                try:
                    probs, _ = self._il["model"].predict(obs, me, self._il["features"], self._il["tile_inputs"])
                    self.ilp = probs
                    self.il_th = [t * P["il_th"] for t in self._il["model"].th]
                except Exception:
                    self.ilp = None; _M_REPORT["il_errors"] = _M_REPORT.get("il_errors", 0) + 1''')

rep('''    def _choose_crops(self, obs, day, free_tiles, plants, n_anim, shops, fut, val, money):
        P = MOON_P''', '''    def _ilq(self, pos, label):
        """Learned probability / calibrated threshold for a job on a tile (>= 1.0 means 'the elites would do it')."""
        if self.ilp is None:
            return None
        k = self._il["L"][label]
        return self.ilp[pos[1] * 10 + pos[0]][k] / max(1e-3, self.il_th[k])

    def _il_crops(self, day, free_tiles, money):
        plan = {}
        budget = money
        if day >= 28:
            return plan
        opts = []
        for pos in free_tiles:
            best = None
            for crop in ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"):
                q = self._ilq(pos, "PLANT_" + crop)
                if q is not None and q >= 1.0 and (best is None or q > best[0]):
                    best = (q, crop)
            if best:
                opts.append((best[0], pos, best[1]))
        for q, pos, crop in sorted(opts, reverse=True):
            c = _M_CROPS[crop]["seed"]
            if budget >= c:
                plan[pos] = crop; budget -= c
        _M_REPORT["il_plants"] = _M_REPORT.get("il_plants", 0) + len(plan)
        return plan

    def _il_herd(self, day, n_anim, money, free_struct, free_tiles):
        out = []
        budget = money
        opts = []
        for st, lst in free_struct.items():
            for pos in lst:
                for a in _M_ANIM:
                    if _M_ANIM[a]["st"] == st:
                        q = self._ilq(pos, "PLACE_" + a)
                        if q is not None and q >= 1.0:
                            opts.append((q, pos, a, False))
        for pos in free_tiles:
            for a in _M_ANIM:
                q = self._ilq(pos, "PLACE_" + a)
                qb = self._ilq(pos, "BUILD_COOP" if _M_ANIM[a]["st"] == "COOP" else "BUILD_PASTURE")
                if q is not None and max(q, qb or 0) >= 1.0:
                    opts.append((max(q, qb or 0), pos, a, True))
        used = set()
        for q, pos, a, build in sorted(opts, reverse=True):
            if pos in used or len(out) >= MOON_P.get("herd_per_day", 4) or day > 24:
                continue
            if budget >= _M_ANIM[a]["cost"] + 50:
                out.append((a, pos, build)); used.add(pos); budget -= _M_ANIM[a]["cost"]; n_anim[a] += 1
        return out

    def _choose_crops(self, obs, day, free_tiles, plants, n_anim, shops, fut, val, money):
        P = MOON_P
        if self.ilp is not None:
            return self._il_crops(day, free_tiles, money)''')

rep('''    def _choose_herd(self, obs, day, n_anim, shops, fut, val, money, free_struct, free_tiles):
        P = MOON_P''', '''    def _choose_herd(self, obs, day, n_anim, shops, fut, val, money, free_struct, free_tiles):
        P = MOON_P
        if self.ilp is not None:
            return self._il_herd(day, n_anim, money, free_struct, free_tiles)''')

# optional jobs on existing plants: fertilizer and yield waterings follow the learned policy
rep('''                want_fert = crop in ("WHEAT", "CARROT") and age == ws and not fert_active and yu < cd["mx"]''',
    '''                qf = self._ilq(pos, "FERTILIZE")
                want_fert = (qf is not None and qf >= 1.0 and not fert_active and yu < cd["mx"] and in_window) if qf is not None else None
                if want_fert is None:
                    want_fert = crop in ("WHEAT", "CARROT") and age == ws and not fert_active and yu < cd["mx"]''')
rep('''                if eve:
                    covered = 2 if crop == "STRAWBERRY" else 3
                    if not fert_active and covered * pnow[crop] > fert_v * P["fert_gate"]:''', '''                if eve:
                    covered = 2 if crop == "STRAWBERRY" else 3
                    qf = self._ilq(pos, "FERTILIZE")
                    fert_ok = (qf >= 1.0) if qf is not None else (covered * pnow[crop] > fert_v * P["fert_gate"])
                    if not fert_active and fert_ok:''')
# animals: care / collect follow the learned policy; feeding a must-feed animal is never skipped
rep('''            care = P["care"] and nprod <= 28 and (yu_after + 1 + pend) < a["held"] and pnow[a["prod"]] > care_cost * P["care_gate"]''',
    '''            care = P["care"] and nprod <= 28 and (yu_after + 1 + pend) < a["held"] and pnow[a["prod"]] > care_cost * P["care_gate"]
            qc = self._ilq(pos, "CARE")
            if qc is not None:
                care = nprod <= 28 and (yu_after + 1 + pend) < a["held"] and qc >= 1.0''')
rep('''            if t["fertilizer_available"] and day <= 28:
                acts.append(["COLLECT_FERTILIZER"]); value += val["FERTILIZER"] * 0.8''', '''            qk = self._ilq(pos, "COLLECT_FERTILIZER")
            if t["fertilizer_available"] and day <= 28 and (qk is None or qk >= P["il_collect"]):
                acts.append(["COLLECT_FERTILIZER"]); value += val["FERTILIZER"] * 0.8''')
rep('''route_cap=23, drop_reserve=''', '''il=False, il_th=1.0, il_collect=0.5, route_cap=23, drop_reserve=''')
open('moon.py', 'w', encoding='utf-8').write(s)
print('patched')
