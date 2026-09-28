"""Trace one game: our seat plays `cand` from step S (recorded before), the rival replays its tape (pinned town).
Dumps per step for both seats: unit positions (before the step), commands, premium inventory per unit, shed premium,
market orders, and fills. usage: tape_trace.py game.json S cand out.json [team]"""
import sys, os, json, collections
sys.path.insert(0, '/home/user/kaggriculture/gold/harness')
sys.path.insert(0, '/home/user/kaggriculture/arena')
import pinned4 as PN

PREM = ("MILK", "WOOL", "STRAWBERRY", "MELON", "EGG", "FERTILIZER", "WHEAT")


def main():
    path, S, cand, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
    team = sys.argv[5] if len(sys.argv) > 5 else 'offhand'
    import lean
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    d = json.load(open(path, encoding='utf-8'))[0]
    names = d['info']['TeamNames']; P = names.index(team); O = 1 - P
    spawns, shops, rref = PN.reference(d)
    orig = PN.install_pinned(S // 24, O, spawns, shops)
    TR = {}
    FILLS = []; STEP = [0]; FARMS = [None, None]
    oc = K._commit_unit
    def commit(op, item, price, farm, private, market, cap=100):
        ok = oc(op, item, price, farm, private, market, cap)
        if ok and FARMS[0] is not None and op == 'SELL':
            i = 0 if farm is FARMS[0] else 1
            FILLS.append((STEP[0], 0 if i == P else 1, item, price))
        return ok
    opm = K._process_market
    def pm(state, env):
        FARMS[0], FARMS[1] = state[0].observation.farms[0], state[0].observation.farms[1]
        STEP[0] = int(state[0].observation.step)
        return opm(state, env)
    K._commit_unit = commit; K._process_market = pm

    def wrap(inner, side):
        def f(obs, cfg=None):
            a = inner(obs, cfg)
            t = int(obs['step'])
            farm = obs['farms'][obs['player']]
            pos = [list(farm['farmer'])] + [list(h) for h in farm['hands']]
            inv = [{k: int(v) for k, v in i.items() if k in PREM and int(v) > 0} for i in obs['private']['inventories']]
            shed = {k: int(v) for k, v in obs['private']['shed'].items() if k in PREM and int(v) > 0}
            cmds = [a.get('farmer') or ['PASS']] + list(a.get('hands') or []) if isinstance(a, dict) else []
            TR.setdefault(t, [None, None])[side] = dict(pos=pos, cmd=cmds, inv=inv, shed=shed,
                                                        mkt=a.get('market') if isinstance(a, dict) else None)
            return a
        return f
    try:
        A = lean.load(cand)
        ag = [None, None]
        ag[P] = wrap(PN._prefixed(A, d['acts'], P, S), 0)
        ag[O] = wrap(PN._tape(d['acts'], O), 1)
        r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig; K._commit_unit = oc; K._process_market = opm
    json.dump(dict(gid=d['id'], P=P, opp=names[O], us=r['r'][P], them=r['r'][O], tr=TR, fills=FILLS), open(out, 'w'))
    print(d['id'], names[O], r['r'][P] - r['r'][O])


if __name__ == '__main__':
    main()
