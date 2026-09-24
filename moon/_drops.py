    def _ensure_drops(self, r, limit):
        """Deliver harvested goods during the day. A unit never carries more than `limit` units at once,
        and any load left at the end is delivered by the last hour, so it can be sold before the night drop
        (which silently discards whatever the shed cannot hold)."""
        if not r.nodes:
            return
        out = []
        load = 0; lval = 0.0
        for nd in r.nodes:
            if nd.tag == "D":
                load = 0; lval = 0.0
                out.append(nd)
                continue
            if nd.units and (load + nd.units > limit or lval > MOON_P["drop_value"]) and load > 0:
                prev = out[-1].pos if out else r.start
                acc = min(_M_ACCESS, key=lambda a: _m_dist(prev, a) + _m_dist(a, nd.pos))
                out.append(_MoonNode(acc, [["DROP"]], {}, 0.0, 1, "D"))
                load = 0; lval = 0.0
            out.append(nd)
            load += nd.units
            lval += nd.units * self._unit_val(nd)
        final_drop = None
        if load >= MOON_P["final_drop_min"]:
            prev = out[-1].pos
            acc = min(_M_ACCESS, key=lambda a: _m_dist(prev, a))
            final_drop = _MoonNode(acc, [["DROP"]], {}, 0.0, 0, "DF")
            out.append(final_drop)
        r.nodes = out
        # make room: optional work, then mid-route drops, then the lowest-value remaining jobs;
        # the final delivery is kept whenever the route still carries goods
        while r.end() > r.cap:
            idx = None
            for i in range(len(r.nodes) - 1, -1, -1):
                if r.nodes[i].prio > 1 and r.nodes[i].tag not in ("D", "DF"):
                    idx = i; break
            if idx is None:
                for i in range(len(r.nodes) - 1, -1, -1):
                    if r.nodes[i].tag == "D":
                        idx = i; break
            if idx is None:
                cands = [(r.nodes[i].value, i) for i in range(len(r.nodes)) if r.nodes[i].tag not in ("D", "DF", "N")]
                if not cands:
                    _M_REPORT["over_cap"] = _M_REPORT.get("over_cap", 0) + 1
                    break
                idx = min(cands)[1]
                _M_REPORT["cut_jobs"] = _M_REPORT.get("cut_jobs", 0) + 1
            r.nodes.pop(idx)
