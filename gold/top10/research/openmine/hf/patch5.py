"""Patch 5 on gold/top10/full/ctl_hf.py: crew = hands (not minus the farmer), day-0 hires from hires0; melons first on
the melon days; animals before strawberry seeds only before the NE day; wheat seeds for the new quadrant reserved
before the land day's animals."""
import os
F = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'full', 'ctl_hf.py')
src = open(F, encoding='utf-8').read()


def rep(old, new, count=1):
    global src
    n = src.count(old)
    assert n == count, (n, old[:160])
    src = src.replace(old, new)


rep('''    anim_tiles_max=4,
)''', '''    anim_tiles_max=4,
    abs_last=5,                # anim_before_straw applies through this day
    land_wheat=0,              # mid-day land purchase: wheat seeds for this many new tiles reserved before animals
    melon_first=False,         # melons ahead of strawberries on the melon days
)''')
rep('''            self._crew_n = max(0, cn - 1 - int(cw.get("below", 0)))   # hands = crew - farmer''',
    '''            self._crew_n = max(0, cn - int(cw.get("below", 0)))   # the elite fit counts hires (hands)
            if day == opn["from_day"]:
                self._crew_n = int(opn["hires0"])''')
rep('''        want.append(("STRAWBERRY", n_s))
        if day <= op["melon_last"]:
            want.append(("MELON", max(0, op["melon"] - counts.get("MELON", 0))))''', '''        if op.get("melon_first") and day <= op["melon_last"]:
            want.append(("MELON", max(0, op["melon"] - counts.get("MELON", 0))))
            want.append(("STRAWBERRY", n_s))
        else:
            want.append(("STRAWBERRY", n_s))
            if day <= op["melon_last"]:
                want.append(("MELON", max(0, op["melon"] - counts.get("MELON", 0))))''')
rep('''        if opn.get("anim_before_straw"):
            s_res = 0.0''', '''        if opn.get("anim_before_straw") and day <= int(opn.get("abs_last", 5)):
            s_res = 0.0
        w_res = 0.0
        if new_q is not None and opn.get("land_wheat"):
            w_res = 10.0 * min(int(opn["land_wheat"]), max(0, len(free) - n_s_due))
            s_res += w_res''')
# plan-day animal budget: the same abs_last rule
rep('''                budget_ = money - spend - hire_budget - keep - feed0 - land_res - (0 if (opn["anim_before_straw"] or (opn["anim_first_day"] and day == 0)) else straw_due)''',
    '''                budget_ = money - spend - hire_budget - keep - feed0 - land_res - (0 if ((opn["anim_before_straw"] and day <= int(opn.get("abs_last", 5))) or (opn["anim_first_day"] and day == 0)) else straw_due)''')
open(F, 'w', encoding='utf-8', newline='').write(src)
print('patched 5')
