"""Hourly labour profile (days 0-16): per (day, hour) and unit class, effective / move / pass-noop / unsent unit-turns,
and per hand-day the first and last hour with an effective action. Replays recorded games (elite, both tapes) or the
T7 set-up (repaired elite vs candidate, as extract.py ours).
usage (from kg/, NPROC<=4):
  hourly.py elite N_per_team        -> labour/hourly_elite.jsonl
  hourly.py ours cand.py N_per_team -> labour/hourly_ours.jsonl   (seats of ours_T7_seats.jsonl)"""
import sys, os, json, time, collections
from concurrent.futures import ProcessPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__)); OM = os.path.dirname(HERE)
sys.path.insert(0, OM)
import extract  # noqa: E402  (sets sys.path for arena / gold/harness / gold/elite)

NDAY = 17


class HL:
    def __init__(self):
        from kaggle_environments.envs.kaggriculture import kaggriculture as K
        self.K = K; self.FARMS = [None, None]; self.step = 0
        self.cnt = [collections.defaultdict(collections.Counter) for _ in (0, 1)]   # (d,h) -> Counter
        self.hand = [collections.defaultdict(lambda: [99, -1, 0]) for _ in (0, 1)]  # (d, idx) -> [first E h, last E h, nE]
        self.sent = [0, 0]

    def install(self):
        K = self.K; L = self
        self.orig = dict(interpreter=K.interpreter, _apply_unit_action=K._apply_unit_action)
        oi, oa = self.orig['interpreter'], self.orig['_apply_unit_action']

        def interp(state, env):
            o = state[0].observation
            farms = getattr(o, 'farms', None)
            if farms:
                t = int(K.get(o, 'step', 0)); L.step = t; d, h = divmod(t, 24)
                L.FARMS[0], L.FARMS[1] = farms[0], farms[1]
                if d < NDAY:
                    for p in (0, 1):
                        a = state[p].action if isinstance(state[p].action, dict) else {}
                        ha = a.get('hands', []) if isinstance(a, dict) else []
                        nh = len(farms[p]['hands'])
                        sent = min(nh, len(ha) if isinstance(ha, list) else 0)
                        C = L.cnt[p][(d, h)]
                        C['units'] += 1 + nh; C['U'] += nh - sent
            return oi(state, env)

        def act(farm, private, idx, action, bs, day, tpd, cap=100):
            p = 0 if farm is L.FARMS[0] else 1 if farm is L.FARMS[1] else None
            if p is None or day >= NDAY:
                return oa(farm, private, idx, action, bs, day, tpd, cap)
            h = L.step % 24; C = L.cnt[p][(day, h)]
            pos = K._farmer_position(farm, idx)
            if not isinstance(action, list) or not action or pos is None or action[0] == 'PASS':
                C['P'] += 1
                return oa(farm, private, idx, action, bs, day, tpd, cap)
            op = action[0]; x, y = pos[0], pos[1]
            if op in K.FARMER_MOVES:
                r = oa(farm, private, idx, action, bs, day, tpd, cap)
                p1 = K._farmer_position(farm, idx)
                C['M' if (p1[0], p1[1]) != (x, y) else 'P'] += 1
                return r
            t0 = farm['tiles'][y][x]; pre = dict(t0) if isinstance(t0, dict) else t0
            invs = private['inventories']; inv0 = dict(invs[idx]) if idx < len(invs) else {}
            shed0 = dict(private['shed'])
            r = oa(farm, private, idx, action, bs, day, tpd, cap)
            t1 = farm['tiles'][y][x]; inv1 = invs[idx] if idx < len(invs) else {}
            ch = (pre != t1) or ({k: v for k, v in inv0.items() if v} != {k: v for k, v in inv1.items() if v}) or shed0 != private['shed']
            if ch:
                C['E'] += 1
                if idx > 0:
                    H = L.hand[p][(day, idx)]; H[0] = min(H[0], h); H[1] = max(H[1], h); H[2] += 1
                else:
                    C['EF'] += 1
            else:
                C['P'] += 1
            return r

        K.interpreter = interp; K._apply_unit_action = act

    def uninstall(self):
        for k, v in self.orig.items(): setattr(self.K, k, v)

    def out(self, p):
        prof = {'%d_%d' % k: dict(v) for k, v in self.cnt[p].items()}
        hands = {'%d_%d' % k: v for k, v in self.hand[p].items()}
        return dict(prof=prof, hands=hands)


def job_elite(t):
    import lean, pinned4
    path, date, seat = t
    d = extract._load(path)
    L = HL(); L.install()
    try:
        r = lean.play(None, None, d['info']['seed'], agent_objs=[pinned4._tape(d['acts'], 0), pinned4._tape(d['acts'], 1)])
    finally:
        L.uninstall()
    names = d['info']['TeamNames']
    return dict(gid=d['id'], date=date, seat=seat, team=names[seat], role='rec', ok=[int(x) for x in r['r']] == [int(x) for x in d['rewards']], **L.out(seat))


def job_ours(t):
    import lean
    from eval_elite_routes import install_town
    from transplant import build_agent, reference_log
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    path, date, s, cand = t
    d = extract._load(path)
    ref = reference_log(d, s)
    rr = dict(hands=ref['hands'], money=ref['money'], outcomes=ref['outcomes'], shops=ref['shops'])
    orig_eod = install_town(ref['shops'])
    L = HL(); L.install()
    try:
        ag = [None, None]; ag[s] = build_agent(d['acts'], s, rr, slack_min=20); ag[1 - s] = lean.load(cand)
        r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
    finally:
        L.uninstall(); K._end_of_day = orig_eod
    names = d['info']['TeamNames']
    return dict(gid=d['id'], date=date, seat=1 - s, team='T7', opp=names[s], role='ours', ok=True, **L.out(1 - s))


if __name__ == '__main__':
    mode = sys.argv[1]
    files = {r['gid']: (os.path.join(extract.GAMES, r['file']), r['date']) for r in extract._index()}
    if mode == 'elite':
        per = int(sys.argv[2])
        seats = [json.loads(l) for l in open(os.path.join(OM, 'elite_seats.jsonl'), encoding='utf-8')]
        by = collections.defaultdict(list)
        for s in seats:
            if s['date'] >= '2026-09-23' and s['rec_ok']: by[s['team']].append(s)
        jobs = []
        for team, xs in sorted(by.items()):
            xs.sort(key=lambda s: (s['date'], s['gid']), reverse=True)
            step = max(1, len(xs) // per)
            jobs += [(files[s['gid']][0], files[s['gid']][1], s['seat']) for s in xs[::step][:per]]
        fn, outp = job_elite, os.path.join(HERE, 'hourly_elite.jsonl')
    else:
        cand = sys.argv[2]; per = int(sys.argv[3])
        seats = [json.loads(l) for l in open(os.path.join(OM, 'ours_T7_seats.jsonl'), encoding='utf-8')]
        by = collections.defaultdict(list)
        for s in seats: by[s['opp']].append(s)
        jobs = [(files[s['gid']][0], files[s['gid']][1], s['elite_seat'], cand) for team, xs in sorted(by.items()) for s in xs[:per]]
        fn, outp = job_ours, os.path.join(HERE, 'hourly_ours.jsonl')
    print(len(jobs), 'jobs', flush=True)
    t0 = time.time()
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '4'))) as ex, open(outp, 'w', encoding='utf-8') as fh:
        for i, res in enumerate(ex.map(fn, jobs)):
            fh.write(json.dumps(res, ensure_ascii=False) + '\n'); fh.flush()
            if i % 20 == 0: print(i, res['team'], res['gid'], res['ok'], 'T', round(time.time() - t0), flush=True)
    print('ALLDONE', len(jobs), round(time.time() - t0), 's', flush=True)
