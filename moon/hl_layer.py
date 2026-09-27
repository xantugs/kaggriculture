
# =====================================================================================
# HL (offhand, 2026-09-24): reservation price on crash days. From day D0 to D1, SELL orders of ITEMS are cut while
# the quote is below P_MIN, unless the shed (after this step's drops, before sales) holds more than ROOM units -
# the day-end storage guards still sell what would not fit. Held stock is sold by the chassis once the quote recovers.
# =====================================================================================
_HL_ON = True
_HL_CFG = dict(items=('STRAWBERRY',), d0=20, d1=27, p_min=40, room=85)
_HL_REPORT = dict(hl_turns=0, hl_units=0, hl_errors=0)
_HL_PARENT = agent
del agent


def agent(observation, configuration=None):
    action = _HL_PARENT(observation, configuration)
    try:
        c = _HL_CFG
        step = int(observation['step']); day = step // 24
        if not _HL_ON or not isinstance(action, dict) or not c['d0'] <= day <= c['d1']:
            return action
        prices = observation['market']['prices']
        items = [it for it in c['items'] if int(prices.get(it, 0)) < c['p_min']]
        if not items:
            return action
        market = action.get('market') or []
        if not any(len(o) >= 3 and o[0] == 'SELL' and o[1] in items for o in market):
            return action
        stock = projected_shed(action, FarmView(observation))
        if sum(max(0, int(v)) for v in stock.values()) > c['room']:
            return action
        new = []; cut = 0
        for o in market:
            if len(o) >= 3 and o[0] == 'SELL' and o[1] in items:
                cut += int(o[2]); continue
            new.append(o)
        _HL_REPORT['hl_turns'] += 1; _HL_REPORT['hl_units'] += cut
        action = dict(action); action['market'] = new
    except Exception as e:
        _HL_REPORT['hl_errors'] += 1; _HL_REPORT['hl_last_error'] = repr(e)[:160]
    return action


agent.telemetry = _HL_REPORT
agent = globals().pop('agent')
globals().pop('kaggle_submission_agent', None)
kaggle_submission_agent = agent
