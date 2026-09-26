"""Add the wool-first V233 crew (v233_wool_first) to a lean build: lean_patch_wf.py in.py out.py"""
import sys
src = open(sys.argv[1], encoding='utf-8').read()
func = '''
def _v233_worker_wool_first(obs, actor, targets):
    farm = obs['farms'][obs['player']]; private = obs['private']; step = int(obs['step'])
    pos = tuple(farm['hands'][actor - 1]); inv = private['inventories'][actor]
    access = ((4, 4), (5, 4), (4, 5), (5, 5))
    home = min(access, key=lambda p: (abs(pos[0] - p[0]) + abs(pos[1] - p[1]), p))
    distance = abs(pos[0] - home[0]) + abs(pos[1] - home[1])
    cargo = [item for item in ('WOOL', 'FERTILIZER') if inv.get(item, 0)]
    if cargo and step % 24 >= (22 if step // 24 == 29 else 23) - distance:
        return _v219_walk(pos, home) or ['PLACE', cargo[0], inv[cargo[0]]]
    missing = sum(not (isinstance(farm['tiles'][y][x], dict) and farm['tiles'][y][x].get('animal') == 'SHEEP') for x, y in targets)
    if missing and not inv.get('SHEEP', 0) and private['shed'].get('SHEEP', 0):
        return _v219_walk(pos, home) or ['PICKUP', 'SHEEP', min(missing, private['shed']['SHEEP'])]
    hungry = sum(not (isinstance(farm['tiles'][y][x], dict) and farm['tiles'][y][x].get('fed_today')) for x, y in targets)
    if hungry and not inv.get('WHEAT', 0) and private['shed'].get('WHEAT', 0):
        return _v219_walk(pos, home) or ['PICKUP', 'WHEAT', min(hungry, private['shed']['WHEAT'])]
    wool_left = any(isinstance(farm['tiles'][y][x], dict) and farm['tiles'][y][x].get('animal') == 'SHEEP'
                    and int(farm['tiles'][y][x].get('yield_units', 0) or 0) > 0 for x, y in targets)
    busy = wool_left or inv.get('WOOL', 0) > 0
    tasks = []
    for target in targets:
        x, y = target; tile = farm['tiles'][y][x]; command = None
        if tile is None: command = ['BUILD_PASTURE']
        elif isinstance(tile, dict) and tile.get('kind') == 'WEED': command = ['DIG']
        elif isinstance(tile, dict) and tile.get('kind') == 'PASTURE' and not tile.get('animal'):
            if inv.get('SHEEP', 0): command = ['PLACE', 'SHEEP']
        elif isinstance(tile, dict) and tile.get('animal') == 'SHEEP':
            if not tile['fed_today'] and inv.get('WHEAT', 0): command = ['FEED']
            elif not tile['cared_today']: command = ['CARE']
            elif tile['yield_units']: command = ['HARVEST']
            elif tile['fertilizer_available'] and not busy: command = ['COLLECT_FERTILIZER']
        if command: tasks.append((abs(pos[0] - x) + abs(pos[1] - y), targets.index(target), target, command))
    if inv.get('WOOL', 0) and not wool_left and not any(c[0] in ('FEED', 'CARE', 'BUILD_PASTURE', 'PLACE', 'DIG') for _d, _i, _t, c in tasks):
        return _v219_walk(pos, home) or ['PLACE', 'WOOL', inv['WOOL']]
    if tasks:
        _, _, target, command = min(tasks)
        return _v219_walk(pos, target) or command
    if cargo: return _v219_walk(pos, home) or ['PLACE', cargo[0], inv[cargo[0]]]
    return ['PASS']
_SL_WORKER = _v233_worker_wool_first
'''
a = "_SL_WORKER = _v233_worker\n"
assert src.count(a) == 1
src = src.replace(a, a + func, 1)
open(sys.argv[2], 'w', encoding='utf-8').write(src)
print('patched', sys.argv[2])
