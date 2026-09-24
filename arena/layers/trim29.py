
# ---- experimental layer: trim the most expensive hires on the final day -------------------------
_T29_DROP = __K__
_T29_FROM = __FROM__
_T29_PARENT = agent
def agent(observation, configuration=None):
    action = _T29_PARENT(observation, configuration)
    try:
        step = int(observation['step'])
        if step >= _T29_FROM:
            seat = int(observation['player'])
            farm = observation['farms'][seat]
            market = list(action.get('market') or [])
            hires_here = sum(1 for o in market if isinstance(o, list) and o and o[0] == 'HIRE')
            if hires_here:
                # planned total hires today = already hired + hires in this action
                done = int(farm.get('hires_today', 0))
                planned_total = done + hires_here
                if not hasattr(agent, '_t29_plan'):
                    agent._t29_plan = {}
                day = step // 24
                cap = agent._t29_plan.get(day)
                if cap is None:
                    cap = max(0, planned_total - _T29_DROP)
                    agent._t29_plan[day] = cap
                allow = max(0, cap - done)
                out = []
                for o in market:
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
