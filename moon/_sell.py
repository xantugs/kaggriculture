    def sell_orders(self, obs, slots):
        if slots <= 0:
            return []
        step = obs["step"]; day = step // 24; hour = step % 24
        priv = obs["private"]
        shed = priv["shed"]
        inv = obs["market"]["inventory"]
        final = day >= 29
        if final and step >= 712:
            return [["SELL", it, 999] for it in _M_PRODUCTS][:slots]
        herd = getattr(self, "herd_size", 0)
        today = getattr(self, "need_today", {}) if hour <= 1 else {}
        keep = {"WHEAT": 0 if final else herd + 2 + today.get("WHEAT", 0),
                "FERTILIZER": 0 if final else MOON_P["fert_keep"] + today.get("FERTILIZER", 0)}
        carried = 0
        for u_inv in priv.get("inventories", []) or []:
            for k, v in u_inv.items():
                if k not in _M_ANIM:
                    carried += v
        # harvests still to come today (rough: 3 units per remaining HARVEST)
        more = 0
        for q in self.queues.values():
            for a, _ in q:
                if a[0] == "HARVEST":
                    more += 3
        total = sum(v for k, v in shed.items() if k not in _M_ANIM)
        sell = {}
        for item in _M_PRODUCTS:
            q = shed.get(item, 0) - keep.get(item, 0)
            if q <= 0:
                continue
            p0 = _m_price(item, inv[item])
            base = _M_MKT[item][0]
            if item == "FERTILIZER":
                floor = MOON_P["fert_floor"]
            elif final or day >= 28:
                floor = 1
            else:
                floor = max(1, min(p0 * MOON_P["sell_drop"], base * 0.35))
            n = 0; iv = inv[item]
            while n < q and _m_price(item, iv) >= floor:
                n += 1; iv += 1
            if n > 0:
                sell[item] = n
        # capacity: everything in the shed plus what units bring home tonight must fit
        over = total - sum(sell.values()) + carried + (more if hour < 22 else 0) - MOON_P["shed_target"]
        if over > 0:
            cands = []
            for item in _M_PRODUCTS:
                left = shed.get(item, 0) - sell.get(item, 0)
                hard = 0 if item not in keep else min(keep[item], herd if item == "WHEAT" else 2)
                for k in range(max(0, left - hard)):
                    iv = inv[item] + sell.get(item, 0) + k
                    cands.append((_m_price(item, iv) / _M_MKT[item][0], item))
            cands.sort()
            for _, item in cands[:over]:
                sell[item] = sell.get(item, 0) + 1
        out = [["SELL", it, n] for it, n in sell.items() if n > 0]
        return out[:slots]

