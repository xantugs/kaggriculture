"""Elite farm composition as a function of the shops revealed, from ledger replays.
usage: composition_table.py elite_ledger.jsonl ours_ledger.jsonl [teams=A,B|WINNERS]
Buckets each game/seat by the demand for a product among the shops known at day D (12: 4 shops, 18: 6, 24: 8) and
prints mean tile counts for elite seats vs our live seats."""
import sys, json, collections
US = 'offhand'
SHOPS = {"BAKERY": ["EGG", "WHEAT"], "PIZZA_SHOP": ["MILK", "TOMATO", "WHEAT"], "BRUNCH_SPOT": ["EGG", "WHEAT", "STRAWBERRY"],
         "YARN_STORE": ["WOOL"], "ICE_CREAM_SHOP": ["STRAWBERRY", "MILK", "WHEAT"], "PET_CAFE": ["CARROT"],
         "SMOOTHIE_SHOP": ["STRAWBERRY", "MILK"], "FARMERS_MARKET": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"]}
PROD_TILE = {'TOMATO': 'TOMATO', 'STRAWBERRY': 'STRAWBERRY', 'CARROT': 'CARROT', 'WHEAT': 'WHEAT', 'EGG': 'GOOSE', 'MILK': 'COW', 'WOOL': 'SHEEP', 'MELON': 'MELON'}

def demand(shops, prod):
    # daily units the known shops drain: 6 per multi-product shop, 12 per single-product shop
    return sum((12 if len(SHOPS[s]) == 1 else 6) for s in shops if prod in SHOPS[s])

def comp_at(r, seat, day):
    c = r['comp'].get(str(day)) or r['comp'].get(day)
    return (c[seat] if c and c[seat] else None)

def rows_of(path, pick):
    out = []
    for l in open(path, encoding='utf-8'):
        r = json.loads(l)
        for s in (0, 1):
            if pick(r, s):
                out.append((r, s))
    return out

if __name__ == '__main__':
    elite_path, ours_path = sys.argv[1], sys.argv[2]
    teams = sys.argv[3] if len(sys.argv) > 3 else 'WINNERS'
    if teams == 'WINNERS':
        elite = rows_of(elite_path, lambda r, s: r['rewards'][s] is not None and r['rewards'][1 - s] is not None and r['rewards'][s] > r['rewards'][1 - s])
    else:
        want = set(teams.split(','))
        elite = rows_of(elite_path, lambda r, s: r['names'][s] in want)
    ours = rows_of(ours_path, lambda r, s: r['names'][s] == US)
    print(f'elite seats {len(elite)}, our live seats {len(ours)}')
    print('\n=== mean composition (tiles) by day: elite vs ours ===')
    for day in (6, 12, 18, 24):
        line = f'day {day:2d} | '
        for tile in ('WHEAT', 'MELON', 'STRAWBERRY', 'TOMATO', 'CARROT', 'COW', 'SHEEP', 'GOOSE', 'empty', 'LOCKED'):
            e = [comp_at(r, s, day).get(tile, 0) for r, s in elite if comp_at(r, s, day)]
            o = [comp_at(r, s, day).get(tile, 0) for r, s in ours if comp_at(r, s, day)]
            if tile == 'LOCKED':
                e = [100 - sum(v for k, v in comp_at(r, s, day).items()) for r, s in elite if comp_at(r, s, day)]
                o = [100 - sum(v for k, v in comp_at(r, s, day).items()) for r, s in ours if comp_at(r, s, day)]
                tile = 'locked'
            line += f'{tile[:6]:6s} {sum(e)/max(1,len(e)):5.1f}/{sum(o)/max(1,len(o)):5.1f}  '
        print(line)
    print('\n=== tiles at day D by demand for the product among shops known at D (elite / ours, n) ===')
    for prod, tile in (('TOMATO', 'TOMATO'), ('STRAWBERRY', 'STRAWBERRY'), ('CARROT', 'CARROT'), ('EGG', 'GOOSE'), ('WOOL', 'SHEEP'), ('MILK', 'COW')):
        for day in (12, 18, 24):
            k = day // 3
            be = collections.defaultdict(list); bo = collections.defaultdict(list)
            for r, s in elite:
                c = comp_at(r, s, day)
                if c: be[min(demand(r['shops'][:k], prod), 24)].append(c.get(tile, 0))
            for r, s in ours:
                c = comp_at(r, s, day)
                if c: bo[min(demand(r['shops'][:k], prod), 24)].append(c.get(tile, 0))
            keys = sorted(set(be) | set(bo))
            print(f"  {prod[:6]:6s} d{day:2d}: " + '  '.join(f"dem{d:2d}: {sum(be[d])/max(1,len(be[d])):4.1f}/{sum(bo[d])/max(1,len(bo[d])):4.1f} (n {len(be[d])}/{len(bo[d])})" for d in keys))
    print('\n=== elite final cash and tomato tiles at day 18 by tomato demand known at day 12 ===')
    b = collections.defaultdict(list)
    for r, s in elite:
        c = comp_at(r, s, 18)
        if c: b[demand(r['shops'][:4], 'TOMATO')].append((r['rewards'][s], c.get('TOMATO', 0)))
    for d in sorted(b):
        v = b[d]; print(f"  tomato demand {d:2d} at day 12: n {len(v):3d}, cash {sum(x for x, _ in v)/len(v):7.0f}, tomato tiles d18 {sum(y for _, y in v)/len(v):4.1f}")
