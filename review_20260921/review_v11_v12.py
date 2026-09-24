"""Review diagnostics only; does not edit either submitted agent.

Synthetic cases establish mechanisms, not ladder prevalence. Smoke matches use
the unmodified official engine, independently imported agents, and both seats.
"""
import collections
import copy
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from harness import _load_agent_module, make
from kaggle_environments.envs.kaggriculture import kaggriculture as K

SOURCES = {'v11': Path(r'C:\Users\khant\Downloads\main (5).py'),
           'v12': Path(r'C:\Users\khant\Downloads\main (4).py')}
OUT = Path(__file__).with_name('v11_v12_review_results.json')


def focused_checks():
    mod = _load_agent_module(SOURCES['v12'])
    farm = K._new_farm(10, 30000)
    private = K._new_private()
    private['shed']['WHEAT'] = 10
    farm['tiles'][4][4] = K._new_animal('SHEEP', 0)
    farm['tiles'][4][3] = K._new_animal('COW', 0)
    farm['tiles'][3][3] = K._new_plant('WHEAT', 6, 24)
    farm['tiles'][3][3]['yield_units'] = 4
    schedule = [['PICKUP', 'WHEAT', 1], ['FEED'], ['WEST'], ['FEED'], ['NORTH'], ['HARVEST']]
    tape = [{'farmer': ['PASS'], 'hands': [], 'market': []} for _ in range(720)]
    for offset, cmd in enumerate(schedule):
        tape[240 + offset] = {'farmer': cmd, 'hands': [], 'market': []}
    old_routes, old_players = mod._IMPL.chassis.routes, mod._IMPL.chassis.players
    mod._IMPL.chassis.routes = {99: tape}
    mod._IMPL.chassis.players = {0: {'route': 99}}
    obs = {'step': 240, 'player': 0, 'farms': [farm], 'private': private}
    try:
        result = mod._wf_act(obs, copy.deepcopy(tape[240]))
    finally:
        mod._IMPL.chassis.routes, mod._IMPL.chassis.players = old_routes, old_players
    for offset, cmd in enumerate([result['farmer'], *schedule[1:]]):
        K._apply_unit_action(farm, private, 0, cmd, 10, 10, 24, 100)
    chronological = {'requested_pickup': result['farmer'],
                     'first_animal_fed': farm['tiles'][4][4]['fed_today'],
                     'second_animal_fed': farm['tiles'][4][3]['fed_today'],
                     'wheat_acquired_after_failed_feed': private['inventories'][0]['WHEAT']}
    assert chronological['requested_pickup'] == ['PICKUP', 'WHEAT', 1]
    assert chronological['first_animal_fed'] and not chronological['second_animal_fed']

    # The terminal simulator cannot be used directly for a day-15 rollout.
    try:
        mod._PLANNER_NS['simulate'](obs, {}, [tape[240]])
    except Exception as exc:
        simulator = {'exception': type(exc).__name__, 'message': str(exc)}
    else:
        raise AssertionError('expected terminal-only simulator rejection')

    # Find a small concrete example where a clone-assumption reorder hurts
    # against an asymmetric seller. Compare exact lockstep cash margins.
    market_case = None
    for quantities in [(20, 10, 30), (40, 20, 10), (10, 40, 20), (20, 20, 20)]:
        items = ['STRAWBERRY', 'MILK', 'WOOL']
        f = K._new_farm(10, 30000); p = K._new_private()
        p['shed'].update(dict(zip(items, quantities)))
        inv = {it: 10000 for it in mod.PRODUCTS}
        prices = {it: mod._r37_market_price(it, n) for it, n in inv.items()}
        o = {'step': 400, 'player': 0, 'farms': [f, copy.deepcopy(f)], 'private': p,
             'market': {'inventory': inv, 'prices': prices}}
        act = {'farmer': ['PASS'], 'hands': [], 'market': [['SELL', it, q] for it, q in zip(items, quantities)]}
        after = mod._slot_act(o, copy.deepcopy(act))
        if after == act:
            continue
        for it in items:
            rival = [['SELL', it, 30]]
            rival_stock = {it: 30}
            args = (inv, p['shed'], rival_stock, mod._v44y_params(o))
            a, b = mod._v44y_lockstep(act['market'], rival, *args)
            c, d = mod._v44y_lockstep(after['market'], rival, *args)
            if c - d < a - b:
                market_case = {'before': act['market'], 'after': after['market'],
                               'rival_orders': rival, 'before_margin': a-b,
                               'after_margin': c-d, 'margin_change': (c-d)-(a-b)}
                break
        if market_case:
            break
    assert market_case is not None
    return {'wfeed_temporal_counterexample': chronological,
            'terminal_simulator_scope': simulator,
            'ungated_slot_counterexample': market_case,
            'v44y_reorder_gate_enabled': mod._V44Y_REORDER_GATE}


def smoke(seed, v12_seat):
    names = ['v11', 'v12'] if v12_seat else ['v12', 'v11']
    mods = [_load_agent_module(SOURCES[name]) for name in names]
    counters = [collections.Counter(), collections.Counter()]
    failures = [[], []]
    times = [[], []]
    ids = {}; current = {'step': 0}
    original_apply = K._apply_unit_action
    final_plans = [None, None]

    def apply(farm, private, actor, cmd, *args, **kwargs):
        seat = ids.get(id(farm))
        before = None
        if seat is not None and cmd and cmd[0] in ('FEED', 'FERTILIZE'):
            pos = farm['farmer'] if actor == 0 else farm['hands'][actor-1]
            tile = farm['tiles'][pos[1]][pos[0]]
            if isinstance(tile, dict):
                before = (tuple(pos), copy.deepcopy(tile), dict(private['inventories'][actor]))
        result = original_apply(farm, private, actor, cmd, *args, **kwargs)
        if before is not None:
            pos, old, inv = before
            tile = farm['tiles'][pos[1]][pos[0]]
            if cmd[0] == 'FEED' and old.get('animal') and not old.get('fed_today'):
                counters[seat]['feed_attempts_on_unfed_animals'] += 1
                if not tile.get('fed_today'):
                    counters[seat]['failed_feed'] += 1
                    if not inv.get('WHEAT', 0): counters[seat]['failed_feed_no_carried_wheat'] += 1
                    failures[seat].append({'step': current['step'], 'actor': actor,
                                           'pos': pos, 'op': 'FEED', 'carried_wheat': inv.get('WHEAT', 0),
                                           'shed_wheat': private['shed'].get('WHEAT', 0)})
            if cmd[0] == 'FERTILIZE' and old.get('kind') == 'PLANT':
                counters[seat]['fertilize_attempts_on_plants'] += 1
                if not inv.get('FERTILIZER', 0):
                    counters[seat]['fertilize_no_carried_fertilizer'] += 1
        return result

    def agent(seat):
        def wrapped(obs, config=None):
            start = time.perf_counter()
            act = mods[seat].agent(obs, config)
            times[seat].append(time.perf_counter()-start)
            if obs['step'] == 696:
                final_plans[seat] = {'planned_hands': mods[seat]._FD_STATE.get(seat, {}).get('plan', {}).get('n_hands'),
                                     'hire_orders': sum(bool(o) and o[0] == 'HIRE' for o in act.get('market', []))}
            return act
        return wrapped

    env = make('kaggriculture', debug=True, configuration={'seed': seed})
    interpreter = env.interpreter
    def interpret(state, environment):
        obs = state[0].observation
        if getattr(obs, 'farms', None):
            ids.clear(); ids.update({id(f): i for i, f in enumerate(obs.farms)})
            current['step'] = obs.get('step', 0)
        return interpreter(state, environment)
    env.interpreter = interpret
    K._apply_unit_action = apply
    start = time.perf_counter()
    try:
        env.run([agent(0), agent(1)])
    finally:
        K._apply_unit_action = original_apply
    statuses = [s.status for s in env.steps[-1]]
    assert statuses == ['DONE', 'DONE'], statuses
    return {'seed': seed, 'seats': names, 'scores': [s.reward for s in env.steps[-1]],
            'statuses': statuses, 'counters': counters, 'feed_failures': failures,
            'final_plans': final_plans,
            'telemetry': [{k: getattr(mod, k, {}) for k in ['_WF_REPORT', '_FG_REPORT', '_WRT_REPORT', '_SLOT_REPORT', '_CA_REPORT']} for mod in mods],
            'runtime': [{'mean': sum(ts)/len(ts), 'max': max(ts)} for ts in times],
            'elapsed_seconds': time.perf_counter()-start}


if __name__ == '__main__':
    result = {'focused_checks': focused_checks(), 'smoke_matches': [],
              'limitations': 'Synthetic counterexamples are not measured live losses. Four clone-family smoke games are not a rating estimate or elite benchmark.'}
    print(json.dumps(result['focused_checks']), flush=True)
    OUT.write_text(json.dumps(result, indent=2), encoding='utf-8')
    for seed in [210001, 1461186332]:
        for seat in [0, 1]:
            match = smoke(seed, seat)
            result['smoke_matches'].append(match)
            OUT.write_text(json.dumps(result, indent=2), encoding='utf-8')
            print(json.dumps({k: match[k] for k in ['seed', 'seats', 'scores', 'counters', 'final_plans', 'runtime', 'elapsed_seconds']}), flush=True)
