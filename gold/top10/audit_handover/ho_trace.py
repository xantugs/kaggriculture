"""Handover trace: play one live game (S=288) with a candidate, and record per day around the takeover:
hands/money/shed/seeds/tile census at hour 0, the chassis's hires per day, the controller's hire search (lo, chosen h,
the h a search from 0 would choose), footprint, visits by tag, rival_sales history size at the first controller day.
usage: ho_trace.py cand gid[,gid...] out.jsonl"""
import sys, os, json, time
sys.path.insert(0, '/home/user/kaggriculture/arena')
sys.path.insert(0, '/home/user/kaggriculture/gold/harness')
from pinned4 import reference, install_pinned, _tape, _prefixed  # noqa: E402
from concurrent.futures import ProcessPoolExecutor

IDX = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gid_index.json')))


def census(farm):
    c = {}
    for row in farm['tiles']:
        for t in row:
            if t is None: k = 'empty'
            elif t == 'LOCKED': k = 'locked'
            elif isinstance(t, dict):
                k = t.get('crop') or t.get('animal') or t.get('kind')
            else: k = '?'
            c[k] = c.get(k, 0) + 1
    return c


def job(t):
    cand, gid, S = t
    import lean
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    d = json.load(open(IDX[str(gid)], encoding='utf-8'))[0]
    names = d['info']['TeamNames']; P = names.index('offhand'); O = 1 - P
    spawns, shops, _ = reference(d)
    orig = install_pinned(S // 24, O, spawns, shops)
    A = lean.load(cand)
    G = A.__globals__; C = G['GoldCtl']; GP = G['GC_P']; REP = G['_GC_REPORT']
    days = {}
    hs = []
    o_rh = C._route_and_hire

    def rh(self, visits, cash, final, day):
        lo_act = 0 if (day == GP["start"] // 24 or final) else max(0, self.last_hires - 3)
        alt = None
        if lo_act > 0:
            s0 = GP['start']; GP['start'] = day * 24
            save_u = REP['gc_unserved']; lu = getattr(self, '_last_unserved', None)
            try:
                r0 = o_rh(self, visits, cash, final, day)
                alt = r0[1]
            finally:
                GP['start'] = s0; REP['gc_unserved'] = save_u; self._last_unserved = lu
        out = o_rh(self, visits, cash, final, day)
        hs.append(dict(day=day, lo=lo_act, h=out[1], h_lo0=alt, last_hires=self.last_hires,
                       tags=''.join(sorted(v.tag for v in visits)), n_vis=len(visits),
                       n_must=sum(1 for v in visits if v.must)))
        return out
    C._route_and_hire = rh
    o_pd = C.plan_day

    def pd(self, obs):
        out = o_pd(self, obs)
        day = int(obs['step']) // 24
        dd = days.setdefault(day, {})
        dd['ctl'] = True
        dd['footprint_n'] = self.footprint_n; dd['fp_bonus'] = getattr(self, 'fp_bonus', 0)
        dd['orders0'] = self.orders0; dd['orders1'] = self.orders1
        dd['rival_sales_n'] = sum(len(v) for v in self.rival_sales.values())
        dd['reserve'] = dict(self.reserve)
        dd['routes_n'] = len(self.routes)
        return out
    C.plan_day = pd

    inner = _prefixed(A, d['acts'], P, S)
    acts = []

    def f(obs, cfg=None):
        step = int(obs['step']); day = step // 24; hour = step % 24
        me = int(obs['player']); farm = obs['farms'][me]
        dd = days.setdefault(day, {})
        if hour == 0:
            dd['money0'] = float(farm['money'])
            dd['shed0'] = {k: int(v) for k, v in dict(obs['private']['shed']).items() if int(v)}
            dd['seeds0'] = {k: int(v) for k, v in dict(obs['private']['seeds']).items() if int(v)}
            dd['census0'] = census(farm)
            dd['quads'] = list(farm['unlocked_quadrants'])
        a = inner(obs, cfg)
        if hour == 23:
            dd['hands23'] = len(farm['hands'])
        dd['maxhands'] = max(dd.get('maxhands', 0), len(farm['hands']))
        acts.append(a)
        return a
    try:
        ag = [None, None]; ag[P] = f; ag[O] = _tape(d['acts'], O)
        ms = int(os.environ['MAXSTEP']) if os.environ.get('MAXSTEP') else None
        r = lean.play(None, None, d['info']['seed'], agent_objs=ag, max_steps=ms)
    finally:
        K._end_of_day = orig
    tel = {k: v for k, v in REP.items() if isinstance(v, (int, float, str))}
    return dict(gid=gid, m=(r['r'][P] - r['r'][O]) if r['r'][P] is not None else None, start=tel.get('gc_start', GP['start']), hs=hs,
                days={k: v for k, v in days.items()}, tel=tel)


if __name__ == '__main__':
    cand = sys.argv[1]; gids = [int(x) for x in sys.argv[2].split(',')]; out = sys.argv[3]
    S = int(os.environ.get('S', '288'))
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '3'))) as ex, open(out, 'w', encoding='utf-8') as fh:
        for r in ex.map(job, [(cand, g, S) for g in gids]):
            fh.write(json.dumps(r, ensure_ascii=False) + '\n'); fh.flush()
            print(r['gid'], r['m'], r['start'], flush=True)
