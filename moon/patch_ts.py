"""Add tape-skeleton execution (MOON_P['tape_exec']) to moon.py: units replay the chassis route's own moves;
at each op/idle step moon picks the best action for the tile's real state; market = tape hires/buys + moon sells."""
p = 'moon.py'
s = open(p, encoding='utf-8').read()
a = '''    def act(self, obs):
        step = obs["step"]; day = step // 24; hour = step % 24'''
b = '''    # ------------------------------------------------------------------ tape-skeleton execution
    def _ts_tile_op(self, tile, day, inv, plan_crop, tape_cmd, seeds):
        """Best action on the unit's current tile given the real state; prefer the tape's own action when useful."""
        useful = []
        if tile is None:
            crop = plan_crop or (tape_cmd[1] if tape_cmd and tape_cmd[0] == "PLANT" and len(tape_cmd) > 1 else None)
            if crop and seeds.get(crop, 0) > 0:
                useful.append(["PLANT", crop])
        elif isinstance(tile, dict):
            k = tile.get("kind")
            if k == "WEED":
                if plan_crop or (tape_cmd and tape_cmd[0] in ("DIG", "PLANT")):
                    useful.append(["DIG"])
            elif k == "PLANT":
                crop = tile["crop"]; cd = _M_CROPS[crop]; age = day - tile["planted_day"]; yu = tile.get("yield_units", 0)
                fert_on = tile.get("fertilized_until_day", -1) >= day; cu = tile.get("consecutive_unwatered", 0)
                wat = tile.get("watered_today")
                if not cd["on"]:
                    ws = (cd["my"] + 1) // 2; inwin = ws <= age <= cd["my"]
                    if inwin and not fert_on and not wat and inv.get("FERTILIZER", 0) > 0 and yu < cd["mx"]:
                        useful.append(["FERTILIZE"])
                    if not wat and (age == 0 or cu >= 1 or inwin):
                        useful.append(["WATER"])
                    ready = age >= cd["fy"] and yu > 0 and (age >= cd["my"] or yu >= cd["mx"] or
                                                            (crop == "WHEAT" and MOON_P.get("wheat_h3") and age >= 3 and yu >= MOON_P["wheat_h3"]))
                    if ready and (wat or not inwin):
                        useful.append(["HARVEST"])
                else:
                    k_next = age + 1 - cd["fy"]
                    eve = k_next >= 0 and k_next % cd["iv"] == 0 and (k_next // cd["iv"] + 1) <= cd["mx"]
                    if yu > 0:
                        useful.append(["HARVEST"])
                    if eve and not fert_on and inv.get("FERTILIZER", 0) > 0:
                        useful.append(["FERTILIZE"])
                    if not wat and (eve or cu >= 1):
                        useful.append(["WATER"])
            elif tile.get("animal"):
                if not tile.get("fed_today") and inv.get("WHEAT", 0) > 0:
                    useful.append(["FEED"])
                if not tile.get("cared_today") and (tile.get("fed_today") or inv.get("WHEAT", 0) > 0):
                    useful.append(["CARE"])
                if tile.get("yield_units", 0) > 0:
                    useful.append(["HARVEST"])
                if tile.get("fertilizer_available"):
                    useful.append(["COLLECT_FERTILIZER"])
        if tape_cmd and any(u[0] == tape_cmd[0] for u in useful):
            return next(u for u in useful if u[0] == tape_cmd[0])
        if useful:
            return useful[0]
        if tape_cmd and tape_cmd[0] in ("BUILD_COOP", "BUILD_PASTURE", "PLACE"):
            return list(tape_cmd)
        return ["PASS"]

    def act_ts(self, obs):
        step = obs["step"]; day = step // 24; hour = step % 24
        me = self.me = int(obs["player"]); farm = obs["farms"][me]; priv = obs["private"]
        native = _IMPL.chassis.players[me]
        tape = _IMPL.chassis.routes[2 if step >= 648 else native["route"]]
        a = tape[step] if step < len(tape) else {}
        if day != self.day:
            try:
                self.plan_day(obs)
            except Exception:
                _M_REPORT["errors"] += 1
            self.day = day
            self.ts_plan = dict(getattr(self, "last_plan", {}) or {})
        tcmds = [a.get("farmer") or ["PASS"]] + list(a.get("hands") or [])
        units = [tuple(farm["farmer"])] + [tuple(h) for h in farm["hands"]]
        invs = priv.get("inventories") or []
        seeds = dict(priv.get("seeds") or {}); shed = dict(priv.get("shed") or {})
        out = []
        for u, pos in enumerate(units):
            c = tcmds[u] if u < len(tcmds) and tcmds[u] else ["PASS"]
            inv = invs[u] if u < len(invs) else {}
            if c[0] in ("NORTH", "SOUTH", "EAST", "WEST", "DROP"):
                cmd = list(c)
            elif c[0] == "PICKUP" and len(c) > 1:
                q = int(c[2]) if len(c) > 2 else 1
                q = min(q, int(shed.get(c[1], 0)))
                cmd = ["PICKUP", c[1], q] if q > 0 else ["PASS"]
                if q > 0:
                    shed[c[1]] = shed.get(c[1], 0) - q
            else:
                x, y = pos; tile = farm["tiles"][y][x]
                cmd = self._ts_tile_op(None if tile == "LOCKED" else tile, day, inv, self.ts_plan.get(pos), c, seeds)
                if cmd[0] == "PLANT":
                    seeds[cmd[1]] = seeds.get(cmd[1], 0) - 1; self.ts_plan.pop(pos, None)
                if cmd[0] != c[0]:
                    _M_REPORT["ts_subst"] = _M_REPORT.get("ts_subst", 0) + 1
            out.append(cmd)
        mk = [list(o) for o in (a.get("market") or []) if o and o[0] in ("HIRE", "BUY_PRODUCT")]
        if hour == 0:
            want = {}
            for pos, crop in self.ts_plan.items():
                want[crop] = want.get(crop, 0) + 1
            for t in range(step, min(step + 24, len(tape))):
                for cc in [tape[t].get("farmer") or ["PASS"]] + list(tape[t].get("hands") or []):
                    if cc and cc[0] == "PLANT" and len(cc) > 1:
                        want[cc[1]] = want.get(cc[1], 0) + 1
            for crop, n in want.items():
                short = n - int(priv["seeds"].get(crop, 0))
                if short > 0 and len(mk) < 9:
                    mk.append(["BUY_SEED", crop, short])
            need_w = sum(1 for row in farm["tiles"] for t in row if isinstance(t, dict) and t.get("animal")) + 4
            if shed.get("WHEAT", 0) < need_w and not any(o[:2] == ["BUY_PRODUCT", "WHEAT"] for o in mk):
                mk.append(["BUY_PRODUCT", "WHEAT", need_w - int(shed.get("WHEAT", 0))])
        try:
            sells = self.sell_orders(obs, 10 - len(mk))
        except Exception:
            sells = []; _M_REPORT["errors"] += 1
        return {"farmer": out[0], "hands": out[1:], "market": (sells + mk)[:10]}

    def act(self, obs):
        if MOON_P.get("tape_exec"):
            return self.act_ts(obs)
        step = obs["step"]; day = step // 24; hour = step % 24'''
assert s.count(a) == 1
s = s.replace(a, b)
a = '''        plan = self._choose_crops(obs, day, cand, plants, n_anim, shops, fut, val, money)'''
b = '''        plan = self._choose_crops(obs, day, cand, plants, n_anim, shops, fut, val, money)
        self.last_plan = dict(plan)'''
assert s.count(a) == 1
s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched')
