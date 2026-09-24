

# =====================================================================================
# Wheat/carrot fertilizer helper. The route waters every wheat plot through its yield window
# (ages 2-4) but fertilizes few of them; a fertilized window gives 6 wheat instead of 4. Each
# morning, after all native and chassis hires, we hire one helper when enough plots are in (or
# entering) their window unfertilized, load collected fertilizer the route won't need, and
# fertilize them nearest-first. The helper never touches anything else.
# =====================================================================================
_WF_CFG = __WFCFG__
_WF_STATE = {}
_WF_REPORT = dict(helpers=0, applied=0, loaded=0, bought=0, skipped_days=0, errors=0)
_WF_ACCESS = ((4, 4), (5, 4), (4, 5), (5, 5))


def _wf_targets(farm, day, hour):
    out = []
    for y in range(10):
        for x in range(10):
            t = farm['tiles'][y][x]
            if not (isinstance(t, dict) and t.get('kind') == 'PLANT' and t.get('crop') in _WF_CFG['crops']):
                continue
            age = day - int(t['planted_day']); fu = int(t.get('fertilized_until_day', -1))
            if fu >= day:
                continue
            crop = t['crop']
            first, last = _WF_CFG['crops'][crop]
            # still two watered window days ahead of the fertilizer: age <= last-1 (today counts only if unwatered)
            if age < first - 1 or age > last - 1:
                continue
            if age == last - 1 and t.get('watered_today'):
                continue
            if age == first - 1 and hour < 12:
                # tomorrow's window start is covered by today's application (day..day+2)
                pass
            out.append((x, y))
    return out


def _wf_native_pickups(native, day, hour):
    try:
        planned = _v219_native_day(native, day)
    except Exception:
        return 0
    n = 0
    for a in planned[hour:]:
        for c in [a.get('farmer')] + list(a.get('hands') or []):
            if c and len(c) > 1 and c[0] == 'PICKUP' and c[1] == 'FERTILIZER':
                n += int(c[2]) if len(c) > 2 else 1
    return n


def _wf_can_hire(obs, action, player):
    step = int(obs['step']); day, hour = divmod(step, 24)
    native = _IMPL.chassis.players.get(player)
    if native is None:
        return False
    planned = _v219_native_day(native, day)
    if any(o and o[0] == 'HIRE' for a in planned[hour + 1:] for o in a.get('market', [])):
        return False
    if native.get('pending'):
        return False
    if any(o and o[0] == 'HIRE' for o in action.get('market', [])):
        return False
    if _R51_INPUT_STATES.get(player, {}).get('pending'):
        return False
    for parent in (_V219_STATES.get(player, {}), _V233_STATES.get(player, {})):
        if parent.get('pending'):
            return False
    if 12 <= day <= 28 and hour < _WF_CFG['hire_hour']:
        return False
    return True


_WF_PARENT = agent
def agent(observation, configuration=None):
    action = _WF_PARENT(observation, configuration)
    try:
        step = int(observation['step']); player = int(observation['player']); day, hour = divmod(step, 24)
        st = _WF_STATE.get(player)
        if st is None or step <= st.get('step', -1):
            st = _WF_STATE[player] = {'step': -1}
            for k in _WF_REPORT: _WF_REPORT[k] = 0
        st['step'] = step
        if not (_WF_CFG['d0'] <= day <= _WF_CFG['d1']) or not isinstance(action, dict):
            return action
        if st.get('day') != day:
            st.update(day=day, hired=False, pend=None, worker=None, loaded=False, done=set())
        farm = observation['farms'][player]; private = observation['private']
        out = action
        if st.get('pend'):
            p = st.pop('pend')
            if len(farm['hands']) >= p['actor']:
                st['worker'] = p['actor']
        if not st['hired'] and hour <= _WF_CFG['last_hour'] and _wf_can_hire(observation, action, player):
            targets = _wf_targets(farm, day, hour)
            if len(targets) >= _WF_CFG['min_targets'] and len(action.get('market') or []) < 10 and farm['money'] > _WF_CFG['min_money']:
                native = _IMPL.chassis.players.get(player)
                stock = int(projected_shed(action, FarmView(observation)).get('FERTILIZER', 0))
                spare = stock - _wf_native_pickups(native, day, hour) - _WF_CFG['keep']
                need = min(len(targets), _WF_CFG['max_apps'])
                buy = 0
                if spare < need and int(observation['market']['prices']['FERTILIZER']) <= _WF_CFG['max_buy_price']:
                    buy = need - max(0, spare)
                if max(0, spare) + buy >= _WF_CFG['min_targets'] and len(action.get('market') or []) + 1 + (1 if buy else 0) <= 10:
                    extra = ([['BUY_PRODUCT', 'FERTILIZER', buy]] if buy else []) + [['HIRE']]
                    # drop the parent's fertilizer sales today while our helper needs the stock
                    market = [o for o in (action.get('market') or []) if not (isinstance(o, list) and len(o) >= 2 and o[:2] == ['SELL', 'FERTILIZER'])]
                    out = dict(action); out['market'] = market + extra
                    st['hired'] = True; st['pend'] = {'actor': len(farm['hands']) + 1}; st['quota'] = max(0, spare) + buy
                    _WF_REPORT['helpers'] += 1; _WF_REPORT['bought'] += buy
            elif hour >= _WF_CFG['last_hour']:
                _WF_REPORT['skipped_days'] += 1
        if st.get('worker') is not None and not st.get('loaded') and out.get('market'):
            if out is action:
                out = dict(action)
            out['market'] = [o for o in out['market'] if not (isinstance(o, list) and len(o) >= 2 and o[:2] == ['SELL', 'FERTILIZER'])]
        w = st.get('worker')
        if w is not None and w <= len(farm['hands']):
            pos = tuple(farm['hands'][w - 1]); inv = private['inventories'][w] if w < len(private['inventories']) else {}
            have = int(inv.get('FERTILIZER', 0))
            cmd = None
            if not st['loaded']:
                if pos in _WF_ACCESS:
                    stock = int(private['shed'].get('FERTILIZER', 0))
                    q = min(stock, st.get('quota', 0), _WF_CFG['max_apps'])
                    st['loaded'] = True
                    if q > 0:
                        cmd = ['PICKUP', 'FERTILIZER', q]; _WF_REPORT['loaded'] += q
                else:
                    a = min(_WF_ACCESS, key=lambda p: abs(p[0] - pos[0]) + abs(p[1] - pos[1]))
                    cmd = ['EAST' if a[0] > pos[0] else 'WEST'] if a[0] != pos[0] else (['SOUTH' if a[1] > pos[1] else 'NORTH'])
            if cmd is None and have > 0:
                targets = [p for p in _wf_targets(farm, day, hour) if p not in st['done']]
                if targets:
                    tgt = min(targets, key=lambda p: (abs(p[0] - pos[0]) + abs(p[1] - pos[1]), p))
                    if tgt == pos:
                        cmd = ['FERTILIZE']; st['done'].add(tgt); _WF_REPORT['applied'] += 1
                    elif tgt[0] != pos[0]:
                        cmd = ['EAST' if tgt[0] > pos[0] else 'WEST']
                    else:
                        cmd = ['SOUTH' if tgt[1] > pos[1] else 'NORTH']
            if cmd is None:
                cmd = ['PASS']
            if out is action:
                out = dict(action)
            hands = list(out.get('hands') or [])
            while len(hands) < len(farm['hands']):
                hands.append(['PASS'])
            hands[w - 1] = cmd
            out['hands'] = hands
        return out
    except Exception:
        _WF_REPORT['errors'] += 1
    return action
agent.telemetry = _WF_REPORT
agent = globals().pop('agent')
globals().pop('kaggle_submission_agent', None)
kaggle_submission_agent = agent
