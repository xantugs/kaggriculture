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
        P = MOON_P
        final = day >= 29
        orders0 = []
        bought = set()
        # --- land
        quads = list(farm["unlocked_quadrants"])
        new_quads = []
        if not final:
            if "NE" not in quads and day >= 6 and money >= P["land_ne_money"]:
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
                want_fert = crop in ("WHEAT", "CARROT") and age == ws and not fert_active and yu < cd["mx"]
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
                if day == 28 and ready and yu2 > 0:
                    harvest_now = True
                if harvest_now:
                    acts.append(["HARVEST"]); value += yu2 * val[crop] * 0.5
                    harvest_free.append((pos, acts, need, value))
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
                if yu > 0 and (yu >= 3 or (eve and yu + 2 > 4) or done or day >= 28):
                    acts.append(["HARVEST"]); value += yu * val[crop] * 0.5
                if eve:
                    if not fert_active:
                        acts.append(["FERTILIZE"]); need["FERTILIZER"] = 1
                    acts.append(["WATER"]); value += val[crop]
                elif cu >= 1 and not done:
                    acts.append(["WATER"]); value += 4 * val[crop]
                if done and yu == 0 and not acts:
                    continue
                if acts:
                    nodes.append(_MoonNode(pos, acts, need, value, 1 if (cu >= 1 or eve or yu >= 3) else 2, "O"))

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
            care = P["care"] and nprod <= 28 and (yu + 1 + pend) < a["held"]
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

        # --- herd purchases reserve their tiles first
        free_tiles = sorted(set(empties) | set(weeds), key=lambda p: _m_dist(p, (4.5, 4.5)))
        herd = self._choose_herd(obs, day, n_anim, shops, fut, val, money, structs, free_tiles)
        herd_tiles = set(p for _, p, build in herd if build)
        for animal, pos, build in herd:
            if money < _M_ANIM[animal]["cost"] + 150:
                continue
            orders0.append(["BUY_ANIMAL", animal, 1]); money -= _M_ANIM[animal]["cost"]; bought.add(animal)
            _M_REPORT["bought_animals"] += 1
            acts = []
            if build:
                if pos in weeds: acts.append(["DIG"])
                acts.append(["BUILD_COOP" if _M_ANIM[animal]["st"] == "COOP" else "BUILD_PASTURE"])
            acts.append(["PLACE", animal])
            nodes.append(_MoonNode(pos, acts, {animal: 1}, 800.0, 0, "N", earliest=1))

        # --- new plantings on free tiles (after the herd took its tiles)
        hf_map = {p: (acts, need, value) for p, acts, need, value in harvest_free}
        cand = [p for p in free_tiles if p not in herd_tiles] + [p for p in hf_map]
        plan = self._choose_crops(obs, day, cand, plants, n_anim, shops, fut, val, money)
        seed_buy = {}
        for pos, crop in plan.items():
            seed_buy[crop] = seed_buy.get(crop, 0) + 1
        seeds_ok = {}
        for crop, n in seed_buy.items():
            have = seeds.get(crop, 0)
            buy = max(0, n - have)
            if buy:
                afford = max(0, int((money - 60) // _M_CROPS[crop]["seed"]))
                buy = min(buy, afford)
                if buy:
                    orders0.append(["BUY_SEED", crop, buy]); money -= buy * _M_CROPS[crop]["seed"]
            seeds_ok[crop] = min(n, have + buy)
        cnt = {}
        kept = {}
        for pos, crop in plan.items():
            cnt[crop] = cnt.get(crop, 0) + 1
            if cnt[crop] <= seeds_ok.get(crop, 0):
                kept[pos] = crop
        plan = kept
        _M_REPORT["planted"] += len(plan)
        weed_set = set(weeds)
        for pos, (acts, need, value) in hf_map.items():
            acts = list(acts)
            e = 0
            if pos in plan:
                acts += [["PLANT", plan[pos]], ["WATER"]]
                value += 60.0
                e = 1
            nodes.append(_MoonNode(pos, acts, need, value, 1, "HP", earliest=e))
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
        self.herd_size = len(animals) + len(herd)
        self._route_and_hire(obs, day, nodes, orders0, money, final, bought)

    # ------------------------------------------------------------------ strategy
    def _choose_crops(self, obs, day, free_tiles, plants, n_anim, shops, fut, val, money):
        P = MOON_P
        if day >= 28:
            return {}
        cur = {"WHEAT": 0, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 0}
        for pos, t in plants:
            if t["max_lifespan_step"] < 0 or t["yield_units"] > 0:
                cur[t["crop"]] += 1
        dem = self._demand(shops)
        straw_shops = sum(1 for s in shops if "STRAWBERRY" in _M_SHOPS[s])
        tom_shops = sum(1 for s in shops if "TOMATO" in _M_SHOPS[s])
        target = {}
        target["STRAWBERRY"] = min(P["straw_cap"], P["straw_base"] + P["straw_per_shop"] * straw_shops) if day <= P["straw_last_day"] else 0
        target["TOMATO"] = P["tom_per_shop"] * tom_shops if P["tom_first_day"] <= day <= P["tom_last_day"] else 0
        target["CARROT"] = int(P["carrot_per_shop"] * (dem["CARROT"] - 1.0) / 6.0) if P["carrot_first_day"] <= day <= 26 else 0
        herd = sum(n_anim.values())
        target["WHEAT"] = (max(6, int(herd * 1.2)) + 6) if day <= 25 else 0
        tiles = sorted(set(free_tiles), key=lambda p: _m_dist(p, (4.5, 4.5)))
        plan = {}
        budget = money - 300
        for crop in ("STRAWBERRY", "TOMATO", "CARROT", "WHEAT"):
            want = target.get(crop, 0) - cur[crop]
            while want > 0 and tiles and budget >= _M_CROPS[crop]["seed"]:
                pos = tiles.pop(0) if crop != "WHEAT" else tiles.pop()
                plan[pos] = crop; want -= 1; budget -= _M_CROPS[crop]["seed"]
        return plan

    def _choose_herd(self, obs, day, n_anim, shops, fut, val, money, structs, free_tiles):
        P = MOON_P
        if day > P["herd_last_day"] or day < 6:
            return []
        milk_shops = sum(1 for s in shops if "MILK" in _M_SHOPS[s])
        yarn = shops.count("YARN_STORE")
        egg_shops = sum(1 for s in shops if "EGG" in _M_SHOPS[s])
        tgt = {"COW": P["cows_base"] + P["cows_per_shop"] * milk_shops,
               "SHEEP": P["sheep_base"] + P["sheep_per_yarn"] * yarn,
               "GOOSE": P["geese_base"] + P["geese_per_shop"] * egg_shops}
        free_struct = {"COOP": [p for p, k in structs if k == "COOP"], "PASTURE": [p for p, k in structs if k == "PASTURE"]}
        pool = list(free_tiles)
        out = []
        budget = money - 250
        while len(out) < P.get("herd_per_day", 4):
            # buy the animal type furthest below target, relative to target
            gaps = [(n_anim[a] / max(1, tgt[a]), a) for a in ("SHEEP", "COW", "GOOSE") if n_anim[a] < tgt[a] and budget >= _M_ANIM[a]["cost"]]
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
        cap = 23 if final else 24
        routes = [_MoonRoute(0, fpos, cap, 0, bought)]
        slots0 = 10 - len(orders0)
        max_h = P["max_hires"]
        occ = {a: 0 for a in _M_ACCESS}
        if fpos in occ: occ[fpos] += 1

        def spawn():
            best = sorted(occ.items(), key=lambda kv: (kv[1], _M_ACCESS.index(kv[0])))[0][0]
            occ[best] += 1
            return best

        nodes.sort(key=lambda n: (n.prio, -n.value))
        mand = [n for n in nodes if n.prio <= 1]
        opt = [n for n in nodes if n.prio > 1]
        dropped = []

        def best_insert(nd, rs):
            best = None
            for r in rs:
                base = r.end()
                for i in range(len(r.nodes) + 1):
                    trial = r.nodes[:i] + [nd] + r.nodes[i:]
                    e = r.end(trial)
                    if e <= r.cap:
                        d = e - base
                        if best is None or d < best[0]:
                            best = (d, r, i)
            return best

        hires = 0

        def new_route():
            h0 = 1 if hires <= slots0 else 2
            return _MoonRoute(hires, spawn(), cap, h0, bought)

        for nd in mand:
            b = best_insert(nd, routes)
            if b is None and hires < max_h:
                hires += 1
                routes.append(new_route())
                b = best_insert(nd, routes[-1:])
            if b is None:
                dropped.append(nd)
            else:
                b[1].nodes.insert(b[2], nd)
        for nd in opt:
            b = best_insert(nd, routes)
            if b is None:
                dropped.append(nd)
            else:
                b[1].nodes.insert(b[2], nd)
        while dropped and hires < max_h and not final:
            wage = _m_fib(hires)
            occ_backup = dict(occ)
            hires += 1
            trial = new_route()
            gain = 0.0; placed = []
            for nd in sorted(dropped, key=lambda n: -n.value):
                b = best_insert(nd, [trial])
                if b is not None:
                    trial.nodes.insert(b[2], nd); gain += nd.value; placed.append(nd)
            if placed and gain > wage * 1.3 + P["labor_turn"] * trial.cost():
                routes.append(trial)
                dropped = [n for n in dropped if n not in placed]
            else:
                hires -= 1
                occ.clear(); occ.update(occ_backup)
                break
        _M_REPORT["dropped_jobs"] += len(dropped)
        _M_REPORT["hires"] += hires
        for r in routes:
            r.nodes = self._improve(r)
        n0 = min(hires, max(0, slots0))
        self.orders_h0 = orders0 + [["HIRE"]] * n0
        self.orders_h1 = [["HIRE"]] * (hires - n0)
        self.queues = {}
        self.planned_start = {}
        for r in routes:
            self.queues[r.unit] = self._compile(r, final)
            if r.unit > 0:
                self.planned_start[r.unit] = (r.start, r.hour0)
        self.routes = routes

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

    def _compile(self, r, final):
        q = []
        need = r.needs()
        t = r.hour0
        ps = r.pick_start(need)
        while t < ps:
            q.append(["PASS"]); t += 1
        for item in ("WHEAT", "FERTILIZER", "GOOSE", "COW", "SHEEP"):
            n = need.get(item, 0)
            if n > 0:
                q.append(["PICKUP", item, n]); t += 1
        p = r.start
        for nd in r.nodes:
            d = _m_dist(p, nd.pos)
            p = self._walk(q, p, nd.pos); t += d
            while t < nd.earliest:
                q.append(["PASS"]); t += 1
            q.extend([list(a) for a in nd.acts]); t += len(nd.acts)
        if final:
            tgt = min(_M_ACCESS, key=lambda a: _m_dist(p, a))
            p = self._walk(q, p, tgt)
            q.append(["DROP"])
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
            return
        r.start = pos
        r.nodes = self._improve(r)
        self.queues[u] = self._compile(r, self.day >= 29)[1 if False else 0:]

    # ------------------------------------------------------------------ market
    def sell_orders(self, obs, slots):
        if slots <= 0:
            return []
        step = obs["step"]; day = step // 24; hour = step % 24
        shed = obs["private"]["shed"]
        inv = obs["market"]["inventory"]
        out = []
        final = day >= 29
        herd = getattr(self, "herd_size", 0)
        today = getattr(self, "need_today", {}) if hour <= 1 else {}
        keep = {"WHEAT": 0 if final else herd + 2 + today.get("WHEAT", 0),
                "FERTILIZER": 0 if final else 10 + today.get("FERTILIZER", 0)}
        for a in _M_ANIM:
            keep[a] = 10 ** 6
        total = sum(v for k, v in shed.items() if k not in _M_ANIM)
        pressure = total > 60
        shops = list(_m_g(obs["town"], "unlocked_shops", []) or [])
        dem = self._demand(shops)
        for item in _M_PRODUCTS:
            q = shed.get(item, 0) - keep.get(item, 0)
            if final and step >= 712:
                out.append(["SELL", item, 999]); continue
            if q <= 0:
                continue
            base = _M_MKT[item][0]
            daily = dem.get(item, 1.0)
            floor = base * (0.55 if daily < 3 else 0.8) * MOON_P["sell_margin"]
            if pressure:
                floor *= 0.6
            if item == "FERTILIZER":
                floor = 30
            if final or day >= 28:
                floor = 1
            n = 0; iv = inv[item]
            while n < q and _m_price(item, iv) >= floor:
                n += 1; iv += 1
            lot = q if (final or pressure or day >= 28) else max(2, int(daily / 2) + 2)
            n = min(n, lot)
            if n > 0:
                out.append(["SELL", item, n])
        return out[:slots]


