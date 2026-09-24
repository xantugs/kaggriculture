

# =====================================================================================
# Price-aware hold. The route sells on a fixed schedule, including into gluts (milk and
# wool at $8-50 when both farms sell together). A unit sold into a glut is lost value:
# the town drains stock every 4 steps and the price recovers within days. This layer cuts
# a scheduled sale down to the units whose own sale price stays at or above a threshold
# (a fraction of the product's base price), keeps the rest in the shed, and releases the
# held units once the price has recovered. The threshold falls to zero over the last days.
# =====================================================================================
_HD_CFG = __HDCFG__
_HD_STATE = {}
_HD_REPORT = dict(cut_units=0, released_units=0, cut_steps=0, errors=0)


def _hd_threshold(item, step, key='alpha'):
    base = _R37_MARKET_PARAMS[item]['base']
    a = _HD_CFG[key].get(item, 0.0)
    t = step / 24.0
    d0, d1 = _HD_CFG['ramp']
    if t >= d1:
        return 0.0
    if t > d0:
        a = a * (d1 - t) / (d1 - d0)
    return a * base


def _hd_allowed(item, inv, thr, maxq):
    k = 0
    while k < maxq and _r37_market_price(item, inv + k) >= thr:
        k += 1
    return k


_HD_PARENT = agent
def agent(observation, configuration=None):
    action = _HD_PARENT(observation, configuration)
    try:
        step = int(observation['step']); player = int(observation['player'])
        st = _HD_STATE.get(player)
        if st is None or step <= st.get('step', -1):
            st = _HD_STATE[player] = {'step': -1, 'held': {}}
            for k in _HD_REPORT: _HD_REPORT[k] = 0
        st['step'] = step
        if step >= _HD_CFG['stop_step'] or step < _HD_CFG['start_step'] or not isinstance(action, dict):
            return action
        inv = observation['market']['inventory']
        stock = dict(projected_shed(action, FarmView(observation)))
        carried = sum(sum(int(v) for v in (i or {}).values()) for i in (observation['private'].get('inventories') or []))
        crowded = sum(max(0, int(v)) for v in stock.values()) + carried > _HD_CFG['crowd']
        held = st['held']
        market = []
        changed = False
        sold_items = set()
        for o in (action.get('market') or []):
            if isinstance(o, list) and len(o) >= 3 and o[0] == 'SELL' and o[1] in _HD_CFG['alpha']:
                item = o[1]; q = int(o[2]); avail = max(0, int(stock.get(item, 0)))
                want = min(q, avail)
                if want <= 0:
                    market.append(o); continue
                thr = 0.0 if crowded else _hd_threshold(item, step)
                ok = _hd_allowed(item, int(inv[item]), thr, want)
                ok = max(ok, min(want, avail - _HD_CFG['cap'].get(item, 999)))
                extra = 0
                if held.get(item, 0) > 0:
                    rel = 0.0 if crowded else _hd_threshold(item, step, 'release')
                    extra = max(0, min(held[item], avail - ok, _hd_allowed(item, int(inv[item]), max(thr, rel), avail) - ok))
                if ok < want:
                    held[item] = held.get(item, 0) + (want - ok)
                    _HD_REPORT['cut_units'] += want - ok; _HD_REPORT['cut_steps'] += 1
                if extra > 0:
                    held[item] -= extra; _HD_REPORT['released_units'] += extra
                n = ok + extra
                sold_items.add(item)
                if n != q:
                    changed = True
                if n > 0:
                    market.append(['SELL', item, n])
                else:
                    changed = True
                continue
            market.append(o)
        # release held stock without a parent order once the price has recovered
        for item, h in list(held.items()):
            if h <= 0 or item in sold_items or len(market) >= 10:
                continue
            avail = max(0, int(stock.get(item, 0)))
            if avail <= 0:
                held[item] = 0; continue
            rel = 0.0 if crowded else max(_hd_threshold(item, step), _hd_threshold(item, step, 'release'))
            n = min(h, avail, _hd_allowed(item, int(inv[item]), rel, min(h, avail)))
            if n > 0:
                market.append(['SELL', item, n]); held[item] -= n; changed = True
                _HD_REPORT['released_units'] += n
        out = dict(action); out['market'] = market
        if _HD_CFG.get('animal'):
            farm = observation['farms'][player]
            cmds = [out.get('farmer') or ['PASS']] + [list(c) for c in (out.get('hands') or [])]
            pos = [tuple(farm['farmer'])] + [tuple(p) for p in farm['hands']]
            prod = {'COW': 'MILK', 'SHEEP': 'WOOL', 'GOOSE': 'EGG'}
            cap = {'COW': 6, 'SHEEP': 6, 'GOOSE': 4}; step_prod = {'COW': 2, 'SHEEP': 2, 'GOOSE': 2}
            for a, c in enumerate(cmds):
                if a >= len(pos) or not c or c[0] != 'HARVEST':
                    continue
                x, y = pos[a]; t = farm['tiles'][y][x]
                if not (isinstance(t, dict) and t.get('animal') in prod):
                    continue
                item = prod[t['animal']]
                if item not in _HD_CFG['animal']:
                    continue
                if int(t.get('yield_units', 0)) + step_prod[t['animal']] > cap[t['animal']]:
                    continue
                if _r37_market_price(item, int(inv[item])) >= _hd_threshold(item, step, 'animal'):
                    continue
                cmds[a] = ['PASS']; changed = True; _HD_REPORT['skipped_harvests'] = _HD_REPORT.get('skipped_harvests', 0) + 1
            out['farmer'], out['hands'] = cmds[0], cmds[1:]
        if changed:
            return out
    except Exception:
        _HD_REPORT['errors'] += 1
    return action
agent.telemetry = _HD_REPORT
agent = globals().pop('agent')
globals().pop('kaggle_submission_agent', None)
kaggle_submission_agent = agent
