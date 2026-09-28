"""Anatomy of recorded ladder games: replay both tapes and snapshot both farms on chosen days.
usage: live_anatomy.py games.json out.jsonl [team=offhand]
Per game: for days 6, 9, 12, 16, 20, 24 (start of the day) both farms' money, land quadrants, animals by kind, crop tiles by
crop, hands hired that day; revenue by product per window (0-11, 12-15, 16-19, 20-23, 24-29) for both seats."""
import sys, os, json, collections
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, '/home/user/kaggriculture/arena'); sys.path.insert(0, '/home/user/kaggriculture/gold/harness')
DAYS = (6, 9, 12, 16, 20, 24)
WIN = ((0, 11), (12, 15), (16, 19), (20, 23), (24, 29))


def snap(farm):
    an = collections.Counter(); cr = collections.Counter()
    for row in farm['tiles']:
        for t in row:
            if isinstance(t, dict):
                if t.get('animal'):
                    an[t['animal']] += 1
                elif t.get('crop'):
                    cr[t['crop']] += 1
    return dict(money=round(farm['money']), land=len(farm['unlocked_quadrants']), an=dict(an), cr=dict(cr), hands=len(farm.get('hands') or []))


def job(t):
    import lean
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    from pinned4 import _tape
    path, team = t
    d = json.load(open(path, encoding='utf-8'))[0]
    names = d['info']['TeamNames']; P = names.index(team); O = 1 - P
    snaps = {}; rev = [collections.Counter(), collections.Counter()]; FARMS = [None, None]; STEP = [0]
    oc = K._commit_unit
    def commit(op, item, price, farm, private, market, cap=100):
        ok = oc(op, item, price, farm, private, market, cap)
        if ok and op == 'SELL' and FARMS[0] is not None:
            i = 0 if farm is FARMS[0] else 1
            day = STEP[0] // 24
            w = [k for k, (a, b) in enumerate(WIN) if a <= day <= b][0]
            rev[i]['%s_%d' % (item, w)] += price
        return ok
    opm = K._process_market
    def pm(state, env):
        st = state[0].observation.step; STEP[0] = st
        FARMS[0], FARMS[1] = state[0].observation.farms[0], state[0].observation.farms[1]
        if st % 24 == 1 and st // 24 in DAYS and st // 24 not in snaps:
            snaps[st // 24] = [snap(FARMS[P]), snap(FARMS[O])]
        return opm(state, env)
    K._commit_unit = commit; K._process_market = pm
    try:
        r = lean.play(None, None, d['info']['seed'], agent_objs=[_tape(d['acts'], 0), _tape(d['acts'], 1)])
    finally:
        K._commit_unit = oc; K._process_market = opm
    return dict(gid=d['id'], opp=names[O], meta=d.get('meta'), us=r['r'][P], them=r['r'][O], rec=[d['rewards'][P], d['rewards'][O]],
                snaps={str(k): v for k, v in snaps.items()}, rev_us=dict(rev[P]), rev_them=dict(rev[O]))


if __name__ == '__main__':
    src, out = sys.argv[1], sys.argv[2]; team = sys.argv[3] if len(sys.argv) > 3 else 'offhand'
    games = json.load(open(src, encoding='utf-8'))
    split = src + '.d'; os.makedirs(split, exist_ok=True); jobs = []
    for i, d in enumerate(games):
        f = os.path.join(split, 'a%d.json' % i)
        if not os.path.exists(f):
            json.dump([d], open(f, 'w', encoding='utf-8'))
        jobs.append((f, team))
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '6'))) as ex, open(out, 'w', encoding='utf-8') as fh:
        for r in ex.map(job, jobs):
            fh.write(json.dumps(r, ensure_ascii=False) + '\n'); fh.flush()
    print('done', len(jobs))
