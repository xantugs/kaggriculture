"""Divergence trace of the REPAIRED transplant vs its recording. usage: diag_repaired.py games cand results max cushion"""
import sys, json, collections
sys.path.insert(0, '/home/user/kaggriculture/arena'); sys.path.insert(0, '/home/user/kaggriculture/gold/harness'); sys.path.insert(0, '/home/user/kaggriculture/gold/elite')
import lean, pinned4
from eval_elite_routes import install_town, load_games
from diag_collapse import snap_tape
from transplant import build_agent, reference_log
from kaggle_environments.envs.kaggriculture import kaggriculture as K

def snap_any(inner, p, log):
    # same snapshot as snap_tape, but around an arbitrary agent
    def f(obs, cfg=None):
        a = inner(obs, cfg)
        farm = obs['farms'][p]; priv = obs['private']
        tiles = collections.Counter()
        for row in farm['tiles']:
            for t in row:
                if t is None: tiles['empty'] += 1
                elif t == 'LOCKED': tiles['locked'] += 1
                elif isinstance(t, dict):
                    if t.get('kind') == 'PLANT': tiles['P:' + t['crop']] += 1
                    elif t.get('animal'): tiles['A:' + t['animal']] += 1
                    else: tiles[t.get('kind')] += 1
        log.append(dict(step=obs['step'], money=farm['money'], hands=len(farm.get('hands') or []), farmer=list(farm['farmer']),
                        hpos=[list(h) for h in (farm.get('hands') or [])], shed=dict(priv.get('shed') or {}), seeds=dict(priv.get('seeds') or {}),
                        carried=[dict(i) for i in (priv.get('inventories') or [])], tiles=dict(tiles), act=a))
        return a
    return f

path, cand, res = sys.argv[1], sys.argv[2], sys.argv[3]
maxn = int(sys.argv[4]); cushion = int(sys.argv[5])
teams = sys.argv[6].split(',') if len(sys.argv) > 6 else None
rows = [json.loads(l) for l in open(res)]
pick = [r for r in rows if r['m'] is not None and r['tape'] < 0.6 * r['rec_tape'] and (teams is None or r['team'] in teams)]
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
    hands = [x['hands'] for x in rec] + [0]
    tr = []; orig = install_town(r0['shops'])
    try:
        ag = [None, None]; ag[s] = snap_any(build_agent(acts, s, hands, cushion=cushion), s, tr); ag[1 - s] = lean.load(cand)
        r1 = lean.play(None, None, d['info']['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig
    def first(cond):
        for a, b in zip(rec, tr):
            if cond(a, b): return a['step']
        return None
    fh = first(lambda a, b: a['hands'] != b['hands']); ft = first(lambda a, b: a['tiles'] != b['tiles'])
    fs = first(lambda a, b: a['seeds'] != b['seeds']); fp = first(lambda a, b: a['hpos'] != b['hpos'] or a['farmer'] != b['farmer'])
    fc = first(lambda a, b: a['carried'] != b['carried']); fsh = first(lambda a, b: a['shed'] != b['shed'])
    print(f"{r['team'][:14]:14s} s{s} gid {r['gid']} rec {r['rec_tape']:7.0f} repaired {r1['r'][s]:7.0f} ({r1['r'][s]/r['rec_tape']:.2f}) | first div: hands {fh} pos {fp} tiles {ft} seeds {fs} carried {fc} shed {fsh}")
    cands = [x for x in (fh, ft, fs, fp) if x is not None]
    if not cands: continue
    s0 = min(cands)
    for i in range(max(0, s0 - 2), min(len(rec), s0 + 2)):
        a, b = rec[i], tr[i]
        print(f"   step {a['step']:3d} d{a['step']//24} h{a['step']%24} | rec money {a['money']:6.0f} hands {a['hands']} farmer {a['farmer']} hpos {a['hpos']} seeds {a['seeds']} carried {a['carried']}")
        print(f"                  | tr  money {b['money']:6.0f} hands {b['hands']} farmer {b['farmer']} hpos {b['hpos']} seeds {b['seeds']} carried {b['carried']}")
        print(f"        rec act {a['act']}")
        if b['act'] != a['act']: print(f"        tr  act {b['act']}")
        if a['tiles'] != b['tiles']: print(f"        tiles rec {a['tiles']}\n              tr  {b['tiles']}")
        if a['shed'] != b['shed']:
            print(f"        shed rec {{k:v for k,v in a['shed'].items() if v}}".replace('{k:v for k,v in a[\'shed\'].items() if v}', str({k: v for k, v in a['shed'].items() if v})))
            print(f"        shed tr  {str({k: v for k, v in b['shed'].items() if v})}")
    # money by day
    print('   money d3..d27 rec/tr:', ' '.join(f"d{dd}:{rec[dd*24]['money']:.0f}/{tr[dd*24]['money']:.0f}" for dd in (3, 6, 9, 12, 15, 18, 21, 24, 27) if dd * 24 < len(tr)))
