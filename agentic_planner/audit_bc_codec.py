"""Audit the current BC interface with perfect label predictions, without ML deps.

Reads the actual label and decoder functions by AST. Does not modify moon code.
Synthetic cases establish representational defects, not their game-level cost.
Optional replay files audit frequencies on original, exactly reproduced states.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def load_selected(path, names):
    tree = ast.parse(path.read_text(encoding='utf-8'))
    nodes = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            nodes.append(node)
        elif isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id in names for t in node.targets):
            nodes.append(node)
    ns = {}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), ns)
    return ns


CORE_PATH = ROOT / 'moon' / 'bc_core.py'
LAYER_PATH = ROOT / 'moon' / 'bc_layer.py'
CORE = load_selected(CORE_PATH, {
    'UA', 'UA_I', 'QTY', 'ITEMS', 'SELL_BINS', 'BUY_BINS', 'SEED_BINS',
    'MARKET_HEADS', 'MARKET_SIZES', 'qty_bin', 'bin_of', 'unit_label', 'market_labels'})
LAYER = load_selected(LAYER_PATH, {
    '_BC_REPORT', '_BC_ACCESS', '_BC_MOVES', '_BC_ANIM_ST', '_bc_legal', '_bc_act'})


class Vector(list):
    def __neg__(self):
        return Vector(-v for v in self)


class ArrayOps:
    """Only the argmax/argsort operations the actual decoder uses."""
    @staticmethod
    def argmax(v):
        return max(range(len(v)), key=v.__getitem__)

    @staticmethod
    def argsort(v):
        return sorted(range(len(v)), key=v.__getitem__)


def logits(n, index):
    return Vector(1 if i == index else 0 for i in range(n))


def oracle_decode(obs, action):
    """Inject the teacher's true encoded labels into the unchanged decoder."""
    farm = obs['farms'][obs['player']]
    positions = [farm['farmer']] + list(farm['hands'])
    commands = [action.get('farmer', ['PASS'])] + list(action.get('hands') or [])
    labels = [CORE['unit_label'](commands[k] if k < len(commands) else ['PASS'])
              for k in range(len(positions))]
    ml = CORE['market_labels'](action.get('market') or [], obs['private']['shed'])
    output = (
        [logits(len(CORE['UA']), a) for a, q in labels],
        [logits(len(CORE['QTY']), q) for a, q in labels],
        {h: logits(n, ml[h]) for h, n in zip(CORE['MARKET_HEADS'], CORE['MARKET_SIZES'])})
    ns = dict(CORE, np=ArrayOps, W=None, features=None)
    ns['encode'] = lambda *args: (None, None, [(tuple(p), None) for p in positions])
    ns['forward'] = lambda *args: output
    LAYER['_bc_load'] = lambda: ns
    return LAYER['_bc_act'](obs, None)


def synthetic_cases():
    from world import World, PASS
    cases = [
        ('same_turn_delivery_sale', 1000, {}, {'STRAWBERRY': 10},
         {'farmer': ['DROP'], 'market': [['SELL', 'STRAWBERRY', 10]]}),
        ('sale_funds_purchase', 100, {'WOOL': 10}, {},
         {'farmer': ['PASS'], 'market': [['SELL', 'WOOL', 10], ['BUY_ANIMAL', 'COW', 1]]}),
        ('order_and_buy_quantity', 10000, {'WOOL': 10}, {},
         {'farmer': ['PASS'], 'market': [['SELL', 'WOOL', 10], ['BUY_PRODUCT', 'WHEAT', 10]]}),
        ('pickup_quantity', 1000, {'WHEAT': 20}, {},
         {'farmer': ['PICKUP', 'WHEAT', 13], 'market': []}),
        ('selective_deposit', 1000, {}, {'WHEAT': 5, 'STRAWBERRY': 7},
         {'farmer': ['PLACE', 'WHEAT', 1], 'market': []}),
    ]
    out = []
    for name, money, shed, bag, action in cases:
        world = World.new_for_validation(5000)
        world.state[0].observation.farms[0]['money'] = money
        world.state[0].observation.farms[0]['farmer'] = [4, 4]
        private = world.state[0].observation.private
        private['shed'] = shed.copy()
        private['inventories'] = [bag.copy()]
        action['hands'] = []
        decoded = oracle_decode(world.observation(0), action)
        assert decoded != action, name
        outcomes = {}
        for tag, act in [('teacher', action), ('perfect_labels_decoded', decoded)]:
            w = world.fork()
            w.advance([act, PASS])
            outcomes[tag] = {'cash': w.cash()[0], 'private': dict(w.state[0].observation.private)}
        assert outcomes['teacher'] != outcomes['perfect_labels_decoded'], name
        out.append(dict(case=name, teacher=action, decoded=decoded, outcomes=outcomes))
    assert out[0]['decoded']['market'] == []
    assert out[1]['decoded']['market'] == [['SELL', 'WOOL', 10]]
    assert out[2]['decoded']['market'][0] == ['BUY_PRODUCT', 'WHEAT', 8]
    assert out[3]['decoded']['farmer'] == ['PICKUP', 'WHEAT', 12]
    assert out[4]['decoded']['farmer'] == ['DROP']
    return out


def replay_audit(path):
    """Count observable decoder failures without letting them alter replay states."""
    from collections import Counter
    sys.path.insert(0, str(ROOT / 'arena'))
    from lean import K, play
    rep = json.loads(path.read_text(encoding='utf-8'))
    names = (rep.get('info') or {}).get('TeamNames') or []
    acts = rep.get('acts')
    if acts is None:
        acts = [[entry.get('action') for entry in step] for step in rep['steps']]
    counts = [Counter(), Counter()]
    examples = []

    def tape(p):
        def f(obs, cfg):
            t = obs['step']
            action = acts[t + 1][p]
            if not isinstance(action, dict):
                action = {'farmer': ['PASS'], 'hands': [], 'market': []}
            decoded = oracle_decode(obs, action)
            c = counts[p]
            c['turns'] += 1
            c['teacher_sale_turns'] += any(o and o[0] == 'SELL' for o in action.get('market', []))
            farm, priv = copy.deepcopy(obs['farms'][p]), copy.deepcopy(obs['private'])
            commands = [action.get('farmer')] + list(action.get('hands') or [])
            for k, cmd in enumerate(commands):
                K._apply_unit_action(farm, priv, k, cmd, cfg.boardSize, obs['day'],
                                     cfg.turnsPerDay, cfg.shedCapacity)
            # A requested sale has physical stock only AFTER teacher unit actions,
            # but the perfect-label decoder omits it entirely. This is not an
            # estimate of lost income: later sales might recover part of it.
            decoded_goods = {o[1] for o in decoded['market'] if o[0] == 'SELL'}
            lost = []
            for o in action.get('market', []):
                if (len(o) >= 3 and o[0] == 'SELL' and o[2] > 0
                        and obs['private']['shed'].get(o[1], 0) == 0
                        and priv['shed'].get(o[1], 0) > 0 and o[1] not in decoded_goods):
                    lost.append(o[1])
            if lost:
                c['delivery_sale_omitted_turns'] += 1
                c['delivery_sale_omitted_orders'] += len(lost)
                if len(examples) < 6:
                    examples.append(dict(step=t, seat=p, products=lost, teacher=action, decoded=decoded))
            for cmd in commands:
                if isinstance(cmd, list) and len(cmd) >= 3 and cmd[0] == 'PICKUP':
                    a, q = CORE['unit_label'](cmd)
                    if CORE['UA'][a].startswith('PICKUP_'):
                        c['pickup_commands'] += 1
                        c['pickup_requested_quantity_changed'] += CORE['QTY'][q] != cmd[2]
            return action
        return f

    result = play(None, None, rep['info']['seed'], agent_objs=[tape(0), tape(1)])
    assert result['err'] == [None, None], result
    assert list(result['r']) == rep['rewards'], (result['r'], rep['rewards'])
    return dict(file=str(path), teams=names, reproduced_rewards=result['r'],
                counts=[dict(c) for c in counts], examples=examples)


if __name__ == '__main__':
    result = {'method': 'Perfect encoded teacher labels injected into actual BC decoder; no network inference.',
              'source_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in [CORE_PATH, LAYER_PATH]},
              'synthetic': synthetic_cases(),
              'replays': [replay_audit(Path(p)) for p in sys.argv[1:]]}
    destination = Path(__file__).with_suffix('.json')
    destination.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({'synthetic_cases_confirmed': len(result['synthetic']),
                      'replays': [{k: r[k] for k in ('teams', 'reproduced_rewards', 'counts')}
                                  for r in result['replays']], 'report': str(destination)}, indent=2))
