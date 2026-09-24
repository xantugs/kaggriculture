"""Labor model of a team from exact replays of its recorded games (both seats replayed from their action tapes).
For days D0..D1 it measures, per team-day:
  units, hire hours, per-unit turns (move / useful op / shed / pass), distinct tiles worked per unit, zone spread,
  watering of one-time crops by age (in-window vs outside), watering of ongoing crops on eve vs non-eve days,
  feed / care / harvest / collect frequency per animal-day, fertilize by crop, shed trips per unit, owned quadrants,
  tile use by kind, and whether a unit stays within one quadrant.
usage: laborprof.py team max_games D0 D1 files..."""
import sys, os, json, collections, random
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
from concurrent.futures import ProcessPoolExecutor

MOVES = {'NORTH': (0, -1), 'SOUTH': (0, 1), 'EAST': (1, 0), 'WEST': (-1, 0)}
CROPS = {'WHEAT': (2, 4, False, 0), 'CARROT': (2, 3, False, 0), 'TOMATO': (8, 8, True, 1), 'STRAWBERRY': (10, 10, True, 2), 'MELON': (10, 12, False, 0)}


def quad(x, y):
    return ('N' if y < 5 else 'S') + ('W' if x < 5 else 'E')


def job(d):
    import lean, pinned
    team, D0, D1 = d['_team'], d['_D0'], d['_D1']
    n = d['info']['TeamNames']; P = n.index(team)
    st = collections.Counter(); per_unit = []
    state = {}

    def wrap_factory(p, inner):
        def f(obs, cfg=None):
            a = inner(obs, cfg)
            if p == P:
                s = int(obs['step']); day = s // 24; hour = s % 24
                if D0 <= day <= D1 and isinstance(a, dict):
                    farm = obs['farms'][p]; priv = obs['private']
                    units = [tuple(farm['farmer'])] + [tuple(h) for h in farm['hands']]
                    cmds = [a.get('farmer') or ['PASS']] + list(a.get('hands') or [])
                    if hour == 0:
                        st['days'] += 1
                        st['quads'] += len(farm['unlocked_quadrants'])
                        for row in farm['tiles']:
                            for t in row:
                                if t == 'LOCKED': continue
                                k = 'empty' if t is None else (t.get('kind') if t.get('kind') in ('WEED', 'PLANT') else ('animal' if t.get('animal') else 'struct'))
                                if k == 'PLANT': k = 'crop_' + t['crop']
                                st['tile_' + k] += 1
                        state['uz'] = collections.defaultdict(set); state['ut'] = collections.Counter()
                        state['day'] = day
                    for o in a.get('market') or []:
                        if o and o[0] == 'HIRE':
                            st['hires'] += 1; st['hire_h%02d' % hour] += 1
                    st['unit_turns'] += len(units)
                    for i, pos in enumerate(units):
                        c = cmds[i] if i < len(cmds) and cmds[i] else ['PASS']
                        op = c[0]
                        if op in MOVES: st['t_move'] += 1; continue
                        if op in ('PICKUP', 'DROP') or (op == 'PLACE' and pos in ((4, 4), (5, 4), (4, 5), (5, 5)) and not (isinstance(farm['tiles'][pos[1]][pos[0]], dict) and farm['tiles'][pos[1]][pos[0]].get('kind') in ('COOP', 'PASTURE'))):
                            st['t_shed'] += 1; st['shed_' + op] += 1; continue
                        if op == 'PASS': st['t_pass'] += 1; continue
                        st['t_useful'] += 1; st['op_' + op] += 1
                        state['uz'][i].add(pos); state['ut'][i] += 1
                        x, y = pos; t = farm['tiles'][y][x]
                        if isinstance(t, dict) and t.get('kind') == 'PLANT':
                            crop = t['crop']; fy, my, ongoing, iv = CROPS[crop]; age = day - t['planted_day']
                            if op == 'WATER':
                                if not ongoing:
                                    w0 = (my + 1) // 2
                                    st['water_1t_' + ('inwin' if w0 <= age <= my else ('age0' if age == 0 else 'outwin'))] += 1
                                else:
                                    k_next = age + 1 - fy
                                    eve = k_next >= 0 and k_next % iv == 0
                                    st['water_on_' + ('eve' if eve else ('young' if age < fy - 1 else 'noneve'))] += 1
                            elif op == 'FERTILIZE':
                                st['fert_' + crop] += 1
                            elif op == 'HARVEST':
                                st['harv_' + crop] += 1; st['harv_units_' + crop] += t.get('yield_units', 0)
                        elif isinstance(t, dict) and t.get('animal'):
                            st['anim_' + op] += 1
                    if hour == 23:
                        for i in state['uz']:
                            tiles = state['uz'][i]
                            if not tiles: continue
                            st['unitdays'] += 1; st['unit_tiles'] += len(tiles)
                            qs = {quad(x, y) for x, y in tiles}
                            st['unit_quads'] += len(qs); st['unit_1quad'] += len(qs) == 1
                            xs = [x for x, y in tiles]; ys = [y for x, y in tiles]
                            st['unit_span'] += (max(xs) - min(xs)) + (max(ys) - min(ys))
                        animals = sum(1 for row in farm['tiles'] for t in row if isinstance(t, dict) and t.get('animal'))
                        st['animal_days'] += animals
            return a
        return f
    try:
        A = [wrap_factory(0, pinned._tape(d['acts'], 0)), wrap_factory(1, pinned._tape(d['acts'], 1))]
        r = lean.play(None, None, d['info']['seed'], agent_objs=A)
        ok = [int(x) for x in r['r']] == [int(x) for x in d['rewards']]
    except Exception as e:
        return None
    return dict(st) if ok else None


if __name__ == '__main__':
    team, mx, D0, D1, files = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5:]
    gs = []
    for f in files:
        it = (json.loads(l) for l in open(f, encoding='utf-8')) if f.endswith('.jsonl') else json.load(open(f, encoding='utf-8'))
        for d in it:
            if team in (d['info'].get('TeamNames') or []):
                d['_team'] = team; d['_D0'] = D0; d['_D1'] = D1; gs.append(d)
    random.Random(1).shuffle(gs); gs = gs[:mx]
    tot = collections.Counter(); ng = 0
    with ProcessPoolExecutor(int(os.environ.get('WORKERS', '8'))) as ex:
        for r in ex.map(job, gs):
            if r: tot.update(r); ng += 1
    days = max(1, tot['days'])
    print(f"{team}: games {ng}, team-days {days} (days {D0}-{D1})")
    print(f"  quadrants owned avg {tot['quads'] / days:.2f}; units/day {tot['unit_turns'] / days / 24:.1f}; hires/day {tot['hires'] / days:.1f}")
    print('  hire hours:', {k[-2:]: round(v / days, 2) for k, v in sorted(tot.items()) if k.startswith('hire_h')})
    ut = max(1, tot['unit_turns'])
    print(f"  turns/day {ut / days:.0f}: move {tot['t_move'] / ut:.2f} useful {tot['t_useful'] / ut:.2f} shed {tot['t_shed'] / ut:.2f} pass {tot['t_pass'] / ut:.2f}")
    print('  useful ops/day:', {k[3:]: round(v / days, 1) for k, v in sorted(tot.items(), key=lambda kv: -kv[1]) if k.startswith('op_')})
    print('  shed ops/day:', {k[5:]: round(v / days, 1) for k, v in tot.items() if k.startswith('shed_')})
    ud = max(1, tot['unitdays'])
    print(f"  per working unit-day: tiles {tot['unit_tiles'] / ud:.1f}, quadrants {tot['unit_quads'] / ud:.2f}, single-quadrant {tot['unit_1quad'] / ud:.2f}, bbox span {tot['unit_span'] / ud:.1f}")
    print('  tile use/day:', {k[5:]: round(v / days, 1) for k, v in sorted(tot.items(), key=lambda kv: -kv[1]) if k.startswith('tile_')})
    ad = max(1, tot['animal_days'])
    print(f"  per animal-day: feed {tot['anim_FEED'] / ad:.2f} care {tot['anim_CARE'] / ad:.2f} harvest {tot['anim_HARVEST'] / ad:.2f} collect {tot['anim_COLLECT_FERTILIZER'] / ad:.2f}")
    print('  one-time-crop waterings/day:', {k[9:]: round(v / days, 1) for k, v in tot.items() if k.startswith('water_1t_')})
    print('  ongoing-crop waterings/day:', {k[9:]: round(v / days, 1) for k, v in tot.items() if k.startswith('water_on_')})
    print('  fertilize/day:', {k[5:]: round(v / days, 1) for k, v in tot.items() if k.startswith('fert_')})
    print('  harvests/day (units/harvest):', {k[5:]: f"{v / days:.1f} ({tot['harv_units_' + k[5:]] / max(1, v):.1f})" for k, v in tot.items() if k.startswith('harv_') and not k.startswith('harv_units')})
