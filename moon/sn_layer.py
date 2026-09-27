
# =====================================================================================
# SN (offhand, 2026-09-24): sell steep-curve goods as soon as they are in the shed. Above its reference stock a
# strawberry sale lowers every later strawberry quote by ~1.92 (milk ~2.1) for both farms, so on crash days the
# farm that sells first takes the higher quotes and pushes the rival's later lots down. From day D0, every step,
# the shed stock of ITEMS (after this step's drops, minus the sells already ordered, minus KEEP) is sold at the
# front of the order list while the quote is >= MIN_PRICE.
# =====================================================================================
_SN_ON = True
_SN_CFG = dict(items=('STRAWBERRY',), d0=18, last_step=695, min_price=2, keep=0, hours=None, front=True)
_SN_REPORT = dict(sn_turns=0, sn_units=0, sn_errors=0)
_SN_PARENT = agent
del agent


def agent(observation, configuration=None):
    action = _SN_PARENT(observation, configuration)
    try:
        c = _SN_CFG
        step = int(observation['step'])
        if not _SN_ON or not isinstance(action, dict) or step // 24 < c['d0'] or step > c['last_step']:
            return action
        if c['hours'] is not None and step % 24 not in c['hours']:
            return action
        market = [list(o) for o in (action.get('market') or [])]
        prices = observation['market']['prices']
        stock = projected_shed(action, FarmView(observation))
        add = []
        for it in c['items']:
            if int(prices.get(it, 0)) < c['min_price']:
                continue
            selling = sum(int(o[2]) for o in market if len(o) >= 3 and o[:2] == ['SELL', it])
            q = int(stock.get(it, 0)) - selling - c['keep']
            if q > 0:
                add.append(['SELL', it, q])
        if not add or len(market) + len(add) > 10:
            return action
        market = add + market if c['front'] else market + add
        _SN_REPORT['sn_turns'] += 1; _SN_REPORT['sn_units'] += sum(o[2] for o in add)
        action = dict(action); action['market'] = market
    except Exception as e:
        _SN_REPORT['sn_errors'] += 1; _SN_REPORT['sn_last_error'] = repr(e)[:160]
    return action


agent.telemetry = _SN_REPORT
agent = globals().pop('agent')
globals().pop('kaggle_submission_agent', None)
kaggle_submission_agent = agent
