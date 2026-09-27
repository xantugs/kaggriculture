"""Turn on trim_fix (gold/top10/full/ctl.py knob) in a lean build: lean_patch_nextleak.py in.py out.py
GoldCtl._step_unit trims a unit's queue from hour 10 on (_trim_queue drops optional visits, lowest value per action first,
until the queue fits the turns left). sf8 passed 23 - hour, but a unit acting at hour h still has hours h..23 = 24 - h
turns (dispatch and courier already use 23 - hour + 1; only day 29, whose last processed step is hour 22, has 23 - h).
Routes are planned to fill the day exactly (cap 23 = hours 1..23), so every full route that ran exactly on time lost one
planned visit at hour 10: mostly window waterings of wheat/carrots, harvests of ongoing crops and tomato waterings.
With the knob on: 24 - hour on days 0-28, 23 - hour on day 29 (unchanged there)."""
import sys
src = open(sys.argv[1], encoding='utf-8').read()
subs = [
    ("""        if q and hour >= GC_P['trim_hour']:
            self._trim_queue(q, pos, 23 - hour)
""",
     """        if q and hour >= GC_P['trim_hour']:
            self._trim_queue(q, pos, 24 - hour if GC_P.get('trim_fix') and (not self.final) else 23 - hour)
"""),
    # the knob: on
    ("GC_P.update({'mkt_dp_d29': False, 'final_sell0': 3, 'final_cap': 19})\n",
     "GC_P.update({'mkt_dp_d29': False, 'final_sell0': 3, 'final_cap': 19})\nGC_P.update({'trim_fix': True})\n"),
]
for old, new in subs:
    assert src.count(old) == 1, ('anchor', old[:80], src.count(old))
    src = src.replace(old, new, 1)
open(sys.argv[2], 'w', encoding='utf-8').write(src)
print('patched', sys.argv[2], 'trim_fix on')
