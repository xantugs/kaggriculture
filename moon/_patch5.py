s = open('moon.py', encoding='utf-8').read()


def rep(old, new):
    global s
    assert old in s, old[:80]
    s = s.replace(old, new)


def rep_span(start, end, new):
    global s
    i = s.index(start); j = s.index(end)
    s = s[:i] + new + s[j:]


rep("""    straw_last_day=13, straw_base=10, straw_per_shop=8, straw_cap=36,
    tom_first_day=8, tom_last_day=18, tom_per_shop=8,
    carrot_per_shop=6, carrot_first_day=9,""", """    straw_last_day=12, straw_d6=16, straw_d7=20, straw_d10=33,
    tom_first_day=9, tom_last_day=17, tom_per_shop=5, tom_cap=12,
    carrot_pet=8, carrot_fm=4, carrot_first_day=9, wheat_extra=6, fill_wheat_day=24, fill_carrot_day=26,
    shed_credit=0.7, sell_drop=0.8,""")

rep("""        n_est = max(6, getattr(self, "last_hires", 8))
        reserve = sum(_m_fib(k) for k in range(n_est)) + 20 * 12 + 50
        money -= reserve""", """        n_est = max(6, getattr(self, "last_hires", 8))
        reserve = sum(_m_fib(k) for k in range(n_est)) + 50
        inv_m = obs["market"]["inventory"]
        shed_val = sum(shed.get(p, 0) * _m_price(p, inv_m[p]) for p in ("CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL"))
        money += P["shed_credit"] * min(shed_val, 4000) - reserve""")

rep_span("        # --- herd purchases reserve their tiles first", "        # --- new plantings on free tiles (after the herd took its tiles)", '''        # --- herd: animals waiting in the shed first, then purchases; both reserve their tiles
        free_tiles = sorted(set(empties) | set(weeds), key=lambda p: _m_dist(p, (4.5, 4.5)))
        free_struct = {"COOP": [p for p, k in structs if k == "COOP"], "PASTURE": [p for p, k in structs if k == "PASTURE"]}
        herd_tiles = set()
        placements = []
        for animal in ("COW", "SHEEP", "GOOSE"):
            for _ in range(int(shed.get(animal, 0))):
                st = _M_ANIM[animal]["st"]
                if free_struct[st]:
                    placements.append((animal, free_struct[st].pop(0), False, False))
                else:
                    pool = [p for p in free_tiles if p not in herd_tiles]
                    if not pool:
                        break
                    placements.append((animal, pool[0], True, False)); herd_tiles.add(pool[0])
                n_anim[animal] += 1
        herd = self._choose_herd(obs, day, n_anim, shops, fut, val, money, free_struct, [p for p in free_tiles if p not in herd_tiles])
        for animal, pos, build in herd:
            if money < _M_ANIM[animal]["cost"] + 50:
                continue
            orders0.append(["BUY_ANIMAL", animal, 1]); money -= _M_ANIM[animal]["cost"]; bought.add(animal)
            _M_REPORT["bought_animals"] += 1
            placements.append((animal, pos, build, True))
            if build:
                herd_tiles.add(pos)
        for animal, pos, build, new in placements:
            acts = []
            if build:
                if pos in weeds: acts.append(["DIG"])
                acts.append(["BUILD_COOP" if _M_ANIM[animal]["st"] == "COOP" else "BUILD_PASTURE"])
            acts.append(["PLACE", animal])
            nodes.append(_MoonNode(pos, acts, {animal: 1}, 900.0, 0, "N", earliest=1 if new else 0))

''')

rep_span("    def _choose_herd(self", "    # ------------------------------------------------------------------ routing", '''    def _choose_herd(self, obs, day, n_anim, shops, fut, val, money, free_struct, free_tiles):
        P = MOON_P
        if day > P["herd_last_day"] or day < 6:
            return []
        milk_shops = sum(1 for s in shops if "MILK" in _M_SHOPS[s])
        yarn = shops.count("YARN_STORE")
        egg_shops = sum(1 for s in shops if "EGG" in _M_SHOPS[s])
        tgt = {"COW": P["cows_base"] + P["cows_per_shop"] * milk_shops,
               "SHEEP": P["sheep_base"] + P["sheep_per_yarn"] * yarn,
               "GOOSE": P["geese_base"] + P["geese_per_shop"] * egg_shops}
        pool = list(free_tiles)
        out = []
        budget = money
        while len(out) < P.get("herd_per_day", 4):
            gaps = [(n_anim[a] / max(1, tgt[a]), a) for a in ("SHEEP", "COW", "GOOSE") if n_anim[a] < tgt[a] and budget >= _M_ANIM[a]["cost"] + 50]
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

''')

rep_span("    def _choose_crops(self", "    def _choose_herd(self", '''    def _choose_crops(self, obs, day, free_tiles, plants, n_anim, shops, fut, val, money):
        P = MOON_P
        if day >= 27:
            return {}
        cur = {"WHEAT": 0, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 0}
        for pos, t in plants:
            if t["max_lifespan_step"] < 0 or t["yield_units"] > 0 or not _M_CROPS[t["crop"]]["on"]:
                cur[t["crop"]] += 1
        tom_shops = sum(1 for s in shops if "TOMATO" in _M_SHOPS[s])
        pet = shops.count("PET_CAFE"); fm = shops.count("FARMERS_MARKET")
        target = {}
        if day <= 6: ts = P["straw_d6"]
        elif day <= 9: ts = P["straw_d7"]
        elif day <= P["straw_last_day"]: ts = P["straw_d10"]
        else: ts = 0
        target["STRAWBERRY"] = ts
        target["TOMATO"] = min(P["tom_cap"], P["tom_per_shop"] * tom_shops) if P["tom_first_day"] <= day <= P["tom_last_day"] else 0
        target["CARROT"] = (P["carrot_pet"] * pet + P["carrot_fm"] * fm) if P["carrot_first_day"] <= day <= P["fill_carrot_day"] else 0
        herd = sum(n_anim.values())
        target["WHEAT"] = (herd + P["wheat_extra"]) if day <= P["fill_wheat_day"] else 0
        tiles = sorted(set(free_tiles), key=lambda p: _m_dist(p, (4.5, 4.5)))
        plan = {}
        budget = money
        for crop in ("WHEAT", "STRAWBERRY", "TOMATO", "CARROT"):
            want = target.get(crop, 0) - cur[crop]
            while want > 0 and tiles and budget >= _M_CROPS[crop]["seed"]:
                pos = tiles.pop() if crop == "WHEAT" else tiles.pop(0)
                plan[pos] = crop; want -= 1; budget -= _M_CROPS[crop]["seed"]
        fill = "WHEAT" if day <= P["fill_wheat_day"] else ("CARROT" if day <= P["fill_carrot_day"] else None)
        if fill and day >= 10:
            while tiles and budget >= _M_CROPS[fill]["seed"]:
                plan[tiles.pop()] = fill; budget -= _M_CROPS[fill]["seed"]
        return plan

''')

rep('elif spend + c <= money + P.get("seed_credit", 400):', 'elif spend + c <= money + 200:')

rep_span("        for item in _M_PRODUCTS:\n            q = shed.get(item, 0) - keep.get(item, 0)", "        return out[:slots]", '''        for item in _M_PRODUCTS:
            q = shed.get(item, 0) - keep.get(item, 0)
            if final and step >= 712:
                out.append(["SELL", item, 999]); continue
            if q <= 0:
                continue
            p0 = _m_price(item, inv[item])
            base = _M_MKT[item][0]
            if item == "FERTILIZER":
                floor = 25
            elif final or day >= 28 or pressure:
                floor = 1
            else:
                floor = max(1, min(p0 * MOON_P.get("sell_drop", 0.8), base * 0.35))
            n = 0; iv = inv[item]
            while n < q and _m_price(item, iv) >= floor:
                n += 1; iv += 1
            if n > 0:
                out.append(["SELL", item, n])
''')
open('moon.py', 'w', encoding='utf-8').write(s)
print('patched')
