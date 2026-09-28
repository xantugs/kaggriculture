"""Add visit_watered (g_wheat track) to a lean build, for ADAPT-flagged rivals and rich-town takeovers only:
lean_patch_vw.py in.py out.py
A mid-day re-plan (dispatch of idle units, the hour-2 rematch) of a one-time crop already watered today counts no further
growth from WATER, so it no longer harvests a fertilized carrot at age 2 (3 units, 4 tomorrow) or wheat at age 3 (5 units,
6 tomorrow) with the tile left unplanted until the next day. Same logic as GC_P['visit_watered'] in the full controller."""
import sys
src = open(sys.argv[1], encoding='utf-8').read()
nl = '\r\n' if '\r\n' in src else '\n'
src = src.replace('\r\n', '\n')

def rep(a, b):
    global src
    assert src.count(a) == 1, (a[:80], src.count(a))
    src = src.replace(a, b)

rep("""                g = min(2 if fert_active else 1, cd['mx'] - yu)
                acts.append(['WATER'])
""", """                g = min(2 if fert_active else 1, cd['mx'] - yu)
                if GC_P.get('visit_watered') and t.get('watered_today'):
                    g = 0
                acts.append(['WATER'])
""")
anchor = "GC_P.update({'mkt_dp_d29': False, 'final_sell0': 3, 'final_cap': 19})\n"
rep(anchor, anchor + "GC_P['div_over'] = dict(GC_P['div_over'], visit_watered=True)\nGC_P['rich_over'] = dict(GC_P['rich_over'], visit_watered=True)\n")
open(sys.argv[2], 'w', encoding='utf-8', newline='').write(src.replace('\n', nl))
print('patched', sys.argv[2])
