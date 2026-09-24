"""v12 + XB block layer with a JSON config. usage: build_xb.py out.py '{json cfg}'"""
import sys, os, json
here = os.path.dirname(os.path.abspath(__file__))
DEF = dict(crop='STRAWBERRY', commit_day=13, commit_hour=2, n=20, min_price=190, min_shops=1, buy_land=True, min_tiles=8,
           reserve=3000, max_crew=3, move_per_task=1.3, hire_deadline=3, plant_days=2, fertilize=True, harvest_at=2,
           sell_lot=12, sell_min=30)
cfg = dict(DEF); cfg.update(json.loads(sys.argv[2]) if len(sys.argv) > 2 else {})
base = open(os.path.join(here, '..', 'arena', 'cand', 'omw_v12.py'), encoding='utf-8').read()
layer = open(os.path.join(here, 'xb_layer.py'), encoding='utf-8').read().replace('__XBCFG__', repr(cfg))
open(sys.argv[1], 'w', encoding='utf-8').write(base.rstrip() + '\n\n' + layer)
print('built', sys.argv[1], cfg)
