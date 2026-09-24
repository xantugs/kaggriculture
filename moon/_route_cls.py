class _MoonRoute:
    """A unit's day: optional wait, pickups at its shed spawn, then tile visits in order.
    Shed deliveries are part of the route: `expand` inserts a DROP whenever the carried load or its value
    passes the limits, and a final delivery when goods are still carried, so every cost estimate
    already pays for getting the harvest to market. Time is the hour at which the next action executes;
    `cap` is the last usable hour + 1."""
    __slots__ = ("unit", "start", "cap", "nodes", "hour0", "bought", "deliver")

    def __init__(self, unit, start, cap, hour0, bought=(), deliver=True):
        self.unit = unit; self.start = start; self.cap = cap; self.nodes = []; self.hour0 = hour0
        self.bought = set(bought); self.deliver = deliver

    def needs(self, nodes=None):
        n = {}
        for nd in (self.nodes if nodes is None else nodes):
            for k, v in nd.need.items():
                n[k] = n.get(k, 0) + v
        return n

    def pick_start(self, need):
        # items bought at hour 0 reach the shed after that hour's unit actions
        if self.hour0 == 0 and any(k in self.bought for k in need):
            return 1
        return self.hour0

    def expand(self, nodes=None):
        nodes = self.nodes if nodes is None else nodes
        if not self.deliver:
            return nodes
        lim = MOON_P["load_limit"]; vlim = MOON_P["drop_value"]
        out = []; load = 0; lval = 0.0; prev = self.start
        for nd in nodes:
            if nd.units and load > 0 and (load + nd.units > lim or lval > vlim):
                acc = min(_M_ACCESS, key=lambda a: _m_dist(prev, a) + _m_dist(a, nd.pos))
                out.append(_MoonNode(acc, [["DROP"]], {}, 0.0, 1, "D"))
                load = 0; lval = 0.0
            out.append(nd)
            load += nd.units; lval += nd.units * nd.uval
            prev = nd.pos
        if load >= MOON_P["final_drop_min"] or lval >= MOON_P["final_drop_value"]:
            acc = min(_M_ACCESS, key=lambda a: _m_dist(prev, a))
            out.append(_MoonNode(acc, [["DROP"]], {}, 0.0, 1, "D"))
        return out

    def end(self, nodes=None):
        nodes = self.expand(nodes)
        need = self.needs(nodes)
        t = self.pick_start(need) + len(need)
        p = self.start
        for nd in nodes:
            t += _m_dist(p, nd.pos)
            if t < nd.earliest:
                t = nd.earliest
            t += len(nd.acts)
            if t > nd.deadline:
                return 999
            p = nd.pos
        return t

    def cost(self, nodes=None):
        return self.end(nodes) - self.hour0

    def fits(self, nodes=None):
        return self.end(nodes) <= self.cap
