

# ---- CARE pruning from day _CP_CFG['from_day']: a CARE command on an animal whose product is
# ---- glutted (price below its gate) becomes a PASS.  The unit keeps its tape timing.
_CP_CFG = __CPCFG__
_CP_REPORT = dict(pruned=0, kept=0)
_CP_PRODUCT = {'GOOSE': 'EGG', 'COW': 'MILK', 'SHEEP': 'WOOL'}
_CP_PARENT = agent
def agent(observation, configuration=None):
    action = _CP_PARENT(observation, configuration)
    try:
        step = int(observation['step'])
        if step // 24 < _CP_CFG['from_day'] or step >= 696 or not isinstance(action, dict):
            return action
        farm = observation['farms'][int(observation['player'])]
        prices = observation['market']['prices']
        cmds = [action.get('farmer') or ['PASS']] + list(action.get('hands') or [])
        pos = [farm['farmer']] + list(farm['hands'])
        changed = False
        for i, c in enumerate(cmds):
            if not c or c[0] != 'CARE' or i >= len(pos): continue
            x, y = pos[i]; t = farm['tiles'][y][x]
            if not isinstance(t, dict) or not t.get('animal'): continue
            a = t['animal']
            gate = _CP_CFG['gate'].get(a)
            if gate is None: _CP_REPORT['kept'] += 1; continue
            if int(prices.get(_CP_PRODUCT[a], 0)) < gate:
                cmds[i] = ['PASS']; changed = True; _CP_REPORT['pruned'] += 1
            else:
                _CP_REPORT['kept'] += 1
        if changed:
            action = dict(action); action['farmer'] = cmds[0]; action['hands'] = cmds[1:]
    except Exception:
        pass
    return action
agent.telemetry = _CP_REPORT
agent = globals().pop('agent')
globals().pop('kaggle_submission_agent', None)
kaggle_submission_agent = agent
