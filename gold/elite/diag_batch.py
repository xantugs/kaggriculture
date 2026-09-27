"""Batch divergence diagnosis for open-loop elite replays: first step where hands/tiles/seeds diverge, cash at the
first failed hire, blocked plants, weeds. usage: diag_batch.py games.jsonl.gz cand.py results.jsonl [max] [filter]"""
import sys, json, collections
sys.path.insert(0, '/home/user/kaggriculture/arena'); sys.path.insert(0, '/home/user/kaggriculture/gold/harness'); sys.path.insert(0, '/home/user/kaggriculture/gold/elite')
import lean, pinned4
from eval_elite_routes import install_town, load_games
from diag_collapse import snap_tape
from kaggle_environments.envs.kaggriculture import kaggriculture as K

path, cand, res = sys.argv[1], sys.argv[2], sys.argv[3]
maxn = int(sys.argv[4]) if len(sys.argv) > 4 else 8
flt = sys.argv[5] if len(sys.argv) > 5 else 'collapse'
rows = [json.loads(l) for l in open(res)]
if flt == 'collapse':
    pick = [r for r in rows if r['m'] is not None and r['tape'] < 0.6 * r['rec_tape']]
else:
    pick = [r for r in rows if r['team'] == flt and r['m'] is not None]
# spread across teams
byt = collections.defaultdict(list)
for r in pick: byt[r['team']].append(r)
sel = []
while len(sel) < maxn and any(byt.values()):
    for t in list(byt):
        if byt[t] and len(sel) < maxn: sel.append(byt[t].pop(0))
games = {g['id']: g for g in load_games(path)}
for r in sel:
    d = games[r['gid']]; s = r['seat']; acts = d['acts']
    rec = []; ag0 = [pinned4._tape(acts, 0), pinned4._tape(acts, 1)]; ag0[s] = snap_tape(acts, s, rec)
    r0 = lean.play(None, None, d['info']['seed'], agent_objs=ag0)
    tr = []; orig = install_town(r0['shops'])
    try:
        ag = [None, None]; ag[s] = snap_tape(acts, s, tr); ag[1 - s] = lean.load(cand)
        r1 = lean.play(None, None, d['info']['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig
    def first(cond):
        for a, b in zip(rec, tr):
            if cond(a, b): return a['step']
        return None
    f_hands = first(lambda a, b: a['hands'] != b['hands'])
    f_tiles = first(lambda a, b: a['tiles'] != b['tiles'])
    f_seeds = first(lambda a, b: a['seeds'] != b['seeds'])
    f_money = first(lambda a, b: a['money'] != b['money'])
    f_hpos = first(lambda a, b: a['hpos'] != b['hpos'])
    # hire analysis at the first hands divergence: look at the previous step's market orders
    info = ''
    if f_hands is not None:
        i = f_hands - 1
        a, b = rec[i], tr[i]
        hires = sum(1 for o in (a['act'].get('market') or []) if o and o[0] == 'HIRE')
        info = f"hire step {i}: money rec {a['money']:.0f} tr {b['money']:.0f}, HIREs issued {hires}, hands after rec {rec[f_hands]['hands']} tr {tr[f_hands]['hands']}"
    # blocked plant: seeds diverge while tiles diverge the same step
    weeds3 = (rec[72]['tiles'].get('WEED', 0), tr[72]['tiles'].get('WEED', 0)) if len(tr) > 72 else None
    money_gap_day0 = [(t, rec[t]['money'] - tr[t]['money']) for t in (1, 12, 23) if t < len(tr)]
    print(f"{r['team'][:14]:14s} s{s} gid {r['gid']} rec {r['rec_tape']:7.0f} tape {r['tape']:7.0f} | first div: money {f_money} hands {f_hands} hpos {f_hpos} tiles {f_tiles} seeds {f_seeds} | weeds d3 rec/tr {weeds3} | money gap (rec-tr) at steps 1/12/23: {[(t, int(g)) for t, g in money_gap_day0]}")
    if info: print('     ', info)
    # show the recorded step-0 market orders and the transplant's money right after
    print('      step0 market:', rec[0]['act'].get('market'))
    if f_tiles is not None and (f_hands is None or f_tiles < f_hands):
        i = f_tiles - 1
        print(f"      tiles diverge after step {i}: act {rec[i]['act']}  rec tiles {rec[f_tiles]['tiles']}  tr tiles {tr[f_tiles]['tiles']}")
