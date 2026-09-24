

# =====================================================================================
# ECO (offhand, 2026-09-24): self-supplied inputs. Top farms buy almost no wheat or fertilizer; the chassis sells
# its own wheat/fertilizer and buys it back (414 wheat @ $41.3 bought vs 639 sold @ $40.4 per game). From day
# `from_day` this outermost layer keeps enough own stock for the route's planned pickups over the next `horizon`
# turns plus a reserve, drops purchases that stock already covers, and trims sales that would leave it short.
# =====================================================================================
_ECO_PARENT = agent
_ECO_CFG = dict(wheat=True, fert=True, from_day=2, horizon=24, reserve_w=4, reserve_f=2, trim_sells=True, cut_buys=True)
_ECO_REPORT = dict(eco_buy_cut_w=0, eco_sell_cut_w=0, eco_buy_cut_f=0, eco_sell_cut_f=0, eco_errors=0)
_ECO_SHED = ((4, 4), (5, 4), (4, 5), (5, 5))


def _eco_planned_pickups(tape, step, horizon, item):
    n = 0
    for t in range(step + 1, min(len(tape), step + 1 + horizon)):
        a = tape[t]
        for c in [a.get('farmer') or ['PASS']] + list(a.get('hands') or []):
            if c and c[0] == 'PICKUP' and len(c) > 1 and c[1] == item:
                n += max(1, int(c[2])) if len(c) > 2 else 1
        if (t + 1) % 24 == 0 and t > step + 1:
            pass
    return n


def _eco_act(obs, action):
    c = _ECO_CFG; step = int(obs['step']); day = step // 24
    if day < c['from_day'] or step >= 712 or not isinstance(action, dict):
        return action
    player = int(obs['player']); priv = obs['private']; shed = priv.get('shed') or {}
    native = _IMPL.chassis.players[player]
    tape = _IMPL.chassis.routes[2 if step >= 648 else native['route']]
    cmds = [action.get('farmer') or ['PASS']] + list(action.get('hands') or [])
    market = [list(o) for o in (action.get('market') or [])]
    changed = False
    for item, on, rsv, kb, ks in (('WHEAT', c['wheat'], c['reserve_w'], 'eco_buy_cut_w', 'eco_sell_cut_w'),
                                  ('FERTILIZER', c['fert'], c['reserve_f'], 'eco_buy_cut_f', 'eco_sell_cut_f')):
        if not on:
            continue
        now = sum(max(1, int(x[2])) if len(x) > 2 else 1 for x in cmds if x and x[0] == 'PICKUP' and len(x) > 1 and x[1] == item)
        need = _eco_planned_pickups(tape, step, c['horizon'], item) + rsv
        stock = int(shed.get(item, 0)) - now
        sells = [o for o in market if o and o[0] == 'SELL' and len(o) > 2 and o[1] == item]
        buys = [o for o in market if o and o[0] == 'BUY_PRODUCT' and len(o) > 2 and o[1] == item]
        sold = sum(max(0, int(o[2])) for o in sells)
        bought = sum(max(0, int(o[2])) for o in buys)
        after = stock - min(sold, max(0, stock)) + bought
        # 1. purchases our own stock already covers
        if c['cut_buys'] and bought and after - bought >= need:
            for o in buys:
                _ECO_REPORT[kb] += int(o[2]); o[2] = 0
            changed = True; after -= bought
        elif c['cut_buys'] and bought and after > need:
            cut = min(bought, after - need)
            for o in buys:
                d = min(cut, int(o[2])); o[2] = int(o[2]) - d; cut -= d; _ECO_REPORT[kb] += d
            changed = True
        # 2. sales that would leave our own supply short (sell less instead of buying back later)
        if c['trim_sells'] and sold and stock - sold < need:
            keep = min(sold, need - (stock - sold))
            for o in sells:
                d = min(keep, int(o[2])); o[2] = int(o[2]) - d; keep -= d; _ECO_REPORT[ks] += d
            changed = True
    if not changed:
        return action
    out = dict(action); out['market'] = [o for o in market if not (o and o[0] in ('SELL', 'BUY_PRODUCT') and len(o) > 2 and int(o[2]) <= 0)]
    return out


def agent(observation, configuration=None):
    action = _ECO_PARENT(observation, configuration)
    try:
        action = _eco_act(observation, action)
    except Exception as e:
        _ECO_REPORT['eco_errors'] += 1; _ECO_REPORT['eco_last_error'] = repr(e)[:160]
    return action


agent.telemetry = _ECO_REPORT
agent = globals().pop('agent')
globals().pop('kaggle_submission_agent', None)
kaggle_submission_agent = agent
