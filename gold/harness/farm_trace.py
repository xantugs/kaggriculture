"""Per-day farm state of both players in a pinned game (crop/animal counts, hands, money, shed) at hour 12.
usage: farm_trace.py cand.py gid [S] [day_from]"""
import sys, os, json, collections
sys.path.insert(0, '/home/user/kaggriculture/gold/harness'); sys.path.insert(0, '/home/user/kaggriculture/arena')
import pinned4, lean
from kaggle_environments.envs.kaggriculture import kaggriculture as K

def counts(farm):
    c = collections.Counter()
    for row in farm['tiles']:
        for t in row:
            if t is None: c['free'] += 1
            elif t == 'LOCKED': c['locked'] += 1
            elif isinstance(t, dict):
                if t.get('kind') == 'WEED': c['weed'] += 1
                elif t.get('crop'): c[t['crop'][:4] + ('*' if (t.get('yield_units') or 0) > 0 else '')] += 1
                elif t.get('animal'): c[t['animal'][:4]] += 1
                else: c[str(t.get('kind'))[:6]] += 1
    return c

def main():
    cand, gid = sys.argv[1], int(sys.argv[2]); S = int(sys.argv[3]) if len(sys.argv) > 3 else 288; d0 = int(sys.argv[4]) if len(sys.argv) > 4 else 20
    for path in ['moon/strong2800.json', 'moon/strong_new.json']:
        games = json.load(open(path)); d = next((g for g in games if g['id'] == gid), None)
        if d: break
    names = d['info']['TeamNames']; P = names.index('offhand'); O = 1 - P
    spawns, shops, rref = pinned4.reference(d)
    orig = pinned4.install_pinned(S // 24, O, spawns, shops)
    snaps = {}
    opm = K._process_market
    def pm(state, env):
        st = state[0].observation.step
        if st % 24 == 12 or st == 718:
            obs = state[0].observation
            snaps[st] = [(counts(obs.farms[i]), len(obs.farms[i]['hands']), int(obs.farms[i]['money']),
                          sum(int(v) for v in state[i].observation.private['shed'].values()) if hasattr(state[i].observation, 'private') else -1) for i in (0, 1)]
        return opm(state, env)
    K._process_market = pm
    try:
        A = lean.load(cand); ag = [None, None]
        ag[P] = pinned4._prefixed(A, d['acts'], P, S); ag[O] = pinned4._tape(d['acts'], O)
        r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig; K._process_market = opm
    print('gid', gid, 'opp', names[O], 'result us %.0f them %.0f margin %+.0f' % (r['r'][P], r['r'][O], r['r'][P] - r['r'][O]))
    for st in sorted(snaps):
        if st // 24 < d0: continue
        us, them = snaps[st][P], snaps[st][O]
        print('day %2d h%2d  US   hands %d money %6d shed %3d  %s' % (st // 24, st % 24, us[1], us[2], us[3], dict(sorted(us[0].items()))))
        print('           THEM hands %d money %6d shed %3d  %s' % (them[1], them[2], them[3], dict(sorted(them[0].items()))))
if __name__ == '__main__':
    main()
