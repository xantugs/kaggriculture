    def _route_and_hire(self, obs, day, nodes, orders0, money, final, bought):
        P = MOON_P
        farm = obs["farms"][self.me]
        fpos = tuple(farm["farmer"])
        cap = 22 if final else P["route_cap"]
        slots0 = 10 - len(orders0)
        max_h = P["max_hires"]
        mand = [n for n in nodes if n.prio <= 1]
        opt = sorted([n for n in nodes if n.prio > 1], key=lambda n: -n.value)

        def ang(n):
            return _m_math.atan2(n.pos[1] - 4.5, n.pos[0] - 4.5)

        def radial(ns):
            return sorted(ns, key=lambda n: _m_dist(n.pos, (4.5, 4.5)))

        probe = _MoonRoute(-1, (4, 4), cap, 1, bought)

        def group_cost(ns):
            if not ns:
                return 0
            rs = radial(ns)
            probe.start = min(_M_ACCESS, key=lambda a: _m_dist(a, rs[0].pos))
            return probe.end(rs)

        # sweep: angular order, cut greedily, try every rotation
        seq0 = sorted(mand, key=ang)
        best = None
        n = len(seq0)
        step = 1 if n <= 60 else 2
        for s0 in range(0, max(1, n), step):
            seq = seq0[s0:] + seq0[:s0]
            groups = []; cur = []
            for nd in seq:
                if group_cost(cur + [nd]) <= cap:
                    cur.append(nd)
                else:
                    if cur:
                        groups.append(cur)
                    cur = [nd]
            if cur:
                groups.append(cur)
            score = (len(groups), sum(group_cost(g) for g in groups))
            if best is None or score < best[0]:
                best = (score, groups)
        groups = best[1] if best else []
        n_units = max(1, len(groups))
        hires = min(max_h, n_units - 1)
        occ = {a: 0 for a in _M_ACCESS}
        if fpos in occ:
            occ[fpos] += 1
        units = [(0, fpos, 0)]
        for k in range(1, hires + 1):
            sp = sorted(occ.items(), key=lambda kv: (kv[1], _M_ACCESS.index(kv[0])))[0][0]
            occ[sp] += 1
            units.append((k, sp, 1 if k <= slots0 else 2))
        routes = [_MoonRoute(u, sp, cap, h0, bought) for u, sp, h0 in units]
        groups.sort(key=lambda g: -group_cost(g))
        free = list(routes)
        dropped = []
        for g in groups:
            if not free:
                dropped.extend(g); continue
            rg = radial(g)
            r = min(free, key=lambda rr: (rr.hour0, _m_dist(rr.start, rg[0].pos)))
            free.remove(r)
            r.nodes = rg
            r.nodes = self._improve(r)
            while r.nodes and r.end() > r.cap:
                dropped.append(r.nodes.pop())

        def best_insert(nd, rs):
            bi = None
            for r in rs:
                base = r.end()
                for i in range(len(r.nodes) + 1):
                    e = r.end(r.nodes[:i] + [nd] + r.nodes[i:])
                    if e <= r.cap:
                        d = e - base
                        if bi is None or d < bi[0]:
                            bi = (d, r, i)
            return bi

        still = []
        for nd in dropped:
            b = best_insert(nd, routes)
            if b is None:
                still.append(nd)
            else:
                b[1].nodes.insert(b[2], nd)
        dropped = still
        # try to empty the lightest hand's route into the others
        while len(routes) > 1:
            light = min(routes[1:], key=lambda r: sum(len(x.acts) for x in r.nodes))
            others = [r for r in routes if r is not light]
            saved = [(r, list(r.nodes)) for r in others]
            ok = True
            for nd in list(light.nodes):
                b = best_insert(nd, others)
                if b is None:
                    ok = False; break
                b[1].nodes.insert(b[2], nd)
            if ok:
                routes = others
                hires -= 1
            else:
                for r, ns in saved:
                    r.nodes = ns
                break
        # unit indices must be 0..hires in hire order; spawn tiles follow the hire order
        routes.sort(key=lambda r: r.unit)
        occ = {a: 0 for a in _M_ACCESS}
        if fpos in occ:
            occ[fpos] += 1
        for k, r in enumerate(routes):
            r.unit = k
            if k > 0:
                sp = sorted(occ.items(), key=lambda kv: (kv[1], _M_ACCESS.index(kv[0])))[0][0]
                occ[sp] += 1
                r.start = sp
                r.hour0 = 1 if k <= slots0 else 2
        for nd in opt:
            b = best_insert(nd, routes)
            if b is None:
                dropped.append(nd)
            else:
                b[1].nodes.insert(b[2], nd)
        while dropped and hires < max_h and not final:
            wage = _m_fib(hires)
            k = hires + 1
            sp = sorted(occ.items(), key=lambda kv: (kv[1], _M_ACCESS.index(kv[0])))[0][0]
            trial = _MoonRoute(k, sp, cap, 1 if k <= slots0 else 2, bought)
            gain = 0.0; placed = []
            for nd in sorted(dropped, key=lambda x: -x.value):
                b = best_insert(nd, [trial])
                if b is not None:
                    trial.nodes.insert(b[2], nd); gain += nd.value; placed.append(nd)
            if placed and gain > wage * 1.3 + P["labor_turn"] * trial.cost():
                occ[sp] += 1
                hires = k
                routes.append(trial)
                dropped = [x for x in dropped if x not in placed]
            else:
                break
        _M_REPORT["dropped_jobs"] += len(dropped)
        _M_REPORT["dropped_mand"] = _M_REPORT.get("dropped_mand", 0) + sum(1 for x in dropped if x.prio <= 1)
        _M_REPORT["hires"] += hires
        for r in routes:
            r.nodes = self._improve(r)
            while r.nodes and r.end() > r.cap:
                r.nodes.pop()
            if not final:
                self._insert_drop(r)
        for r in routes:
            _M_REPORT["turns"] = _M_REPORT.get("turns", 0) + (r.end() - r.hour0)
            _M_REPORT["acts"] = _M_REPORT.get("acts", 0) + sum(len(x.acts) for x in r.nodes)
            _M_REPORT["cap_left"] = _M_REPORT.get("cap_left", 0) + max(0, r.cap - r.end())
        _M_REPORT["units"] = _M_REPORT.get("units", 0) + len(routes)
        n0 = min(hires, max(0, slots0))
        self.last_hires = hires
        sched = {0: [["HIRE"]] * n0 + orders0}
        if hires > n0:
            sched[1] = [["HIRE"]] * (hires - n0)
        self.queues = {}
        self.planned_start = {}
        self.exp_pos = {}
        plant_at = {}
        for r in routes:
            q = self._compile(r, final)
            self.queues[r.unit] = q
            if r.unit > 0:
                self.planned_start[r.unit] = (r.start, r.hour0)
            for k, (a, _) in enumerate(q):
                if a[0] == "PLANT":
                    plant_at.setdefault(a[1], []).append(r.hour0 + k)
        seeds = dict(obs["private"]["seeds"])
        for crop, hours in plant_at.items():
            hours.sort()
            have = seeds.get(crop, 0)
            per = {}
            for h in hours[have:]:
                per[h - 1] = per.get(h - 1, 0) + 1
            for h, n in per.items():
                sched.setdefault(max(0, h), []).append(["BUY_SEED", crop, n])
        self.sched = sched
        self.routes = routes

