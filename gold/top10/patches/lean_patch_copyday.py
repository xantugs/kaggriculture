"""Move the copy-game takeover from day 24 to another day in a lean build: lean_patch_copyday.py in.py out.py DAY
(the lean file folds GC_P['start'] = 576 into two literals: agent()'s `start = 576` and _route_and_hire's first-day test)."""
import sys
src = open(sys.argv[1], encoding='utf-8').read()
day = int(sys.argv[3]); step = day * 24
for old, new in (('    start = 576\n', '    start = %d\n' % step),
                 ('lo = 0 if day == 576 // 24 or final', 'lo = 0 if day == %d // 24 or final' % step)):
    assert src.count(old) == 1, ('anchor', old, src.count(old))
    src = src.replace(old, new)
open(sys.argv[2], 'w', encoding='utf-8').write(src)
print('patched', sys.argv[2], 'copy takeover day', day)
