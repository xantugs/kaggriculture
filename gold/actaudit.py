"""Action audit, days >= D0, both seats (decoupled, closed loop), averaged over seeds.
Counts effective actions by kind/crop, no-ops, moves, and one-time crop cycles (plant->harvest age, yield).
usage: actaudit.py A.py B.py seeds [D0]"""
import sys, json, copy, collections, multiprocessing as mp
sys.path.insert(0, '/home/user/kaggriculture/arena')


def run(args):
    A0, B0, seed, D0, D1 = args
    import lean, decouple
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    decouple.install(0)
    A = lean.load(A0); B = lean.load(B0)
    C = [collections.Counter(), collections.Counter()]
    PRIVS = [None, None]
    oa = K._apply_unit_action

    def apply(farm, private, idx, action, bs, day, tpd, cap=100):
        if PRIVS[0] is None or day < D0 or day > D1:
            return oa(farm, private, idx, action, bs, day, tpd, cap)
        i = 0 if private is PRIVS[0] else 1
        c = C[i]
        op = action[0] if isinstance(action, list) and action else 'NONE'
        pos = K._farmer_position(farm, idx)
        tile0 = None
        if pos is not None:
            tile0 = copy.deepcopy(farm['tiles'][pos[1]][pos[0]])
        inv = K._farmer_inventory(private, idx)
        inv0 = dict(inv); shed0 = dict(private['shed']); seeds0 = dict(private['seeds'])
        oa(farm, private, idx, action, bs, day, tpd, cap)
        tile1 = farm['tiles'][pos[1]][pos[0]] if pos is not None else None
        changed = (tile0 != tile1) or (inv0 != dict(inv)) or (shed0 != dict(private['shed'])) or (seeds0 != dict(private['seeds']))
        if op in ('NORTH', 'SOUTH', 'EAST', 'WEST'):
            c['move'] += 1; return
        if op == 'PASS':
            c['pass'] += 1; return
        if not changed:
            c['noop_' + op] += 1; return
        crop = tile0.get('crop') if isinstance(tile0, dict) else None
        if op == 'PLANT':
            c['plant_' + action[1]] += 1
        elif op == 'HARVEST' and isinstance(tile0, dict):
            if crop:
                c['harv_' + crop] += 1
                c['units_' + crop] += tile0['yield_units']
                if not K.CROPS[crop]['ongoing']:
                    age = day - tile0['planted_day']
                    c['age_%s_%d' % (crop, age)] += 1
            else:
                c['harv_' + tile0['animal']] += 1; c['units_' + tile0['animal']] += tile0['yield_units']
        elif op in ('WATER', 'FERTILIZE') and crop:
            c[op.lower() + '_' + crop] += 1
        else:
            c[op.lower()] += 1
    K._apply_unit_action = apply
    om = K._process_market

    def pm(state, env):
        PRIVS[0], PRIVS[1] = state[0].observation.private, state[1].observation.private
        return om(state, env)
    K._process_market = pm
    lean.play(None, None, seed, agent_objs=[A, B])
    return [dict(C[0]), dict(C[1])]


if __name__ == '__main__':
    A0, B0 = sys.argv[1], sys.argv[2]
    s = sys.argv[3]
    seeds = list(range(int(s.split('-')[0]), int(s.split('-')[1]) + 1)) if '-' in s else [int(x) for x in s.split(',')]
    D0 = int(sys.argv[4]) if len(sys.argv) > 4 else 12
    D1 = int(sys.argv[5]) if len(sys.argv) > 5 else 29
    with mp.Pool(4) as p:
        res = p.map(run, [(A0, B0, sd, D0, D1) for sd in seeds])
    T = [collections.Counter(), collections.Counter()]
    for a, b in res:
        T[0].update(a); T[1].update(b)
    n = len(res)
    keys = sorted(set(T[0]) | set(T[1]))
    print('%-22s %8s %8s %8s' % ('key', 'A', 'B', 'A-B'))
    for k in keys:
        a, b = T[0][k] / n, T[1][k] / n
        if max(abs(a), abs(b)) >= 0.5:
            print('%-22s %8.1f %8.1f %8.1f' % (k, a, b, a - b))
