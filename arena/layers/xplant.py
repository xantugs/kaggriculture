

# =====================================================================================
# XPLANT: from day 15, replay a recorded day-15+ action stream of a stronger agent built on
# the same chassis, when our farm at the switch step is identical to theirs.
# =====================================================================================
_XP_LIB = __XPLIB__
_XP_CFG = __XPCFG__
_XP_STATE = {}
_XP_REPORT = dict(matched=0, used=0, mism=0, errors=0)


def _xp_key(tiles):
    out = []
    for row in tiles:
        for t in row:
            if t is None: out.append('.')
            elif t == 'LOCKED': out.append('#')
            elif isinstance(t, dict):
                if t.get('kind') == 'PLANT': out.append(t['crop'][:2] + str(t['planted_day']))
                elif t.get('animal'): out.append(t['animal'][:2])
                else: out.append(t.get('kind', '?')[:2])
            else: out.append('?')
    return '|'.join(out)


_XP_PARENT = agent
def agent(observation, configuration=None):
    action = _XP_PARENT(observation, configuration)
    try:
        step = int(observation['step']); player = int(observation['player'])
        st = _XP_STATE.get(player)
        if st is None or step <= st.get('step', -1):
            st = _XP_STATE[player] = {'step': -1, 'entry': None}
            for k in _XP_REPORT: _XP_REPORT[k] = 0
        st['step'] = step
        S = _XP_CFG['switch']
        if step == S:
            key = _xp_key(observation['farms'][player]['tiles'])
            best = None
            force = _XP_CFG.get('force')
            for e in _XP_LIB:
                if force is not None:
                    if [e['id'], e['team']] == list(force): best = e
                elif e['key'] == key and (best is None or e['score'] > best['score']):
                    best = e
            st['entry'] = best
            if best is not None:
                _XP_REPORT['matched'] += 1; _XP_REPORT['keyok'] = int(best['key'] == key)
        e = st.get('entry')
        if e is None or step < S or step >= _XP_CFG['stop']:
            return action
        rec = e['acts'][step - S]
        if not isinstance(rec, dict):
            return action
        _XP_REPORT['used'] += 1
        out = {'farmer': rec.get('farmer') or ['PASS'], 'hands': list(rec.get('hands') or []), 'market': [list(o) for o in (rec.get('market') or []) if o]}
        farm = observation['farms'][player]; private = observation['private']
        n = len(farm['hands'])
        if len(out['hands']) != n:
            _XP_REPORT['mism'] += 1
            out['hands'] = (out['hands'] + [['PASS']] * n)[:n]
        day, hour = divmod(step, 24)
        # repair 1: at day start, compare our shed WHEAT/FERTILIZER to the recording's; cover a deficit by
        # trimming the recording's own sell orders first, then buying the rest (as soon as an order slot is free)
        if _XP_CFG.get('rep_wheat', 1):
            if hour == 0 and st.get('wday') != day:
                st['wday'] = day; st['wdef'] = {}
                for item, rk in (('WHEAT', 'wheat'), ('FERTILIZER', 'fert')):
                    rec_n = e.get(rk, {}).get(str(day))
                    if rec_n is None: continue
                    dfc = int(rec_n) + (_XP_CFG['wheat_margin'] if item == 'WHEAT' else 0) - int(private['shed'].get(item, 0))
                    if dfc > 0: st['wdef'][item] = dfc
            for item in list(st.get('wdef', {})):
                dfc = st['wdef'][item]
                for o in out['market']:
                    if dfc > 0 and o and o[0] == 'SELL' and o[1] == item:
                        cut = min(dfc, int(o[2])); o[2] = int(o[2]) - cut; dfc -= cut
                out['market'] = [o for o in out['market'] if not (o and o[0] == 'SELL' and int(o[2]) <= 0)]
                if dfc > 0 and len(out['market']) < 10:
                    out['market'].append(['BUY_PRODUCT', item, dfc])
                    _XP_REPORT['bought_' + item[:4]] = _XP_REPORT.get('bought_' + item[:4], 0) + dfc
                    dfc = 0
                if dfc > 0: st['wdef'][item] = dfc
                else: del st['wdef'][item]
        # repair 2: a rescue hand for animals/plants the recording does not service today but that
        # would be lost tonight (feeding/watering parity differs from the recording's game)
        if _XP_CFG.get('rep_rescue', 1) and st.get('rday') != day:
            st['rday'] = day; st['rescue'] = None; st['rescue_pending'] = None; st['rescue_done'] = set()
            fed = set(tuple(p) for p in e.get('feed', {}).get(str(day), []))
            wat = set(tuple(p) for p in e.get('water', {}).get(str(day), []))
            behind_ok = set(tuple(p) for p in e.get('u1', {}).get(str(day), []))
            todo = []
            for y in range(10):
                for x in range(10):
                    t = farm['tiles'][y][x]
                    if (x, y) in behind_ok:
                        continue
                    if isinstance(t, dict) and t.get('animal') and int(t.get('consecutive_unfed', 0)) >= 1 and (x, y) not in fed:
                        todo.append(((x, y), 'FEED'))
                    elif isinstance(t, dict) and t.get('kind') == 'PLANT' and int(t.get('consecutive_unwatered', 0)) >= 1 and (x, y) not in wat:
                        todo.append(((x, y), 'WATER'))
            st['rescue_todo'] = todo
            if todo: _XP_REPORT['rescue_days'] = _XP_REPORT.get('rescue_days', 0) + 1
        if st.get('rescue_todo') and st.get('rescue') is None and st['rescue_pending'] is None and hour >= 2 and len(out['market']) < 10 and not any(o and o[0] == 'HIRE' for o in out['market']):
            # hire after the recording's own hires of the day
            later = any(o and o[0] == 'HIRE' for a in e['acts'][step - S + 1:min(len(e['acts']), (day + 1) * 24 - S)] if isinstance(a, dict) for o in (a.get('market') or []))
            if not later:
                out['market'].append(['HIRE']); st['rescue_pending'] = n + 1
                _XP_REPORT['rescue_hires'] = _XP_REPORT.get('rescue_hires', 0) + 1
        elif st.get('rescue_pending') is not None and n >= st['rescue_pending']:
            st['rescue'] = st['rescue_pending']; st['rescue_pending'] = None
        r = st.get('rescue')
        if r is not None and r <= n:
            posr = tuple(farm['hands'][r - 1]); inv = (private.get('inventories') or [{}] * (r + 1))[r] if r < len(private.get('inventories') or []) else {}
            todo = [(p, op) for p, op in st['rescue_todo'] if p not in st['rescue_done']]
            cmd = ['PASS']
            need_w = sum(1 for p, op in todo if op == 'FEED')
            if need_w and int(inv.get('WHEAT', 0)) <= 0:
                acc = min(((4, 4), (5, 4), (4, 5), (5, 5)), key=lambda a: abs(a[0] - posr[0]) + abs(a[1] - posr[1]))
                cmd = ['PICKUP', 'WHEAT', need_w] if posr == acc else (['EAST' if acc[0] > posr[0] else 'WEST'] if acc[0] != posr[0] else ['SOUTH' if acc[1] > posr[1] else 'NORTH'])
            elif todo:
                p, op = min(todo, key=lambda v: abs(v[0][0] - posr[0]) + abs(v[0][1] - posr[1]))
                t = farm['tiles'][p[1]][p[0]]
                done = (op == 'FEED' and isinstance(t, dict) and t.get('fed_today')) or (op == 'WATER' and isinstance(t, dict) and t.get('watered_today')) or not isinstance(t, dict)
                if done:
                    st['rescue_done'].add(p)
                elif posr == p:
                    cmd = [op]; st['rescue_done'].add(p); _XP_REPORT['rescues'] = _XP_REPORT.get('rescues', 0) + 1
                else:
                    cmd = ['EAST' if p[0] > posr[0] else 'WEST'] if p[0] != posr[0] else ['SOUTH' if p[1] > posr[1] else 'NORTH']
            out['hands'][r - 1] = cmd
        return out
    except Exception:
        _XP_REPORT['errors'] += 1
    return action
agent.telemetry = _XP_REPORT
agent = globals().pop('agent')
globals().pop('kaggle_submission_agent', None)
kaggle_submission_agent = agent
