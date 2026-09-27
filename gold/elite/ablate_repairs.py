"""Ablate the transplant repairs on a fixed set of games. usage: ablate_repairs.py games cand results"""
import sys, json, collections
sys.path.insert(0, '/home/user/kaggriculture/gold/elite')
from eval_elite_routes import load_games
from transplant import reference_log, transplant_play
path, cand, res = sys.argv[1], sys.argv[2], sys.argv[3]
rows = [json.loads(l) for l in open(res)]
robust = [r for r in rows if r['team'] in ('Sida Zuo', 'Yannik Schiffner', 'Otter Vibe') and r['m'] is not None][:9]
coll = [r for r in rows if r['m'] is not None and r['tape'] < 0.6 * r['rec_tape']]
byt = collections.defaultdict(list)
for r in coll: byt[r['team']].append(r)
sel = []
while len(sel) < 8 and any(byt.values()):
    for t in list(byt):
        if byt[t] and len(sel) < 8: sel.append(byt[t].pop(0))
games = {g['id']: g for g in load_games(path)}
variants = [('outcome +R2', dict(slack_min=0, emergency=False, plant_trim=True)),
            ("+R1' drift-gated", dict(slack_min=8, emergency=False, plant_trim=True)),
            ("+R1' slack 20", dict(slack_min=20, emergency=False, plant_trim=True))]
for label, rs in (('ROBUST', robust), ('COLLAPSED', sel)):
    print(f"=== {label} ({len(rs)} games) ===")
    refs = {(r['gid'], r['seat']): reference_log(games[r['gid']], r['seat']) for r in rs}
    print(f"{'variant':22s} {'ratio':>6} {'wins':>5} {'margin':>8}   per-game ratios")
    plain = [r['tape'] / r['rec_tape'] for r in rs]
    print(f"{'plain tape':22s} {sum(plain)/len(plain):6.2f} {sum(r['m']>0 for r in rs):5d} {sum(r['m'] for r in rs)/len(rs):+8.0f}   {' '.join(f'{x:.2f}' for x in plain)}")
    for name, kw in variants:
        ratios = []; wins = 0; ms = []
        for r in rs:
            d = games[r['gid']]; s = r['seat']
            out = transplant_play(d, s, cand, refs[(r['gid'], s)], **kw)
            tape, cd = out['r'][s] or 0, out['r'][1 - s] or 0
            ratios.append(tape / r['rec_tape']); wins += tape > cd; ms.append(tape - cd)
        print(f"{name:22s} {sum(ratios)/len(ratios):6.2f} {wins:5d} {sum(ms)/len(ms):+8.0f}   {' '.join(f'{x:.2f}' for x in ratios)}", flush=True)
