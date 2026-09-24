
# ---- experimental layer: cap own strawberry plantings -------------------------------------------
_SC_CAP = __CAP__
_SC_PARENT = agent
def agent(observation, configuration=None):
    action = _SC_PARENT(observation, configuration)
    try:
        seat = int(observation['player'])
        farm = observation['farms'][seat]
        seeds = int((observation['private'].get('seeds') or {}).get('STRAWBERRY', 0))
        plants = 0
        for row in farm['tiles']:
            for t in row:
                if isinstance(t, dict) and t.get('kind') == 'PLANT' and t.get('crop') == 'STRAWBERRY':
                    plants += 1
        allowed = max(0, _SC_CAP - plants)
        units = [action.get('farmer')] + list(action.get('hands') or [])
        n_plant = 0
        for i, u in enumerate(units):
            if isinstance(u, list) and len(u) >= 2 and u[0] == 'PLANT' and u[1] == 'STRAWBERRY':
                n_plant += 1
                if n_plant > allowed:
                    if i == 0: action['farmer'] = ['PASS']
                    else: action['hands'][i - 1] = ['PASS']
        used = min(n_plant, allowed)
        room = max(0, allowed - used - max(0, seeds - used))
        new_market = []
        for o in action.get('market') or []:
            if isinstance(o, list) and len(o) >= 3 and o[0] == 'BUY_SEED' and o[1] == 'STRAWBERRY':
                q = min(int(o[2]), room)
                room -= q
                if q > 0:
                    new_market.append(['BUY_SEED', 'STRAWBERRY', q])
                else:
                    new_market.append([])
            else:
                new_market.append(o)
        action['market'] = new_market
    except Exception:
        pass
    return action
agent = globals().pop('agent')
globals().pop('kaggle_submission_agent', None)
kaggle_submission_agent = agent
