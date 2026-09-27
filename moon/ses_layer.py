

# =====================================================================================
# SES (offhand, 2026-09-25): south-east strawberry block in strawberry towns.
# Late strawberry prices depend on the town: with all 4 day-12 shops buying strawberries the price holds
# ~$205 over days 22-28 (212 recorded games); with 3 it averages $154 and extra supply crashes it onto our own
# 33 strawberries (pinned: -$1.6k/game over all games), with fewer it falls to $10-47. SES buys SE on `day`
# in a 4-of-4 town, plants up to `n` strawberries (planted day p produces at the end of ages 9, 11, 13, 15;
# +2 instead of +1 when watered and fertilized that day; a fertilizer lasts 3 days), waters every other day
# (two dry days turn a plant into a weed), fertilizes at age 9, harvests and drops at the shed, with a crew of
# at most `kmax` hands hired after the tape's hires. From the GOLD takeover on, the controller owns these
# tiles like any other. Pinned on the 22 qualifying games of train/hold/fresh16/fresh17: +$10.2k/game, +7 wins.
# The same block with tomatoes (tom_min) lost $11.8k in a 2-tomato-shop town (crew wages, blocks V219); off.
# ADAPT compares our farm with the rival's at its check steps; SES shows ADAPT its SE tiles as the rival's.
# =====================================================================================
import collections
_SES_PARENT = agent
_SES_CFG = dict(day=12, min_hour=4, crew_hour=1, slack=1.3, last_hour=12, min_shops=4, min_price=0, n=25,
                tom_min=99, tom_day=None, tom_n=25, reserve=4000, kmax=2,
                plant_last=13, fert=True, fert_max_price=160, sell=True, mask_ad=True, end_step=576,
                tom_skip=3)
_SES_REPORT = dict(ses_bought=0, ses_hires=0, ses_plants=0, ses_waters=0, ses_harvests=0, ses_fert=0, ses_sold=0,
                   ses_errors=0)
_SES_STATES = {}
_SES_RUN = dict(crop='STRAWBERRY', n=25, plant_last=13)
_SES_LOG = []
_SES_TILES = [(x, y) for y in range(5, 10) for x in range(5, 10)]
_SES_ACCESS = ((4, 4), (5, 4), (4, 5), (5, 5))


def _ses_tiles():
    """The `n` SE tiles nearest the shed corner (5, 5), row by row."""
    return sorted(_SES_TILES, key=lambda p: (p[0] + p[1], p[1]))[:_SES_RUN['n']]


def _ses_fib(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def _ses_walk(pos, t):
    x, y = pos; tx, ty = t
    if x != tx:
        return ['EAST' if x < tx else 'WEST']
    if y != ty:
        return ['SOUTH' if y < ty else 'NORTH']
    return None


def _ses_home(pos):
    return min(_SES_ACCESS, key=lambda p: abs(pos[0] - p[0]) + abs(pos[1] - p[1]))


def _ses_straw_shops(obs):
    return sum(s in ('BRUNCH_SPOT', 'ICE_CREAM_SHOP', 'SMOOTHIE_SHOP', 'FARMERS_MARKET')
               for s in obs['town']['unlocked_shops'])


def _ses_tom_shops(obs):
    return sum(s in ('PIZZA_SHOP', 'FARMERS_MARKET') for s in obs['town']['unlocked_shops'])


_SES_INFO = {}


def _ses_info(crop):
    """(production ages, fertilize ages, first harvest age, seed price): a plant of age a produces at the end of
    that day when a is in the first set; a fertilizer applied at age a covers ages a..a+2."""
    if crop not in _SES_INFO:
        cd = {'STRAWBERRY': (10, 2, 4, 100), 'TOMATO': (8, 1, 4, 50)}[crop]
        prod = [cd[0] - 1 + cd[1] * k for k in range(cd[2])]
        fert = []
        for a in prod:
            if not fert or a > fert[-1] + 2:
                fert.append(a)
        _SES_INFO[crop] = (frozenset(prod), frozenset(fert), cd[0], cd[3])
    return _SES_INFO[crop]


def _ses_crop():
    return _SES_RUN['crop']


def _ses_job(t, day, fert_in_hand, may_plant, extra=False):
    """(command, priority) for one SE tile today, or None. Priority 0 = water or the plant dies tonight,
    1 = fertilize / water on a production day, 2 = harvest, 3 = plant, 4 = water early (spreads the load)."""
    crop = _ses_crop(); prod_a, fert_a, first, _ = _ses_info(crop)
    if t is None:
        return (['PLANT', crop], 3) if may_plant else None
    if not isinstance(t, dict):
        return None
    if t.get('kind') == 'WEED':
        return (['DIG'], 3) if may_plant else None
    if t.get('kind') != 'PLANT' or t.get('crop') != crop:
        return None
    age = day - t['planted_day']
    dry = not t.get('watered_today')
    if dry and t.get('consecutive_unwatered', 1) >= 1 and age <= max(prod_a):
        return ['WATER'], 0
    prod = age in prod_a
    fert_on = t.get('fertilized_until_day', -1) >= day
    if _SES_CFG['fert'] and age in fert_a and not fert_on and fert_in_hand > 0:
        return ['FERTILIZE'], 1
    if dry and prod:
        return ['WATER'], 1
    if t.get('yield_units', 0) > 0 and age >= first:
        return ['HARVEST'], 2
    if dry and extra:
        return ['WATER'], 4
    return None


def _ses_state(player, step):
    st = _SES_STATES.get(player)
    if st is None or step <= st['step']:
        st = _SES_STATES[player] = dict(step=-1, bought=False, buy_step=None, off=False, day=-1, crew=[], pending=None,
                                         requested_day=-1, own=0, last_inv={}, last_cmd={}, extra=set(), crop=None)
        for k in _SES_REPORT:
            _SES_REPORT[k] = 0
    st['step'] = step
    return st


def _ses_mask(obs):
    """Observation copy whose own SE tiles equal the rival's (for ADAPT's farm comparison)."""
    me = int(obs['player']); farms = list(obs['farms'])
    mine = dict(farms[me]); rt = farms[1 - me]['tiles']
    tiles = [list(r) for r in mine['tiles']]
    for (x, y) in _SES_TILES:
        tiles[y][x] = rt[y][x]
    mine['tiles'] = tiles; farms[me] = mine
    out = dict(obs); out['farms'] = farms
    return out


def _ses_plan_jobs(tiles, day, may_plant, st):
    """Steps of work today (a move plus the actions per tile), fertilizer needed; picks `extra` tiles to water
    early so the every-other-day watering splits evenly over days."""
    crop = _ses_crop(); prod_a, fert_a, first, _ = _ses_info(crop)
    steps = 0; fert = 0; busy = []; spare = []
    for (x, y) in _ses_tiles():
        t = tiles[y][x]
        if t is None or (isinstance(t, dict) and t.get('kind') == 'WEED'):
            if may_plant:
                busy.append((x, y)); steps += 3 + (t is not None)
            continue
        if not (isinstance(t, dict) and t.get('crop') == crop):
            continue
        age = day - t['planted_day']; dry = not t.get('watered_today')
        n = 0
        if dry and ((t.get('consecutive_unwatered', 1) >= 1 and age <= max(prod_a)) or age in prod_a):
            n += 1
        if _SES_CFG['fert'] and age in fert_a and t.get('fertilized_until_day', -1) < day:
            n += 1; fert += 1
        if age >= first and (t.get('yield_units', 0) > 0 or (age - 1) in prod_a):
            n += 1
        if n:
            busy.append((x, y)); steps += 1 + n
        elif dry and age < max(prod_a):
            spare.append((x, y))
    plants = len(busy) + len(spare)
    st['extra'] = set(spare[:max(0, (plants + 1) // 2 - len(busy))]) if not may_plant else set()
    steps += 2 * len(st['extra'])
    return steps, fert


def _ses_act(obs, action, st):
    step = int(obs['step']); day = step // 24; hour = step % 24; player = int(obs['player'])
    farm = obs['farms'][player]; private = obs['private']; c = _SES_CFG
    market = list(action.get('market') or [])
    quads = set(farm['unlocked_quadrants'])
    if st['off']:
        return action
    # 1. land: once, in a strawberry town, if SE is still ours to take
    if not st['bought']:
        if st['buy_step'] is not None:
            if 'SE' in quads:
                st['bought'] = True
            elif step > st['buy_step'] + 1:
                st['off'] = True
                return action
            else:
                return action
        else:
            tday = c['tom_day'] or c['day']
            if day < min(c['day'], tday) or hour < c['min_hour']:
                return action
            if st.get('crop') is None:
                if day == c['day'] and _ses_straw_shops(obs) >= c['min_shops'] and obs['market']['prices']['STRAWBERRY'] >= c['min_price']:
                    st['crop'] = 'STRAWBERRY'
                    _SES_RUN.update(crop='STRAWBERRY', n=c['n'], plant_last=c['plant_last'])
                elif day == tday and _ses_tom_shops(obs) >= c['tom_min']:
                    st['crop'] = 'TOMATO'
                    _SES_RUN.update(crop='TOMATO', n=c['tom_n'], plant_last=day + 1)
                elif day >= max(c['day'], tday) and hour > c['last_hour']:
                    st['off'] = True
                    return action
                else:
                    return action
            if day > _SES_RUN['plant_last'] - 1 and hour > c['last_hour']:
                st['off'] = True
                return action
            if (_V233_STATES.get(player) or {}).get('committed') or quads != {'NW', 'NE', 'SW'}:
                st['off'] = True
                return action
            if st['crop'] == 'STRAWBERRY' and _ses_tom_shops(obs) >= c['tom_skip']:   # the chassis' day-18 tomato block (V219) needs SE
                st['off'] = True
                return action
            if any(o and o[0] in ('BUY_LAND', 'HIRE') for o in market) or len(market) > 7:
                return action
            crop = _ses_crop(); sp = _ses_info(crop)[3]
            n = _SES_RUN['n']; have = int(private['seeds'].get(crop, 0))
            if farm['money'] < 4000 + sp * max(0, n - have) + c['reserve']:
                return action
            market.append(['BUY_LAND'])
            if n > have:
                market.append(['BUY_SEED', crop, n - have])
            st['buy_step'] = step; _SES_REPORT['ses_bought'] += 1
            out = dict(action); out['market'] = market
            return out
    # 2. day bookkeeping: crew leaves at midnight, its inventory drops into the shed
    if st['day'] != day:
        for inv in st['last_inv'].values():
            st['own'] += inv
        st['last_inv'] = {}; st['last_cmd'] = {}
        st['day'] = day; st['crew'] = []; st['requested_day'] = -1
    else:
        for actor, prev in st['last_inv'].items():
            if st['last_cmd'].get(actor, [''])[0] == 'DROP' and actor < len(private['inventories']):
                st['own'] += max(0, prev - int(private['inventories'][actor].get(_ses_crop(), 0)))
    tiles = farm['tiles']
    may_plant = day <= _SES_RUN['plant_last']
    if st['pending']:
        first, k = st['pending']; st['pending'] = None
        n_h = len(farm['hands'])
        st['crew'] = [i for i in range(first, first + k) if i <= n_h]
        _SES_REPORT['ses_hires'] += len(st['crew'])
    # 3. crew request once the tape has hired for the day
    if st['requested_day'] != day and hour >= c['crew_hour'] and hour <= 16 and step < c['end_step']:
        native = _IMPL.chassis.players[player]
        tape = _IMPL.chassis.routes[2 if step >= 648 else native['route']]
        later_hire = any(o and o[0] == 'HIRE' for t in range(step + 1, min((day + 1) * 24, len(tape)))
                         for o in tape[t].get('market', []))
        if not later_hire and not any(o and o[0] == 'HIRE' for o in market):
            st['requested_day'] = day
            steps, fert = _ses_plan_jobs(tiles, day, may_plant, st)
            left = 22 - hour
            k = min(c['kmax'], -(-int(steps * c['slack'] + 3) // max(1, left))) if steps else 0
            orders = []
            if may_plant:
                crop = _ses_crop(); sp = _ses_info(crop)[3]
                empty = sum(1 for (x, y) in _ses_tiles() if tiles[y][x] is None)
                have = int(private['seeds'].get(crop, 0))
                if empty > have and farm['money'] > sp * (empty - have) + 1500:
                    orders.append(['BUY_SEED', crop, empty - have])
            shed_f = int(private['shed'].get('FERTILIZER', 0))
            if fert > shed_f and obs['market']['prices']['FERTILIZER'] <= c['fert_max_price']:
                orders.append(['BUY_PRODUCT', 'FERTILIZER', fert - shed_f])
            cost = sum(_ses_fib(farm['hires_today'] + i) for i in range(k))
            if k and farm['money'] >= cost + 1500 and len(market) + len(orders) + k <= 10:
                market += orders + [['HIRE'] for _ in range(k)]
                st['pending'] = (len(farm['hands']) + 1, k)
            _SES_LOG.append((day, hour, steps, k, len(st['extra']), len(market)))
    # 4. crew commands
    cmds = [action.get('farmer') or ['PASS']] + list(action.get('hands') or [])
    n_units = 1 + len(farm['hands'])
    cmds += [['PASS'] for _ in range(n_units - len(cmds))]
    if st['crew']:
        invs = private['inventories']
        crop = _ses_crop(); fert_a = _ses_info(crop)[1]
        seeds_left = int(private['seeds'].get(crop, 0)) - sum(
            1 for cm in cmds if isinstance(cm, list) and cm[:2] == ['PLANT', crop])
        claimed = set(); shed_f = int(private['shed'].get('FERTILIZER', 0))
        room = 100 - sum(int(v) for v in private['shed'].values())
        k = len(st['crew'])
        for j, actor in enumerate(st['crew']):
            if actor >= n_units:
                continue
            pos = tuple(farm['hands'][actor - 1]); inv = invs[actor] if actor < len(invs) else {}
            mine = [xy for xy in _ses_tiles() if (xy[0] - 5) * k // 5 == j] if k > 1 else _ses_tiles()
            carried = int(inv.get(crop, 0)); fin = int(inv.get('FERTILIZER', 0))
            home = _ses_home(pos); dist = abs(pos[0] - home[0]) + abs(pos[1] - home[1])
            cmd = None
            if carried and (hour >= 22 - dist or carried >= 12):
                cmd = _ses_walk(pos, home) or (['DROP'] if room >= carried else ['PASS'])
                if cmd == ['DROP']:
                    room -= carried
            if cmd is None and pos in _SES_ACCESS and fin == 0 and shed_f > 0 and c['fert']:
                want = sum(1 for (x, y) in mine if isinstance(tiles[y][x], dict) and tiles[y][x].get('crop') == crop
                           and day - tiles[y][x]['planted_day'] in fert_a
                           and tiles[y][x].get('fertilized_until_day', -1) < day)
                if want:
                    q = min(want, shed_f); shed_f -= q
                    cmd = ['PICKUP', 'FERTILIZER', q]
            if cmd is None:
                best = None
                for xy in mine:
                    if xy in claimed:
                        continue
                    x, y = xy
                    jp = _ses_job(tiles[y][x], day, fin, may_plant, xy in st.get('extra', ()))
                    if jp is None:
                        continue
                    job, pr = jp
                    if job[0] == 'PLANT' and (seeds_left <= 0 or hour >= 22):
                        continue
                    d = abs(pos[0] - x) + abs(pos[1] - y)
                    if best is None or (pr, d) < best[0]:
                        best = ((pr, d), xy, job)
                if best:
                    _, xy, job = best; claimed.add(xy)
                    cmd = _ses_walk(pos, xy) or job
                    if cmd[0] == 'PLANT':
                        seeds_left -= 1; _SES_REPORT['ses_plants'] += 1
                    elif cmd[0] == 'WATER':
                        _SES_REPORT['ses_waters'] += 1
                    elif cmd[0] == 'HARVEST':
                        _SES_REPORT['ses_harvests'] += 1
                    elif cmd[0] == 'FERTILIZE':
                        _SES_REPORT['ses_fert'] += 1
            if cmd is None:
                if carried:
                    cmd = _ses_walk(pos, home) or (['DROP'] if room >= carried else ['PASS'])
                    if cmd == ['DROP']:
                        room -= carried
                else:
                    cmd = ['PASS']
            cmds[actor] = cmd
            st['last_cmd'][actor] = cmd
            st['last_inv'][actor] = carried
    # 5. sell SES strawberries from the shed
    if c['sell'] and st['own'] > 0 and len(market) < 10:
        crop = _ses_crop(); q = min(st['own'], int(private['shed'].get(crop, 0)))
        if q > 0 and not any(o[:2] == ['SELL', crop] for o in market):
            market.append(['SELL', crop, q]); st['own'] -= q; _SES_REPORT['ses_sold'] += q
    out = dict(action); out['farmer'] = cmds[0]; out['hands'] = cmds[1:]; out['market'] = market
    return out


def agent(observation, configuration=None):
    step = int(observation['step'])
    st = None
    try:
        st = _ses_state(int(observation['player']), step)
    except Exception as e:
        _SES_REPORT['ses_errors'] += 1; _SES_REPORT['ses_last_error'] = repr(e)[:160]
    obs_in = observation
    try:
        if (_SES_CFG['mask_ad'] and st and st['bought'] and step in _AD_CFG['thresh']):
            obs_in = _ses_mask(observation)
    except Exception as e:
        _SES_REPORT['ses_errors'] += 1; _SES_REPORT['ses_last_error'] = repr(e)[:160]
    action = _SES_PARENT(obs_in, configuration)
    try:
        if st is not None and isinstance(action, dict) and 24 * _SES_CFG['day'] <= step < _SES_CFG['end_step']:
            action = _ses_act(observation, action, st)
    except Exception as e:
        _SES_REPORT['ses_errors'] += 1; _SES_REPORT['ses_last_error'] = repr(e)[:160]
    return action


agent.telemetry = _SES_REPORT
agent = globals().pop('agent')
globals().pop('kaggle_submission_agent', None)
kaggle_submission_agent = agent
