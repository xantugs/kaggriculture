s = open('moon.py', encoding='utf-8').read()


def rep(old, new, cnt=1):
    global s
    assert s.count(old) >= 1, old[:80]
    s = s.replace(old, new) if cnt == 0 else s.replace(old, new, cnt)


# node deadline: hour by which the node's actions must be finished
rep('''    __slots__ = ("pos", "acts", "need", "value", "prio", "tag", "earliest")

    def __init__(self, pos, acts, need=None, value=0.0, prio=1, tag="", earliest=0):
        self.pos = pos; self.acts = acts; self.need = need or {}
        self.value = value; self.prio = prio; self.tag = tag; self.earliest = earliest''',
    '''    __slots__ = ("pos", "acts", "need", "value", "prio", "tag", "earliest", "deadline")

    def __init__(self, pos, acts, need=None, value=0.0, prio=1, tag="", earliest=0, deadline=99):
        self.pos = pos; self.acts = acts; self.need = need or {}
        self.value = value; self.prio = prio; self.tag = tag; self.earliest = earliest
        self.deadline = deadline''')
rep('''            if t < nd.earliest:
                t = nd.earliest
            t += len(nd.acts)
            p = nd.pos
        return t''', '''            if t < nd.earliest:
                t = nd.earliest
            t += len(nd.acts)
            if t > nd.deadline:
                return 999
            p = nd.pos
        return t''')
# melon harvest: early deadline; harvest_free carries deadline
rep('''                if harvest_now:
                    acts.append(["HARVEST"]); value += yu2 * val[crop] * 0.5
                    harvest_free.append((pos, acts, need, value))
                    continue''', '''                if harvest_now:
                    acts.append(["HARVEST"]); value += yu2 * val[crop] * 0.5
                    harvest_free.append((pos, acts, need, value, MOON_P["melon_deadline"] if crop == "MELON" else 99))
                    continue''')
rep('''        hf_map = {p: (acts, need, value) for p, acts, need, value in harvest_free}''',
    '''        hf_map = {p: (acts, need, value, dl) for p, acts, need, value, dl in harvest_free}''')
rep('''        for pos, (acts, need, value) in hf_map.items():
            acts = list(acts)
            e = 0
            if pos in plan:
                acts += [["PLANT", plan[pos]], ["WATER"]]
                value += 60.0
                e = 1
            nodes.append(_MoonNode(pos, acts, need, value, 1, "HP", earliest=e))''', '''        for pos, (acts, need, value, dl) in hf_map.items():
            acts = list(acts)
            e = 0
            if pos in plan:
                acts += [["PLANT", plan[pos]], ["WATER"]]
                value += 60.0
                e = 1
            nodes.append(_MoonNode(pos, acts, need, value, 0 if dl < 99 else 1, "HP", earliest=e, deadline=dl))''')
# ongoing crops: harvest as soon as there are MOON_P["og_harvest"] units
rep('''                if yu > 0 and (yu >= 3 or (eve and yu + 2 > 4) or done or day >= 28):''',
    '''                if yu > 0 and (yu >= MOON_P["og_harvest"] or (eve and yu + 2 > 4) or done or day >= 28):''')
# demand-driven herd and tomatoes
rep('''    cows_base=6, cows_per_shop=1, sheep_base=4, sheep_per_yarn=4, geese_base=2, geese_per_shop=2,''',
    '''    cows_base=6, cows_per_shop=1, sheep_base=2, sheep_per_yarn=5, geese_base=0, geese_per_shop=2,
    melon_deadline=8, og_harvest=2,''')
rep('''tom_first_day=9, tom_last_day=17, tom_per_shop=5, tom_cap=12,''', '''tom_first_day=9, tom_last_day=18, tom_per_shop=6, tom_cap=30,''')
open('moon.py', 'w', encoding='utf-8').write(s)
print('patched')
