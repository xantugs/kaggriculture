
# ---- measurement layer: force a mid-game route (days 6..26) -------------------------------------
_FR_ROUTE = __R__
_FR_ORIG_ROUTER = _IMPL.chassis.router
def _fr_router(observation, step, state):
    r = _FR_ORIG_ROUTER(observation, step, state)
    if 144 <= step < 648:
        state['route'] = _FR_ROUTE
        return _FR_ROUTE
    return r
_IMPL.chassis.router = _fr_router
agent = globals().pop('agent')
globals().pop('kaggle_submission_agent', None)
kaggle_submission_agent = agent
