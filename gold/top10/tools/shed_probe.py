"""Night-drop sizing probe: on every night our farm discards goods at the end-of-day drop, which of that day's harvests
ended in the drop (no DROP by the same unit after them), and could the tile have kept those units for tomorrow?

Same pinned world as gold/harness/pinned4.py (our seat replays its tape for steps < S). Per day with a discard:
  ovf        units discarded (carried + shed vs 100)
  room23     shed room before the drop;  lost {item: n}, lost_v $ at the evening price
  h          list of harvests after the unit's last drop of the day:
             [unit, hour, kind, item, units, cls, cost_units]
             cls: 'A' animal whose product fits max_held after tonight's production (free wait)
                  'Acap' animal that would clip at max_held tonight (cost = clipped units)
                  'O' ongoing crop that fits max_yield tonight and does not decay tomorrow (free wait)
                  'Ocap' ongoing crop clipped or decaying tomorrow
                  'G' one-time crop before its last window day, watered today (keeps, may still grow)
                  'M' one-time crop at/after its last window day (decays from hour 0 tomorrow: ~ceil(h/2) units)
                  'X' anything else (thirsty one-time crop, day 28-29, ...)
  cf         COLLECT_FERTILIZER units after the unit's last drop
usage: shed_probe.py games.json S cand out.jsonl [team] (env NPROC, PIN_GIDS)"""
import sys, os, json, time, collections, traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
HERE = '/home/user/kaggriculture/moon'
sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
sys.path.insert(0, os.path.join(HERE, '..', 'gold', 'harness'))
from pinned4 import reference, install_pinned, _tape, _prefixed  # noqa: E402


def job(t):
    import lean
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    path, idx, team, cand, S = t
    t0 = time.time()
    with open(path, encoding='utf-8') as fh:
        d = json.load(fh)[idx]
    names = d['info']['TeamNames']; P = names.index(team); O = 1 - P
    st = dict(farm=None, priv=None, mkt=None, day=0, hour=0)
    days = collections.defaultdict(lambda: dict(ev=[], drops=collections.Counter()))
    o_apply = K._apply_unit_action; o_drop = K._drop_inventories_to_shed; o_int = K.interpreter; o_eod = K._end_of_day
    px = {}

    def interp(state, env):
        obs0 = state[0].observation
        s_ = int(obs0.get('step', 0)); st['day'] = s_ // 24; st['hour'] = s_ % 24
        out = o_int(state, env)
        if st['farm'] is None and obs0.get('farms'):
            st['farm'] = obs0.farms[P]; st['priv'] = state[P].observation.private; st['mkt'] = obs0.market
        return out

    def apply(farm, private, idx_, action, bs, day, tpd, cap=100):
        if farm is not st['farm'] or not isinstance(action, list) or not action:
            return o_apply(farm, private, idx_, action, bs, day, tpd, cap)
        op = action[0]
        dd = days[day]
        if op == 'DROP':
            dd['ev'].append((idx_, st['hour'], 'DROP'))
            return o_apply(farm, private, idx_, action, bs, day, tpd, cap)
        if op not in ('HARVEST', 'COLLECT_FERTILIZER'):
            return o_apply(farm, private, idx_, action, bs, day, tpd, cap)
        pos = farm['farmer'] if idx_ == 0 else (farm['hands'][idx_ - 1] if idx_ - 1 < len(farm['hands']) else None)
        if pos is None:
            return o_apply(farm, private, idx_, action, bs, day, tpd, cap)
        t = farm['tiles'][pos[1]][pos[0]]
        rec = None
        if isinstance(t, dict):
            if op == 'COLLECT_FERTILIZER' and 'animal' in t and t.get('fertilizer_available'):
                rec = (idx_, st['hour'], 'CF', 'FERTILIZER', 1, 'F', 0)
            elif op == 'HARVEST' and int(t.get('yield_units', 0) or 0) > 0:
                y = int(t['yield_units'])
                if 'animal' in t:
                    a = K.ANIMALS[t['animal']]
                    dsf = day + 1 - t['placed_day'] - a['first_yield_day']
                    add = 0
                    if dsf >= 0 and dsf % a['interval'] == 0:
                        add = 1 + (int(t.get('pending_care_bonus', 0) or 0) if t.get('fed_today') else 0)
                    clip = max(0, y + add - a['max_held'])
                    rec = (idx_, st['hour'], t['animal'], a['product'], y, 'A' if clip == 0 else 'Acap', clip)
                elif t.get('kind') == 'PLANT':
                    cd = K.CROPS[t['crop']]; age = day - t['planted_day']
                    if age >= cd['first_yield_day']:
                        if cd['ongoing']:
                            dsf = day + 1 - t['planted_day'] - cd['first_yield_day']
                            add = 0
                            if dsf >= 0 and dsf % cd['interval'] == 0 and dsf // cd['interval'] + 1 <= cd['max_yield']:
                                add = 2 if (t.get('watered_today') and t.get('fertilized_until_day', -1) >= day) else 1
                            clip = max(0, y + add - cd['max_yield'])
                            mls = t['max_lifespan_step']
                            fin = dsf >= 0 and dsf % cd['interval'] == 0 and dsf // cd['interval'] + 1 == cd['max_yield']
                            dec = (mls >= 0 and mls < (day + 2) * tpd)
                            ok = clip == 0 and not dec and t.get('watered_today') and day <= 27
                            rec = (idx_, st['hour'], t['crop'], t['crop'], y, 'O' if ok else 'Ocap', clip)
                        else:
                            watered = t.get('watered_today') or int(t.get('consecutive_unwatered', 1)) == 0
                            if day >= 28:
                                cls = 'X'
                            elif age < cd['max_yield_day'] and t.get('watered_today'):
                                cls = 'G'
                            elif age >= cd['max_yield_day'] and watered:
                                cls = 'M'
                            else:
                                cls = 'X'
                            rec = (idx_, st['hour'], t['crop'], t['crop'], y, cls, 0)
        out = o_apply(farm, private, idx_, action, bs, day, tpd, cap)
        if rec is not None:
            days[day]['ev'].append(rec)
        return out

    def drop(private, capacity):
        if private is not st['priv']:
            return o_drop(private, capacity)
        day = st['day']; dd = days[day]
        shed = private['shed']; shed0 = dict(shed)
        room = max(0, capacity - sum(shed.values()))
        tot = collections.Counter()
        for inv in private['inventories']:
            for k, v in inv.items():
                if v > 0:
                    tot[k] += v
        out = o_drop(private, capacity)
        lost = {k: n - (shed.get(k, 0) - shed0.get(k, 0)) for k, n in tot.items()}
        lost = {k: v for k, v in lost.items() if v > 0}
        dd['room23'] = room; dd['carried'] = sum(tot.values()); dd['lost'] = lost
        dd['px'] = {k: int(st['mkt']['prices'][k]) for k in K.PRODUCTS}
        dd['lost_v'] = sum(v * dd['px'].get(k, 0) for k, v in lost.items())
        return out

    K._apply_unit_action = apply; K._drop_inventories_to_shed = drop; K.interpreter = interp
    try:
        spawns, shops, rref = reference(d)
        orig = install_pinned(S // 24, O, spawns, shops)
        try:
            A = lean.load(cand)
            ag = [None, None]
            ag[P] = _prefixed(A, d['acts'], P, S)
            ag[O] = _tape(d['acts'], O)
            r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
        finally:
            K._end_of_day = orig
    except Exception:
        return dict(gid=d['id'], opp=names[O], cand=cand, S=S, m=None, exc=traceback.format_exc()[-1500:])
    finally:
        K._apply_unit_action = o_apply; K._drop_inventories_to_shed = o_drop; K.interpreter = o_int
    nights = {}
    for day, dd in sorted(days.items()):
        if not dd.get('lost'):
            continue
        last_drop = {}
        for e in dd['ev']:
            if e[2] == 'DROP':
                last_drop[e[0]] = max(last_drop.get(e[0], -1), e[1])
        hs = [list(e) for e in dd['ev'] if e[2] != 'DROP' and e[1] > last_drop.get(e[0], -1)]
        nights[str(day)] = dict(ovf=sum(dd['lost'].values()), room23=dd['room23'], carried=dd['carried'], lost=dd['lost'],
                                lost_v=dd['lost_v'], px=dd['px'], h=hs)
    m = (r['r'][P] - r['r'][O]) if r['r'][P] is not None and r['r'][O] is not None else None
    return dict(gid=d['id'], opp=names[O], cand=cand, S=S, m=m, us=r['r'][P], them=r['r'][O], tmax=r['tmax'][P],
                err=r['err'], nights=nights, wall=round(time.time() - t0, 1))


if __name__ == '__main__':
    f = sys.argv[1]; S = int(sys.argv[2]); cand = sys.argv[3]; out = sys.argv[4]
    team = sys.argv[5] if len(sys.argv) > 5 else 'offhand'
    want = set(int(x) for x in open(os.environ["PIN_GIDS"]).read().split()) if os.environ.get("PIN_GIDS") else None
    split = f + '.d'
    games = []
    corpus = json.load(open(f, encoding='utf-8'))
    for i, d in enumerate(corpus):
        if team in d['info']['TeamNames'] and (want is None or d['id'] in want):
            one = os.path.join(split, '%d.json' % i)
            if not os.path.exists(one):
                os.makedirs(split, exist_ok=True)
                json.dump([d], open(one, 'w', encoding='utf-8'))
            games.append((one, d['id']))
    del corpus
    import gc; gc.collect()
    done = set()
    if os.path.exists(out):
        for line in open(out, encoding='utf-8'):
            try:
                rr = json.loads(line)
                if rr.get('m') is not None:
                    done.add(rr['gid'])
            except ValueError:
                pass
    jobs = [(p, 0, team, cand, S) for p, g in games if g not in done]
    print('games %d done %d jobs %d' % (len(games), len(done), len(jobs)), flush=True)
    t0 = time.time()
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '3'))) as ex, open(out, 'a', encoding='utf-8') as fh:
        futs = [ex.submit(job, j) for j in jobs]
        for k, fu in enumerate(as_completed(futs)):
            rr = fu.result()
            fh.write(json.dumps(rr, ensure_ascii=False) + '\n'); fh.flush()
            print(rr['gid'], rr['opp'], rr['m'], sum(n['ovf'] for n in rr.get('nights', {}).values()), '[%d/%d %.0fs]' % (k + 1, len(jobs), time.time() - t0), flush=True)
