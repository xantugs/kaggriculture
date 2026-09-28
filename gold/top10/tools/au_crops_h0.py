"""au_crops audit: hour-0 hire displacement. Per controller day log n0_hires (routes planned with a 23-turn cap), hires
planned, hires actually ordered at hour 0 (h0), due lots at hour 0, and at hour 23 the units whose queue is unfinished
(unit index, items left), plus plants that die of thirst at age 0 and the unit/hour that planted them.
usage: au_crops_h0.py cand S gid[,gid...] out.jsonl      (env NPROC; corpus gold/top10/gates/live191.json.d)"""
import sys, os, json
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, '/home/user/kaggriculture/arena')
sys.path.insert(0, '/home/user/kaggriculture/gold/harness')
from pinned4 import reference, install_pinned, _tape, _prefixed  # noqa: E402

SPLIT = '/home/user/kaggriculture/gold/top10/gates/live191.json.d'


def job(t):
    path, cand, S = t
    import lean
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    d = json.load(open(path, encoding='utf-8'))[0]
    names = d['info']['TeamNames']; P = names.index('offhand'); O = 1 - P
    spawns, shops, _ = reference(d)
    orig = install_pinned(S // 24, O, spawns, shops)
    A = lean.load(cand)
    G = A.__globals__; C = G['GoldCtl']
    days = {}; FARM = [None]; STEP = [0]; planted = {}
    o_m0 = C._market0

    def m0(self, obs, shed, carried, hour, day):
        out = o_m0(self, obs, shed, carried, hour, day)
        if hour == 0:
            h0 = sum(1 for o in out if o and o[0] == 'HIRE')
            dv = days.setdefault(day, {})
            dv.update(n0=self.n0_hires, hp=self.hires_planned, h0=h0, due=sum(1 for o in out if o and o[0] == 'SELL') - len(self.sell0),
                      nfix=len(self.orders0))
        return out
    C._market0 = m0
    o_act = C.act

    def act(self, obs):
        out = o_act(self, obs)
        if int(obs['hour']) == 23:
            left = {u: [(tuple(tg), a[0]) for tg, a, _v in q if a[0] != 'DROP'] for u, q in (self.queues or {}).items() if q}
            left = {u: v for u, v in left.items() if v}
            if left:
                days.setdefault(int(obs['day']), {})['left'] = {str(u): v for u, v in left.items()}
        return out
    C.act = act
    o_apply = K._apply_unit_action; o_rp = K._daily_refresh_plants; o_int = K.interpreter

    def interp(state, env):
        obs0 = state[0].observation
        if FARM[0] is None and obs0.get('farms'):
            FARM[0] = obs0.farms[P]
        STEP[0] = int(obs0.get('step', 0))
        return o_int(state, env)

    def apply(farm, private, idx, action, bs, day, tpd, cap=100):
        r = o_apply(farm, private, idx, action, bs, day, tpd, cap)
        if farm is FARM[0] and isinstance(action, list) and action and action[0] == 'PLANT':
            pos = farm['farmer'] if idx == 0 else farm['hands'][idx - 1]
            planted[(pos[0], pos[1], day)] = (idx, STEP[0] % 24)
        return r

    def rp(farm, day, tpd):
        if farm is FARM[0]:
            for y, row in enumerate(farm['tiles']):
                for x, t in enumerate(row):
                    if isinstance(t, dict) and t.get('kind') == 'PLANT' and not t['watered_today'] and t['consecutive_unwatered'] + 1 >= 2:
                        days.setdefault(day, {}).setdefault('thirst', []).append(
                            [t['crop'], day - t['planted_day'], x, y, planted.get((x, y, t['planted_day']))])
        return o_rp(farm, day, tpd)
    K._apply_unit_action = apply; K._daily_refresh_plants = rp; K.interpreter = interp
    try:
        ag = [None, None]
        ag[P] = _prefixed(A, d['acts'], P, S)
        ag[O] = _tape(d['acts'], O)
        r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig; K._apply_unit_action = o_apply; K._daily_refresh_plants = o_rp; K.interpreter = o_int
    return dict(gid=d['id'], opp=names[O], m=r['r'][P] - r['r'][O], days={str(k): v for k, v in sorted(days.items())})


def main():
    cand, S, gids, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
    idx = {}
    for f in os.listdir(SPLIT):
        with open(os.path.join(SPLIT, f), encoding='utf-8') as fh:
            head = fh.read(400)
        idx[int(head.split('"id":')[1].split(',')[0])] = os.path.join(SPLIT, f)
    want = list(idx) if gids == 'all' else [int(x) for x in gids.split(',')]
    jobs = [(idx[g], cand, S) for g in want if g in idx]
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '2'))) as ex, open(out, 'w', encoding='utf-8') as fh:
        for r in ex.map(job, jobs):
            fh.write(json.dumps(r, ensure_ascii=False) + '\n'); fh.flush()
            n = sum(1 for d in r['days'].values() if d.get('h0') is not None and d['h0'] < min(d['n0'], d['hp']))
            print(r['gid'], r['opp'], 'm', r['m'], 'displaced days', n, flush=True)


if __name__ == '__main__':
    main()
