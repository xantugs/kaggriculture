

# ---- route library extension (measurement/policy layer) ---------------------------------------------
# _MINED: extra route tapes {route_id: [action per step]} installed into the chassis library on first use.
# _FR_ROUTE: route forced from step 144 until _FR_END (None = keep the chassis router's choice).
# _FR_POLICY: optional callable(observation, default_route) -> route, consulted once at step 144.
_MINED = {}
_FR_ROUTE = None
_FR_END = 648
_FR_POLICY = None
_FR_ORIG_ROUTER = _IMPL.chassis.router
_FR_REPORT = dict(fr_policy_route=-1, fr_errors=0)


def _fr_router(observation, step, state):
    if _MINED:
        lib = _IMPL.chassis.routes
        for k, v in _MINED.items():
            if k not in lib:
                lib[k] = v
    r = _FR_ORIG_ROUTER(observation, step, state)
    if 144 <= step < _FR_END:
        if _FR_POLICY is not None:
            if 'fr_choice' not in state:
                try:
                    state['fr_choice'] = _FR_POLICY(observation, r)
                except Exception:
                    _FR_REPORT['fr_errors'] += 1
                    state['fr_choice'] = r
                _FR_REPORT['fr_policy_route'] = state['fr_choice']
            state['route'] = state['fr_choice']
            return state['fr_choice']
        if _FR_ROUTE is not None:
            state['route'] = _FR_ROUTE
            return _FR_ROUTE
    return r


_IMPL.chassis.router = _fr_router
_fr_agent = globals().pop('kaggle_submission_agent')
globals().pop('agent', None)
agent = _fr_agent
del _fr_agent
agent = globals().pop('agent')
kaggle_submission_agent = agent
