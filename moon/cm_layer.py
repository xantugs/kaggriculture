

# =====================================================================================
# CM: rival-type switch. Several sale layers model the rival as a copy of our own route. Against a rival
# whose farm stops matching ours (checked at steps 143 and 359, weeds ignored), bypass those layers for
# the rest of the game by pointing the next layer in the chain at the bypassed layer's parent.
# =====================================================================================
_CM_SKIP = __CM_SKIP__          # list of (layer parent global, next layer parent global)
_CM_THRESH = __CM_THRESH__      # {step: minimum similarity to still count as a mirror}
_CM_STATE = {'off': False, 'saved': {}}
_CM_REPORT = dict(cm_nonmirror=0, cm_step=-1, cm_sim=-1.0, cm_errors=0)


def _cm_sig(farm):
    out = []
    for row in farm.get('tiles') or []:
        for t in row:
            if t is None or (isinstance(t, dict) and t.get('kind') == 'WEED'):
                out.append('.')
            elif t == 'LOCKED':
                out.append('#')
            elif isinstance(t, dict):
                out.append(str(t.get('crop') or t.get('animal') or t.get('kind')))
            else:
                out.append('?')
    return out


def _cm_restore():
    g = globals()
    for k, v in _CM_STATE['saved'].items():
        g[k] = v
    _CM_STATE['saved'] = {}
    _CM_STATE['off'] = False


_CM_PARENT = agent


def agent(observation, configuration=None):
    try:
        step = int(observation['step'])
        if step == 0 and (_CM_STATE['off'] or _CM_STATE['saved']):
            _cm_restore()
        if step in _CM_THRESH and not _CM_STATE['off']:
            me = int(observation['player'])
            a = _cm_sig(observation['farms'][me]); b = _cm_sig(observation['farms'][1 - me])
            sim = sum(x == y for x, y in zip(a, b)) / max(1, len(a))
            if sim < _CM_THRESH[step]:
                g = globals()
                for layer, nxt in _CM_SKIP:
                    if nxt not in _CM_STATE['saved']:
                        _CM_STATE['saved'][nxt] = g[nxt]
                    g[nxt] = g[layer]
                _CM_STATE['off'] = True
                _CM_REPORT.update(cm_nonmirror=1, cm_step=step, cm_sim=round(sim, 3))
    except Exception:
        _CM_REPORT['cm_errors'] += 1
    return _CM_PARENT(observation, configuration)


agent.telemetry = _CM_REPORT
agent = globals().pop('agent')
globals().pop('kaggle_submission_agent', None)
kaggle_submission_agent = agent
