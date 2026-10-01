"""Find where an open-loop elite replay diverges from its recording.
usage: diag_collapse.py games.jsonl.gz gid seat cand.py
Replays the recorded game (both tapes, original engine) and the transplant (elite tape vs cand, recorded shops,
fresh weeds), snapshotting the elite farm every step, and prints the first divergences by kind."""
import sys, os, json, gzip, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lean, pinned4
from eval_elite_routes import install_town, load_games
from kaggle_environments.envs.kaggriculture import kaggriculture as K

def snap_tape(acts, p, log):
    inner = pinned4._tape(acts, p)
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
        log.append(dict(step=obs['step'], money=farm['money'], hands=len(farm.get('hands') or []),
                        farmer=list(farm['farmer']), hpos=[list(h) for h in (farm.get('hands') or [])],
                        shed=dict(priv.get('shed') or {}), seeds=dict(priv.get('seeds') or {}),
                        carried=[dict(i) for i in (priv.get('inventories') or [])], tiles=dict(tiles),
                        prices={k: int(v) for k, v in obs['market']['prices'].items()},
                        shops=list(obs['town']['unlocked_shops']), act=a))
        return a
    return f

if __name__ == '__main__':
    path, gid, seat, cand = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    d = next(g for g in load_games(path) if g['id'] == gid)
    acts = d['acts']; names = d['info']['TeamNames']
    print('game', gid, names, 'seed', d['info']['seed'], 'rewards', d['rewards'])
    rec = []
    r0 = lean.play(None, None, d['info']['seed'], agent_objs=[snap_tape(acts, 0, rec) if seat == 0 else pinned4._tape(acts, 0),
                                                              snap_tape(acts, 1, rec) if seat == 1 else pinned4._tape(acts, 1)])
    print('recorded replay rewards', r0['r'], 'shops', r0['shops'])
    tr = []
    orig = install_town(r0['shops'])
    try:
        A = lean.load(cand)
        ag = [None, None]; ag[seat] = snap_tape(acts, seat, tr); ag[1 - seat] = A
        r1 = lean.play(None, None, d['info']['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig
    print('transplant rewards', r1['r'], 'err', r1['err'])

    def first(kind, cond):
        for a, b in zip(rec, tr):
            if cond(a, b):
                return a['step']
        return None
    keys = [('money', lambda a, b: abs(a['money'] - b['money']) > 0), ('hands', lambda a, b: a['hands'] != b['hands']),
            ('farmer pos', lambda a, b: a['farmer'] != b['farmer']), ('hand pos', lambda a, b: a['hpos'] != b['hpos']),
            ('tiles', lambda a, b: a['tiles'] != b['tiles']), ('shed', lambda a, b: a['shed'] != b['shed']),
            ('seeds', lambda a, b: a['seeds'] != b['seeds']), ('carried', lambda a, b: a['carried'] != b['carried']),
            ('shops', lambda a, b: a['shops'] != b['shops'])]
    print('first divergence step by kind:')
    for k, c in keys:
        print(f'  {k:10s} {first(k, c)}')
    s0 = min(x for x in (first(k, c) for k, c in keys if k not in ('money', 'shops')) if x is not None)
    lo, hi = max(0, s0 - 3), min(len(rec), s0 + 6)
    print(f'--- steps {lo}..{hi} (rec | transplant) ---')
    for i in range(lo, hi):
        a, b = rec[i], tr[i]
        print(f"step {a['step']:3d} day {a['step']//24} h {a['step']%24}")
        print(f"   rec: money {a['money']:7.0f} hands {a['hands']} farmer {a['farmer']} hpos {a['hpos']} shed {a['shed']} seeds {a['seeds']} carried {a['carried']}")
        print(f"        tiles {a['tiles']}")
        print(f"   tr : money {b['money']:7.0f} hands {b['hands']} farmer {b['farmer']} hpos {b['hpos']} shed {b['shed']} seeds {b['seeds']} carried {b['carried']}")
        print(f"        tiles {b['tiles']}")
        print(f"   act: {a['act']}")
        if a['prices'] != b['prices']:
            print(f"   prices rec {a['prices']}\n          tr  {b['prices']}")
    # money trajectory summary
    print('--- money by day (rec | tr) ---')
    for dday in range(0, 30, 3):
        i = dday * 24
        if i < len(rec):
            print(f"  day {dday:2d}: {rec[i]['money']:8.0f} | {tr[i]['money']:8.0f}   hands {rec[i]['hands']} | {tr[i]['hands']}   tiles rec {rec[i]['tiles']}")
            print(f"                                  tiles tr  {tr[i]['tiles']}")
