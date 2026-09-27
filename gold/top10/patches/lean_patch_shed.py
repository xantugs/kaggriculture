"""Add shed_skip (night-drop overflow: harvests the tile keeps for tomorrow are skipped while tonight's projected shed
load exceeds the shed) to a lean build and turn it ON.

usage: lean_patch_shed.py in.py out.py ['{"shed_skip_cls": ["A","O","G"], ...}']
default: gold/top10/lean_sf8.py -> gold/top10/cands/lean_sf8_shed.py with shed_skip=True and the code's default classes.
The code is shared with the full controller (gold/top10/patches/shed_code.py); every anchor must match exactly once."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shed_code as C

src_path = sys.argv[1] if len(sys.argv) > 1 else 'gold/top10/lean_sf8.py'
out_path = sys.argv[2] if len(sys.argv) > 2 else 'gold/top10/cands/lean_sf8_shed.py'
over = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
src = open(src_path, encoding='utf-8').read()

knobs = {'shed_skip': True}
knobs.update(over)
edits = [
    # knobs ON (the lean GC_P has no shed_* keys: the code's GC_P.get() defaults apply to anything not set here)
    ("GC_P.update({'mkt_dp_d29': False, 'final_sell0': 3, 'final_cap': 19})\n",
     "GC_P.update({'mkt_dp_d29': False, 'final_sell0': 3, 'final_cap': 19})\n" + 'GC_P.update(%r)\n' % (knobs,)),
    # helper methods, right before _step_unit
    ("    def _step_unit(self, u, pos, tiles, inv, seeds, planting, sim, shed, room, hour=0):\n",
     C.METHODS + "    def _step_unit(self, u, pos, tiles, inv, seeds, planting, sim, shed, room, hour=0):\n"),
    # the skip itself, before the unit executes a useful action
    ("            if self._useful(act, tile, inv, seeds, planting, shed, room):\n",
     C.STEP_SKIP + "            if self._useful(act, tile, inv, seeds, planting, shed, room):\n"),
    # tonight's projected overflow, once per step after the courier
    ("            self._courier(positions, invs, tiles, shed, hour)\n        units = []\n",
     "            self._courier(positions, invs, tiles, shed, hour)\n" + C.ACT_OVER + "        units = []\n"),
]
for old, new in edits:
    n = src.count(old)
    assert n == 1, ('anchor count', n, old[:80])
    src = src.replace(old, new, 1)
compile(src, out_path, 'exec')
open(out_path, 'w', encoding='utf-8').write(src)
print('patched', out_path, knobs)
