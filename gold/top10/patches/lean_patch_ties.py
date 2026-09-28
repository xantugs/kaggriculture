"""TIES track (tie_blk / tie_sort) into a lean build: lean_patch_ties.py in.py out.py '{"tie_blk": {"from": 6, "to": 19}, "tie_sort": "impact"}'
The layer's code is taken from gold/top10/full/ctl_r3_ties.py (from `_TB_PREM = (` up to `def _gc_chassis_floor`) and
inserted before the lean file's `def _gc_chassis_floor`; the knobs are set on GC_P right after it; the chassis branch
runs _tie_blk before its sells-first reorder, and with tie_sort "impact" (rival not flagged by ADAPT) that reorder
sorts the SELLs by the price drop each lot causes."""
import sys, os, json
src = open(sys.argv[1], encoding='utf-8').read()
cfg = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {"tie_blk": {"from": 6, "to": 19}}
ctl = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'full', 'ctl_r3_ties.py'), encoding='utf-8').read()
i0 = ctl.index('_TB_PREM = (')
i1 = ctl.index('def _gc_chassis_floor(obs, act):')
code = ctl[i0:i1]
a = 'def _gc_chassis_floor(obs, act):'
assert src.count(a) == 1
src = src.replace(a, code + 'GC_P.update(%r)\n\n\n' % (cfg,) + a, 1)
b = "                action = dict(action); action['market'] = _gc_sells_first(action['market'])\n"
assert src.count(b) == 1
src = src.replace(b, """                _ad_ = globals().get('_AD_STATE')
                if GC_P.get('tie_sort') == 'impact' and not (isinstance(_ad_, dict) and _ad_.get('off')):
                    action = dict(action); action['market'] = _gc_sells_first(action['market'], observation['market']['inventory'])
                else:
                    action = dict(action); action['market'] = _gc_sells_first(action['market'])
""", 1)
c = """        if isinstance(action, dict) and action.get('market'):
            try:
                _ad_ = globals().get('_AD_STATE')"""
assert src.count(c) == 1
src = src.replace(c, """        if GC_P.get('tie_blk'):
            try:
                action = _tie_blk(observation, action)
            except Exception:
                pass
""" + c, 1)
open(sys.argv[2], 'w', encoding='utf-8').write(src)
print('patched', sys.argv[2], cfg)
