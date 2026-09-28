"""Per-hand utilisation of a candidate in repaired elite seats (elite_gate set-up): for each day and unit index
(0 = farmer, i = i-th hand of the day), turns spent working (tile/shed ops), moving, passing, idle (no action).
usage: hand_util.py games.jsonl.gz refs.jsonl cand.py out.jsonl gid:seat[,gid:seat...]"""
import sys, os, json, collections
sys.path.insert(0, '/home/user/kaggriculture/arena'); sys.path.insert(0, '/home/user/kaggriculture/gold/harness'); sys.path.insert(0, '/home/user/kaggriculture/gold/elite')

def play(d, ref, cand):
    import lean
    from eval_elite_routes import install_town
    from transplant import build_agent
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    s = ref['seat']
    rr = dict(hands=ref['hands'], money=ref['money'], outcomes={int(k): v for k, v in ref['outcomes'].items()}, shops=ref['shops'])
    orig_eod = install_town(ref['shops'])
    U = collections.defaultdict(lambda: collections.Counter())   # (day, idx) -> verb counts
    HR = collections.defaultdict(list)                            # (day, idx) -> hours of work
    NH = {}                                                       # day -> hands of the day
    FARM = [None]
    MV = set(K.FARMER_MOVES)
    oau = K._apply_unit_action
    def au(farm, private, idx, action, board_size, day, turns_per_day, shed_capacity=100):
        if FARM[0] is not None and farm is FARM[0] and isinstance(action, list) and action:
            op = 'MOVE' if action[0] in MV else str(action[0])
            U[(day, idx)][op] += 1
            if op == 'PASS': HR[(day, idx)].append((STEP[0] + 1) % 24)
            NH[day] = max(NH.get(day, 0), len(farm.get('hands', [])))
        return oau(farm, private, idx, action, board_size, day, turns_per_day, shed_capacity)
    opm = K._process_market
    STEP = [0]
    def pm(state, env):
        FARM[0] = state[0].observation.farms[1 - s]
        STEP[0] = int(K.get(state[0].observation, 'step', 0))
        return opm(state, env)
    K._apply_unit_action = au; K._process_market = pm
    try:
        ag = [None, None]; ag[s] = build_agent(d['acts'], s, rr, slack_min=20); A = lean.load(cand); ag[1 - s] = A
        r = lean.play(None, None, ref['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig_eod; K._apply_unit_action = oau; K._process_market = opm
    out = {}
    for (day, idx), c in U.items():
        out.setdefault(str(day), {})[str(idx)] = dict(c)
    ph = {}
    for (day, idx), hs in HR.items():
        ph.setdefault(str(day), {})[str(idx)] = hs
    return dict(gid=ref['gid'], seat=s, team=ref['team'], m=r['r'][1 - s] - r['r'][s], units=out, nh={str(k): v for k, v in NH.items()}, pass_hours=ph)

if __name__ == '__main__':
    from eval_elite_routes import load_games
    path, refs, cand, outp, sel = sys.argv[1:6]
    want = [tuple(map(int, x.split(':'))) for x in sel.split(',')]
    R = {(r['gid'], r['seat']): r for r in map(json.loads, open(refs, encoding='utf-8')) if (r['gid'], r['seat']) in want}
    gids = {g for g, _ in want}
    games = {g['id']: g for g in load_games(path) if g['id'] in gids}
    with open(outp, 'a', encoding='utf-8') as fh:
        for k in want:
            x = play(games[k[0]], R[k], cand)
            fh.write(json.dumps(x) + '\n'); fh.flush()
            print(k, x['m'], flush=True)
