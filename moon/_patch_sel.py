s = open('moon.py', encoding='utf-8').read()


def rep(a, b):
    global s
    assert a in s, a[:80]
    s = s.replace(a, b, 1)


# survival water on non-ongoing crops is loss-preventing
rep('''                if acts:
                    nodes.append(_MoonNode(pos, acts, need, value, 1 if cu >= 1 or in_window else 2, "C"))''',
    '''                if acts:
                    if cu >= 1:
                        value += max(yu2, 2) * pnow[crop]
                    nodes.append(_MoonNode(pos, acts, need, value, 0 if cu >= 1 else 1, "C"))''')
# ongoing crops: survival water is loss-preventing; value of a live plant = remaining productions
rep('''                elif cu >= 1 and not done:
                    acts.append(["WATER"]); value += 4 * val[crop]''',
    '''                elif cu >= 1 and not done:
                    left = max(1, cd["mx"] - max(0, (age - cd["fy"]) // cd["iv"] + 1))
                    acts.append(["WATER"]); value += left * 1.5 * pnow[crop]''')
rep('''                if acts:
                    hot = yu >= 1 and val[crop] >= MOON_P["hot_price"]
                    nodes.append(_MoonNode(pos, acts, need, value, 1 if (cu >= 1 or eve or yu >= 3 or hot) else 2, "O"))''',
    '''                if acts:
                    must = (cu >= 1 and not done) or (eve and yu + 2 > 4) or (done and yu > 0)
                    nodes.append(_MoonNode(pos, acts, need, value, 0 if must else 1, "O"))''')
# animals: care is worth a unit plus the price it takes off the rival; must-feed is loss-preventing
rep('''            if must_feed or care or feed_for_bonus:
                acts.append(["FEED"]); need["WHEAT"] = 1
                value += 300.0 if must_feed else pv * 0.3
            if care:
                acts.append(["CARE"]); value += pv * 0.9''',
    '''            if must_feed or care or feed_for_bonus:
                acts.append(["FEED"]); need["WHEAT"] = 1
                value += 300.0 if must_feed else (pnow[a["prod"]] * pend if feed_for_bonus else 0.0)
            if care:
                acts.append(["CARE"]); value += pnow[a["prod"]] * (1.0 + P["denial"])''')
rep('''            if acts:
                nodes.append(_MoonNode(pos, acts, need, value, 1 if (must_feed or yu >= a["held"] - 2) else 2, "A"))''',
    '''            if acts:
                nodes.append(_MoonNode(pos, acts, need, value, 0 if (must_feed or yu >= a["held"] - 1) else 1, "A"))''')
# plantings: value = expected crop value net of seed
rep('''            acts = ([["DIG"]] if pos in weed_set else []) + [["PLANT", crop], ["WATER"]]
            nodes.append(_MoonNode(pos, acts, {}, 80.0, 1, "P", earliest=1))''',
    '''            acts = ([["DIG"]] if pos in weed_set else []) + [["PLANT", crop], ["WATER"]]
            exp_units = {"WHEAT": 4.5, "CARROT": 3.5, "TOMATO": 7.0, "STRAWBERRY": 7.0, "MELON": 5.0}[crop]
            nodes.append(_MoonNode(pos, acts, {}, max(20.0, exp_units * val[crop] - _M_CROPS[crop]["seed"]), 1, "P", earliest=1))''')
rep('''            if pos in plan:
                acts += [["PLANT", plan[pos]], ["WATER"]]
                value += 60.0
                e = 1
            nodes.append(_MoonNode(pos, acts, need, value, 0 if dl < 99 else 1, "HP", earliest=e, deadline=dl))''',
    '''            if pos in plan:
                acts += [["PLANT", plan[pos]], ["WATER"]]
                value += 60.0
                e = 1
            nodes.append(_MoonNode(pos, acts, need, value, 0, "HP", earliest=e, deadline=dl))''')
# selection by value density against the marginal wage
rep('''        mand = [n for n in nodes if n.prio <= 1]
        opt = sorted([n for n in nodes if n.prio > 1], key=lambda n: -n.value)

        def ang(n):''', '''        always = [n for n in nodes if n.prio == 0]
        rest = sorted([n for n in nodes if n.prio > 0], key=lambda n: -n.value / (len(n.acts) + 1.5))
        per_unit = cap - 3
        used = sum(len(n.acts) + 1.5 for n in always)
        mand = list(always); opt = []
        for n in rest:
            c = len(n.acts) + 1.5
            units = int((used + c) // per_unit) + 1
            hires_needed = units - 1
            if hires_needed > max_h:
                opt.append(n); continue
            wage_turn = (_m_fib(hires_needed - 1) / per_unit) if hires_needed >= 1 else 0.0
            if n.value / c >= wage_turn * P["hire_margin"] + P["turn_cost"]:
                mand.append(n); used += c
            else:
                opt.append(n)
        opt.sort(key=lambda n: -n.value)
        _M_REPORT["sel_opt"] = _M_REPORT.get("sel_opt", 0) + len(opt)

        def ang(n):''')
rep('''turn_cost=5.0, fert_gate=1.0, care_gate=1.0,''', '''turn_cost=5.0, fert_gate=1.0, care_gate=0.0, denial=0.5, hire_margin=1.3,''')
rep('''herd_last_day=14, herd_per_day=4, max_hires=13,''', '''herd_last_day=14, herd_per_day=4, max_hires=16,''')
open('moon.py', 'w', encoding='utf-8').write(s)
print('ok')
