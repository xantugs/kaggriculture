"""Patch 3 on gold/top10/full/ctl_hf.py: opening VRP that spreads the animal chores over the crew (short animal
segments, each ending with a shed stop, so the day's fertilizer/premium goods sell in the morning and fund the
reinvestment), then inserts the crop visits after those prefixes (cheapest insertion + 2-opt of the tails)."""
import os
F = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'full', 'ctl_hf.py')
src = open(F, encoding='utf-8').read()


def rep(old, new, count=1):
    global src
    n = src.count(old)
    assert n == count, (n, old[:160])
    src = src.replace(old, new)


rep('''    mid_tiles=True,            # mid-day animal purchases only up to the tiles/structures free for them today
)''', '''    mid_tiles=True,            # mid-day animal purchases only up to the tiles/structures free for them today
    anim_split=None,           # {"budget": 8}: opening VRP, animal chores split over the crew in short segments + shed stop
)''')

rep('''    def _vrp(self, visits, h, starts=None, caps=None):''', '''    def _vrp1_open(self, visits, h, starts=None, caps=None):
        """Opening VRP (anim_split): animal/premium visits by angle around the shed, cut into per-unit segments of about
        `budget` turns, each closed by a shed stop; then the other visits by cheapest insertion after those prefixes."""
        cfg = self.open.get("anim_split") or {}
        spawns = [(4, 4)] + self._spawns(h, (4, 4))
        if starts is not None:
            spawns = list(starts)
        n_units = len(spawns)
        s = GC_P["drop_slack"]
        n0 = getattr(self, "n0_hires", 9)
        if caps is None:
            caps = [23 - s] + [(23 if i < n0 else 22) - s for i in range(n_units - 1)]
        anv = [v for v in visits if v.tag in ("A", "L") or (self._prem_value(v) > 0 and any(a[0] == "HARVEST" for a in v.acts))]
        ids = set(id(v) for v in anv)
        oth = [v for v in visits if id(v) not in ids]
        anv.sort(key=lambda v: _gc_math.atan2(v.pos[1] - 4.5, v.pos[0] - 4.5))
        tot = self._rcost((4, 4), self._order((4, 4), anv)) if anv else 0
        B = max(int(cfg.get("budget", 8)), int(_gc_math.ceil(tot / float(max(1, n_units)))) + 2)
        segs = [[] for _ in range(n_units)]
        u = 0
        for v in anv:
            trial = segs[u] + [v]
            c = self._rcost(spawns[u], self._order(spawns[u], trial))
            if c > B and segs[u] and u + 1 < n_units:
                u += 1; trial = [v]
            segs[u] = trial
        routes = [[] for _ in range(n_units)]
        for u in range(n_units):
            seg = segs[u]
            if not seg:
                continue
            pr = [v for v in seg if self._prem_value(v) > 0 and any(a[0] == "HARVEST" for a in v.acts)]
            an = [v for v in seg if v not in pr]
            head = self._order(spawns[u], pr) if pr else []
            pos = head[-1].pos if head else spawns[u]
            a_ord = self._order(pos, an) if an else []
            seg = head + a_ord
            if sum(v.carry for v in seg) >= int(self.open.get("stop_min", 1)):
                seg = seg + [self._stop_visit(seg[-1].pos)]
            routes[u] = seg
        plen = [len(r) for r in routes]
        costs = [self._rcost(spawns[u], routes[u]) for u in range(n_units)]
        flags = [[any(v.wheat for v in r), any(v.fert for v in r), set(v.anim for v in r if v.anim)] for r in routes]
        unserved = []
        for v in sorted(oth, key=lambda v: (0 if v.must else 1, -v.value / (len(v.acts) + 2.0))):
            best = None
            for u in range(n_units):
                r = routes[u]; fl = flags[u]
                extra = (1 if v.wheat and not fl[0] else 0) + (1 if v.fert and not fl[1] else 0) + (1 if v.anim and v.anim not in fl[2] else 0)
                base = costs[u] + extra + len(v.acts)
                if base > caps[u]:
                    continue
                prev = r[plen[u] - 1].pos if plen[u] > 0 else spawns[u]
                for i in range(plen[u], len(r) + 1):
                    nxt = r[i].pos if i < len(r) else None
                    dd = abs(prev[0] - v.pos[0]) + abs(prev[1] - v.pos[1])
                    if nxt is not None:
                        dd += abs(v.pos[0] - nxt[0]) + abs(v.pos[1] - nxt[1]) - abs(prev[0] - nxt[0]) - abs(prev[1] - nxt[1])
                    c = base + dd
                    if c <= caps[u] and (best is None or c - costs[u] < best[0]):
                        best = (c - costs[u], u, i, c)
                    if nxt is not None:
                        prev = nxt
            if best is None:
                unserved.append(v); continue
            _, u, i, c = best
            routes[u].insert(i, v); costs[u] = c
            if v.wheat: flags[u][0] = True
            if v.fert: flags[u][1] = True
            if v.anim: flags[u][2].add(v.anim)
        for u in range(n_units):
            tail = routes[u][plen[u]:]
            if len(tail) > 2:
                st = routes[u][plen[u] - 1].pos if plen[u] > 0 else spawns[u]
                rr = routes[u][:plen[u]] + self._order(st, tail)
                if self._rcost(spawns[u], rr) <= self._rcost(spawns[u], routes[u]):
                    routes[u] = rr
        # a segment over the cap (a lone unit with many animals) keeps its must visits; the tail goes unserved
        for u in range(n_units):
            while self._rcost(spawns[u], routes[u]) > caps[u] and len(routes[u]) > plen[u]:
                unserved.append(routes[u].pop())
        return routes, spawns, unserved

    def _vrp(self, visits, h, starts=None, caps=None):
        if self.open is not None and self.open.get("anim_split") and self._open_on(getattr(self, "day", 0)) and not self.final:
            return self._vrp1_open(visits, h, starts, caps)''')
open(F, 'w', encoding='utf-8', newline='').write(src)
print('patched 3')
