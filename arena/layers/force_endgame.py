
# ---- measurement layer: force the endgame route (days 27..29) -----------------------------------
_EG_ROUTE = __R__
_EG_ORIG_ROUTER = _IMPL.chassis.router
def _eg_router(observation, step, state):
    r = _EG_ORIG_ROUTER(observation, step, state)
    if step >= 648:
        if _EG_ROUTE == -1:          # keep the mid-game route
            mid = state.get('mid_route')
            if mid is not None:
                state['route'] = mid
                return mid
            return r
        state['route'] = _EG_ROUTE
        return _EG_ROUTE
    if 144 <= step < 648:
        state['mid_route'] = r
    return r
_IMPL.chassis.router = _eg_router
agent = globals().pop('agent')
globals().pop('kaggle_submission_agent', None)
kaggle_submission_agent = agent
