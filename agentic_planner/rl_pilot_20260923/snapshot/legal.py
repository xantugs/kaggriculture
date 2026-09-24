_BC_ACCESS = ((4, 4), (5, 4), (4, 5), (5, 5))
_BC_MOVES = {'NORTH': (0, -1), 'SOUTH': (0, 1), 'EAST': (1, 0), 'WEST': (-1, 0)}
_BC_ANIM_ST = {'GOOSE': 'COOP', 'COW': 'PASTURE', 'SHEEP': 'PASTURE'}


def _bc_legal(a, pos, tile, inv, shed_left, seeds_left, locked):
    x, y = pos
    if a in _BC_MOVES:
        dx, dy = _BC_MOVES[a]
        return 0 <= x + dx < 10 and 0 <= y + dy < 10
    if a == 'PASS':
        return True
    is_plant = isinstance(tile, dict) and tile.get('kind') == 'PLANT'
    is_anim = isinstance(tile, dict) and 'animal' in tile
    at_shed = (x, y) in _BC_ACCESS
    if a.startswith('PICKUP_'):
        return at_shed and shed_left.get(a[7:], 0) > 0
    if a == 'DROP':
        return at_shed and any(v > 0 for v in inv.values())
    if a.startswith('DEPOSIT_'):
        return at_shed and inv.get(a[8:], 0) > 0
    if locked:
        return False
    if a == 'WATER':
        return is_plant and not tile.get('watered_today')
    if a == 'HARVEST':
        return isinstance(tile, dict) and tile.get('yield_units', 0) > 0 and (is_anim or is_plant)
    if a == 'FERTILIZE':
        return is_plant and inv.get('FERTILIZER', 0) > 0
    if a == 'FEED':
        return is_anim and not tile.get('fed_today') and inv.get('WHEAT', 0) > 0
    if a == 'CARE':
        return is_anim and not tile.get('cared_today')
    if a == 'COLLECT_FERTILIZER':
        return is_anim and tile.get('fertilizer_available')
    if a == 'DIG':
        return tile is not None and not is_anim
    if a.startswith('PLANT_'):
        return tile is None and seeds_left.get(a[6:], 0) > 0
    if a in ('BUILD_COOP', 'BUILD_PASTURE'):
        return tile is None
    if a.startswith('PLACE_'):
        an = a[6:]
        return isinstance(tile, dict) and tile.get('kind') == _BC_ANIM_ST[an] and 'animal' not in tile and inv.get(an, 0) > 0
    return False


