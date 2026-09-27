"""Insert the night-drop features (shed_skip, shed_perm; code in shed_code.py) into the full controller
gold/top10/full/ctl.py with every knob OFF by default (sf8 plays unchanged). Reads the file fresh, asserts each anchor
matches exactly once, refuses to run twice.   usage: ctl_patch_shed.py [path=gold/top10/full/ctl.py]"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shed_code as C

path = sys.argv[1] if len(sys.argv) > 1 else 'gold/top10/full/ctl.py'
src = open(path, encoding='utf-8').read()
assert 'def _shed_over(' not in src, 'already patched'
lines = src.split('\n')
k = [i for i, l in enumerate(lines) if l.startswith('    room_v3_min=40,')]
assert len(k) == 1, ('knob anchor', k)
lines.insert(k[0] + 1, (C.KNOBS_CTL + C.KNOBS_CTL_PERM).rstrip('\n'))
src = '\n'.join(lines)
edits = [
    ("    def _step_unit(self, u, pos, tiles, inv, seeds, planting, sim, shed, room, hour=0):\n",
     C.PERM_METHOD + C.METHODS + "    def _step_unit(self, u, pos, tiles, inv, seeds, planting, sim, shed, room, hour=0):\n"),
    ("            if self._useful(act, tile, inv, seeds, planting, shed, room):\n",
     C.STEP_SKIP + "            if self._useful(act, tile, inv, seeds, planting, shed, room):\n"),
    ('        if final and not GC_P["stop_v2"]:\n',
     C.PERM_CALL + '        if final and not GC_P["stop_v2"]:\n'),
    ("            self._courier(positions, invs, tiles, shed, hour)\n        units = []\n",
     "            self._courier(positions, invs, tiles, shed, hour)\n" + C.ACT_OVER + "        units = []\n"),
]
for old, new in edits:
    n = src.count(old)
    assert n == 1, ('anchor count', n, old[:80])
    src = src.replace(old, new, 1)
compile(src, path, 'exec')
open(path, 'w', encoding='utf-8').write(src)
print('patched', path)
