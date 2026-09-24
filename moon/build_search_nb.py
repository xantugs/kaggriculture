"""Assemble the moon search kernel. usage: build_search_nb.py out.py [budget_s] [n_seeds] [per_round]"""
import sys, os, json, zlib, base64
HERE = os.path.dirname(os.path.abspath(__file__))
out = sys.argv[1]
budget = int(sys.argv[2]) if len(sys.argv) > 2 else int(11.3 * 3600)
n_seeds = int(sys.argv[3]) if len(sys.argv) > 3 else 48
per_round = int(sys.argv[4]) if len(sys.argv) > 4 else 8
rd = lambda *p: open(os.path.join(HERE, *p), encoding='utf-8').read()
files = dict(lean=rd('..', 'arena', 'lean.py'), decouple=rd('..', 'arena', 'decouple.py'), base=rd('..', 'arena', 'cand', 'omw_v15b.py'), moon=rd('moon.py'))
blob = base64.b85encode(zlib.compress(json.dumps(files).encode(), 9)).decode()
BEST0 = dict(start=360, feed_daily=True, survive0=True, prio0_first=True, keep_p0=True, room_first=True, fill=True, wheat_extra=16,
             night_guard=True, deliver_idle=True, load_limit=12, max_hires=14, eve0=True, herd_scarce=99.0, fert_gate=0.2,
             premium_hold=17, premium_last=True, over_more=False)
SPACE = dict(max_hires=[13, 14, 15], load_limit=[10, 11, 12, 13, 14, 16], wheat_extra=[8, 12, 16, 20, 24], fill_wheat_day=[23, 24, 25, 26],
             fill_carrot_day=[25, 26, 27], fert_reserve=[0, 4, 8], fert_gate=[0.1, 0.2, 0.5, 1.0], og_harvest=[1, 2, 3],
             night_margin=[4, 8, 12], labor_turn=[1.0, 2.0, 4.0], route_cap=[22, 23], drop_value=[3000, 6000, 10000],
             carrot_pet=[4, 8, 12, 16], carrot_fm=[2, 4, 6, 8], tom_per_shop=[0, 3, 6, 9], tom_last_day=[16, 18], care_hot=[0.4, 0.6, 0.8],
             hot_price=[40, 60, 90], shed_target=[85, 92, 96], turn_cost=[3.0, 5.0, 8.0], premium_hold=[0, 14, 17, 20],
             split_anim=[True, False], wheat_h3=[0, 3, 4], sell_margin=[0.8, 1.0, 1.2], fert_keep=[2, 6, 10],
             crop_order=[None, ["CARROT", "TOMATO", "STRAWBERRY", "WHEAT"], ["TOMATO", "CARROT", "WHEAT", "STRAWBERRY"]],
             moon_end=[696, 1000000], tape_crops=[False, True], tape_fill=[False, True], eve0=[True, False])
if os.environ.get('BEST0_JSON'):
    BEST0 = json.load(open(os.environ['BEST0_JSON']))
head = '''# Kaggriculture: parameter search for the moon season planner (takes over from day 15 on top of v15b).
import os
os.environ['OMP_NUM_THREADS'] = '1'
import subprocess, sys, json, zlib, base64
import importlib.metadata as _md
try:
    _v = _md.version('kaggle-environments')
except Exception:
    _v = None
if _v != '1.32.7':
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '--force-reinstall', '--no-deps', 'kaggle-environments==1.32.7'], check=False)
for _n, _s in json.loads(zlib.decompress(base64.b85decode(%r))).items():
    open('/kaggle/working/%%s.py' %% _n, 'w', encoding='utf-8').write(_s)
BEST0 = %r
SPACE = %r
N_SEEDS = %d
PER_ROUND = %d
BUDGET = %d
SEED0 = 17
''' % (blob, BEST0, SPACE, n_seeds, per_round, budget)
src = head + rd('search_body.py')
compile(src, out, 'exec')
open(out, 'w', encoding='utf-8').write(src)
print('built', out, len(src))
