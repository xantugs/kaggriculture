"""Turn on drop_refill (gold/top10/full/ctl.py knob) in a lean build: lean_patch_escapes.py in.py out.py
The engine's DROP empties a unit's whole inventory. sf8's mid-route shed stops and courier drops therefore also dropped
the wheat (fertilizer, animals) that the rest of the unit's queue still needed: the later FEEDs became no-ops (the
unit CAREd unfed animals), and animals placed the day before without a feed escaped (2 unfed nights in a row).
With the knob on, a unit that DROPs re-picks those inputs from the shed in the next turn(s), on the same shed tile.
Counter: _GC_REPORT['gc_refill'] (units re-picked; rows' `tel` show it)."""
import sys
src = open(sys.argv[1], encoding='utf-8').read()
func = '''
    @staticmethod
    def _drop_refill(q, pos, inv):
        need = {}
        for _t, a, _v in q:
            it = 'WHEAT' if a[0] == 'FEED' else ('FERTILIZER' if a[0] == 'FERTILIZE' else (a[1] if a[0] == 'PLACE' and len(a) > 1 else None))
            if it:
                need[it] = need.get(it, 0) + 1
            elif a[0] == 'PICKUP' and len(a) > 1:
                need[a[1]] = need.get(a[1], 0) - (int(a[2]) if len(a) >= 3 else 1)
        for it in ('GOOSE', 'SHEEP', 'COW', 'FERTILIZER', 'WHEAT'):
            k = min(need.get(it, 0), int(inv.get(it, 0)))
            if k > 0:
                q.insert(0, (tuple(pos), ['PICKUP', it, k], None))
                _GC_REPORT['gc_refill'] = _GC_REPORT.get('gc_refill', 0) + k
'''
subs = [
    # the DROP branch of GoldCtl._step_unit: queue the re-picks after the shed simulation is updated
    ("""                if act[0] == 'DROP':
                    n = sum((int(x) for x in inv.values()))
                    room[0] -= n
                    for k2, n2 in inv.items():
                        shed[k2] = shed.get(k2, 0) + int(n2)
                return act
""",
     """                if act[0] == 'DROP':
                    n = sum((int(x) for x in inv.values()))
                    room[0] -= n
                    for k2, n2 in inv.items():
                        shed[k2] = shed.get(k2, 0) + int(n2)
                    if GC_P.get('drop_refill') and q:
                        self._drop_refill(q, pos, inv)
                return act
"""),
    # the helper goes right before _trim_queue (a GoldCtl method)
    ("    def _trim_queue(self, q, pos, turns_left):\n", func.lstrip('\n') + "\n    def _trim_queue(self, q, pos, turns_left):\n"),
    # the knob: on
    ("GC_P.update({'mkt_dp_d29': False, 'final_sell0': 3, 'final_cap': 19})\n",
     "GC_P.update({'mkt_dp_d29': False, 'final_sell0': 3, 'final_cap': 19})\nGC_P.update({'drop_refill': True})\n"),
]
for old, new in subs:
    assert src.count(old) == 1, ('anchor', old[:80], src.count(old))
    src = src.replace(old, new, 1)
open(sys.argv[2], 'w', encoding='utf-8').write(src)
print('patched', sys.argv[2], 'drop_refill on')
