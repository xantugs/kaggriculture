
# ---- experimental layer: cap total hires per day from a given step ------------------------------
_HC_MAX = __H__
_HC_FROM = __FROM__
_HC_PARENT = agent
def agent(observation, configuration=None):
    action = _HC_PARENT(observation, configuration)
    try:
        step = int(observation['step'])
        if step >= _HC_FROM:
            seat = int(observation['player'])
            done = int(observation['farms'][seat].get('hires_today', 0))
            allow = max(0, _HC_MAX - done)
            out = []
            for o in list(action.get('market') or []):
                if isinstance(o, list) and o and o[0] == 'HIRE':
                    if allow > 0:
                        out.append(o); allow -= 1
                    else:
                        out.append([])
                else:
                    out.append(o)
            action['market'] = out
    except Exception:
        pass
    return action
agent = globals().pop('agent')
globals().pop('kaggle_submission_agent', None)
kaggle_submission_agent = agent
