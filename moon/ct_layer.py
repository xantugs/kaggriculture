

# =====================================================================================
# CT: counter-tomato. The chassis' V219 tomato block (buy SE on day 18, ten tomato plots with their own
# crew) normally needs three tomato shops. It also pays when the rival is visibly a tomato farm: every
# tomato we sell then lowers the price of theirs. Extend the gate to that case, with at least one
# tomato shop open. Mirrors grow no tomatoes, so against them this never fires.
# =====================================================================================
_CT_MIN_RIVAL = __CT_MIN__
_CT_MIN_SHOPS = __CT_SHOPS__
_CT_REPORT = dict(ct_fires=0, ct_checks=0)
_CT_ORIG_Q = _v219_qualifies


def _v219_qualifies(obs, native):
    if _CT_ORIG_Q(obs, native):
        return True
    try:
        _CT_REPORT['ct_checks'] += 1
        me = int(obs['player'])
        farm = obs['farms'][me]; rival = obs['farms'][1 - me]
        rt = sum(1 for row in rival['tiles'] for t in row if isinstance(t, dict) and t.get('crop') == 'TOMATO')
        if rt < _CT_MIN_RIVAL:
            return False
        if len(farm['tiles']) != 10 or set(farm['unlocked_quadrants']) != {'NW', 'NE', 'SW'}:
            return False
        if farm['money'] < 12000:
            return False
        if sum(s in ('PIZZA_SHOP', 'FARMERS_MARKET') for s in obs['town']['unlocked_shops']) < _CT_MIN_SHOPS:
            return False
        if any(farm['tiles'][y][x] != 'LOCKED' for y in (5, 6) for x in range(5, 10)):
            return False
        if obs['private']['seeds'].get('TOMATO', 0) or obs['private']['shed'].get('TOMATO', 0):
            return False
        if any(isinstance(t, dict) and t.get('crop') == 'TOMATO' for row in farm['tiles'] for t in row):
            return False
        for tape in _IMPL.chassis.routes.values():
            for a in tape[432:719]:
                if any(o and o[0] == 'BUY_LAND' for o in a.get('market', [])):
                    return False
                if any(c == ['PLANT', 'TOMATO'] for c in [a.get('farmer')] + a.get('hands', [])):
                    return False
        _CT_REPORT['ct_fires'] += 1
        return True
    except Exception:
        return False


_ct_agent = globals().pop("kaggle_submission_agent")
globals().pop("agent", None)
agent = _ct_agent
del _ct_agent
kaggle_submission_agent = globals().pop("agent")
agent = kaggle_submission_agent
globals().pop("kaggle_submission_agent")
kaggle_submission_agent = agent
