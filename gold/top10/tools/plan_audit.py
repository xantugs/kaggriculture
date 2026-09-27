"""Where does the controller drop work it planned? Instrumented S=0 replay of the live games (same world as scan.py).

Per controller day (hooks on the lean module's GoldCtl class, which leave play unchanged):
  un   visits the day's routing left unserved   [[tag, ops, value, must, x, y, rot]]
  pop  visits the final _plan_stops removed      (same fields; shed stops that pop optional visits after them)
  trim visits _trim_queue removed during the day (same fields)
  rot = 1 when the visit is a HARVEST of a finished ongoing plant on its last day before decay (everything rots next day)
usage: plan_audit.py games.json.d S cand out.jsonl [team]   (env NPROC, PIN_GIDS)  resumable by gid"""
import sys, os, json, time, collections, traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
HERE = '/home/user/kaggriculture/moon'
sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
sys.path.insert(0, os.path.join(HERE, '..', 'gold', 'harness'))
from pinned4 import reference, install_pinned, _tape, _prefixed  # noqa: E402


def _rec(v, tiles, day):
    ops = [a[0] for a in v.acts]
    x, y = int(v.pos[0]), int(v.pos[1])
    rot = 0
    try:
        t = tiles[y][x]
        if isinstance(t, dict) and t.get('kind') == 'PLANT' and 'HARVEST' in ops and int(t.get('max_lifespan_step', -1)) >= 0:
            if int(t['max_lifespan_step']) // 24 <= day + 1 and int(t.get('yield_units', 0) or 0) > 0:
                rot = 1
    except Exception:
        pass
    return [v.tag, '+'.join(o[:2] for o in ops), round(float(v.value), 1), int(bool(v.must)), x, y, rot]


def job(t):
    import lean
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    path, team, cand, S = t
    t0 = time.time()
    d = json.load(open(path, encoding='utf-8'))[0]
    names = d['info']['TeamNames']; P = names.index(team); O = 1 - P
    days = collections.defaultdict(lambda: dict(un=[], pop=[], trim=[]))
    try:
        spawns, shops, rref = reference(d)
        orig = install_pinned(S // 24, O, spawns, shops)
        A = lean.load(cand); G = A.__globals__; C = G['GoldCtl']
        o_rh = C._route_and_hire; o_ps = C._plan_stops; o_tq = C._trim_queue

        def rh(self, visits, cash, final, day):
            out = o_rh(self, visits, cash, final, day)
            try:
                inr = {id(v) for r in out[0] for v in r}
                tl = getattr(self, 'tiles_today', None)
                days[day]['un'] = [_rec(v, tl, day) for v in visits if id(v) not in inr]
            except Exception:
                days[day]['err'] = traceback.format_exc()[-300:]
            return out

        def ps(self, routes, spawns, caps_in=None):
            final = routes is getattr(self, 'routes', None)
            before = [v for r in routes for v in r] if final else None
            out = o_ps(self, routes, spawns, caps_in)
            if final:
                try:
                    now = {id(v) for r in routes for v in r}
                    day = getattr(self, 'day', -1); tl = getattr(self, 'tiles_today', None)
                    days[day]['pop'] = [_rec(v, tl, day) for v in before if id(v) not in now]
                except Exception:
                    pass
            return out

        def tq(self, q, pos, turns_left):
            before = [v for _t, _a, v in q if v is not None]
            out = o_tq(self, q, pos, turns_left)
            try:
                now = {id(v) for _t, _a, v in q if v is not None}
                gone = []
                for v in before:
                    if id(v) not in now and all(id(v) != id(g) for g in gone):
                        gone.append(v)
                if gone:
                    day = getattr(self, 'day', -1); tl = getattr(self, 'tiles_today', None)
                    days[day]['trim'] += [_rec(v, tl, day) for v in gone]
            except Exception:
                pass
            return out
        C._route_and_hire = rh; C._plan_stops = ps; C._trim_queue = tq
        try:
            ag = [None, None]
            ag[P] = _prefixed(A, d['acts'], P, S)
            ag[O] = _tape(d['acts'], O)
            r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
        finally:
            C._route_and_hire = o_rh; C._plan_stops = o_ps; C._trim_queue = o_tq
            K._end_of_day = orig
        m = (r['r'][P] - r['r'][O]) if r['r'][P] is not None and r['r'][O] is not None else None
        return dict(gid=d['id'], opp=names[O], cand=cand, S=S, m=m, days={str(k): v for k, v in sorted(days.items())},
                    err=r['err'], tmax=r['tmax'][P], wall=round(time.time() - t0, 1))
    except Exception:
        return dict(gid=d['id'], opp=names[O], cand=cand, S=S, m=None, exc=traceback.format_exc()[-1500:],
                    wall=round(time.time() - t0, 1))


if __name__ == '__main__':
    split, S, cand, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
    team = sys.argv[5] if len(sys.argv) > 5 else 'offhand'
    want = set(int(x) for x in open(os.environ['PIN_GIDS']).read().split()) if os.environ.get('PIN_GIDS') else None
    done = set()
    if os.path.exists(out):
        for line in open(out, encoding='utf-8'):
            try:
                r = json.loads(line)
                if r.get('m') is not None:
                    done.add(r['gid'])
            except ValueError:
                pass
    jobs = []
    for f in sorted(os.listdir(split), key=lambda s: int(s.split('.')[0])):
        p = os.path.join(split, f)
        with open(p, encoding='utf-8') as fh:
            head = fh.read(400)
        gid = int(head.split('"id":')[1].split(',')[0])
        if (want is None or gid in want) and gid not in done:
            jobs.append((p, team, cand, S))
    print('jobs', len(jobs), 'done', len(done), flush=True)
    t0 = time.time(); n = 0
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '3'))) as ex, open(out, 'a', encoding='utf-8') as fh:
        futs = [ex.submit(job, j) for j in jobs]
        for fu in as_completed(futs):
            r = fu.result(); n += 1
            fh.write(json.dumps(r, ensure_ascii=False) + '\n'); fh.flush()
            print(r['gid'], r.get('opp'), 'm', r.get('m'), 'EXC' if r.get('exc') else '',
                  '[%d/%d %.0fs]' % (n, len(jobs), time.time() - t0), flush=True)
