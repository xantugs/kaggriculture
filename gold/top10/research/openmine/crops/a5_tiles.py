"""Tile lifecycles (crops/tiles_*.jsonl): per crop cohort (planting-day window) and group:
tiles planted per seat, harvest age, units per tile, fertilized share, waters, how it ended; replant transitions.
usage: a5_tiles.py [tiles_elite.jsonl,tiles_T7.jsonl]"""
import sys, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__))
FILES = (sys.argv[1] if len(sys.argv) > 1 else 'tiles_elite.jsonl,tiles_T7.jsonl').split(',')
AB = {'Boey': 'Boey', 'Fourth Quadrant': 'FQ', '吃白饭的大肥鱼': 'CBF', 'THIRD FARM CLUB': 'TFC', 'Yizhou': 'Yiz', 'T7': 'T7'}
ORDER = ['Boey', 'FQ', 'CBF', 'TFC', 'Yiz', 'T7']


def load():
    S = collections.defaultdict(list)
    for fn in FILES:
        p = os.path.join(HERE, fn)
        if not os.path.exists(p):
            continue
        for l in open(p, encoding='utf-8'):
            r = json.loads(l)
            if r['role'] == 'elite_rep':
                continue
            S[AB[r['team']]].append(r)
    return S


COH = {'WHEAT': [(0, 0), (1, 5), (6, 7), (8, 9), (10, 11), (12, 13), (14, 15)],
       'STRAWBERRY': [(0, 5), (6, 7), (8, 11), (12, 15)],
       'MELON': [(0, 0), (1, 3), (4, 9), (10, 15)],
       'TOMATO': [(8, 11), (12, 15)],
       'CARROT': [(8, 11), (12, 15)]}


def cohort_table(S, crop):
    print(f'\n== {crop} cohorts: tiles/seat | first-harvest age | #harv | units/tile | fert% (tiles fertilized) | '
          f'waters/tile | end H/D/W/open % | last-harvest day')
    for a, b in COH[crop]:
        print(f'-- planted d{a}-{b}')
        for g in ORDER:
            seats = S.get(g) or []
            if not seats:
                continue
            P = [p for s in seats for p in s['plantings'] if p[0] == crop and a <= p[1] <= b]
            if not P:
                print(f'   {g:5s}  0'); continue
            n = len(P)
            hv = [p for p in P if p[8]]
            age = sum(p[8][0][0] - p[1] for p in hv) / max(1, len(hv))
            nh = sum(len(p[8]) for p in P) / n
            u = sum(sum(h[2] for h in p[8]) for p in P) / n
            fe = 100 * sum(1 for p in P if p[7]) / n
            wa = sum(len(p[6]) for p in P) / n
            ends = collections.Counter(p[9] for p in P)
            last = sum(p[8][-1][0] for p in hv) / max(1, len(hv))
            print(f'   {g:5s} {n/len(seats):5.1f} | age {age:4.1f} | {nh:3.1f} | {u:4.2f} | {fe:3.0f}% | {wa:4.1f} | '
                  f'{100*ends["H"]/n:3.0f}/{100*ends["D"]/n:3.0f}/{100*ends["W"]/n:3.0f}/{100*ends[None]/n:3.0f} | {last:4.1f}')


def wheat_age(S):
    print('\n== WHEAT planted d0-15: distribution of harvest age (first harvest - planted) and units at that harvest')
    for g in ORDER:
        seats = S.get(g) or []
        if not seats:
            continue
        P = [p for s in seats for p in s['plantings'] if p[0] == 'WHEAT' and p[1] <= 15]
        c = collections.Counter(); u = collections.defaultdict(list)
        dead = 0
        for p in P:
            if p[8]:
                a = p[8][0][0] - p[1]; c[a] += 1; u[a].append(p[8][0][2])
            else:
                dead += 1
        n = len(P)
        print(f'  {g:5s} n/seat {n/len(seats):5.1f}  ' + '  '.join(f'age{a}: {100*c[a]/n:3.0f}% ({sum(u[a])/max(1,len(u[a])):.1f}u)'
                                                        for a in range(1, 7)) + f'  never harvested {100*dead/n:3.0f}%')


def transitions(S):
    """Next planting on the same tile after a cohort (days 0..15), with gap; 'none<=d16' = no planting by day 16."""
    print('\n== replant: what the same tile gets next (share of tiles), for the main cohorts')
    CO = [('WHEAT', 0, 0), ('WHEAT', 1, 5), ('MELON', 0, 3), ('WHEAT', 6, 7), ('WHEAT', 8, 9), ('STRAWBERRY', 0, 5),
          ('WHEAT', 10, 11)]
    for crop, a, b in CO:
        print(f'-- after {crop} planted d{a}-{b}')
        for g in ORDER:
            seats = S.get(g) or []
            if not seats:
                continue
            c = collections.Counter(); gap = collections.defaultdict(list); n = 0
            for s in seats:
                bytile = collections.defaultdict(list)
                for p in s['plantings']:
                    bytile[(p[3], p[4])].append(p)
                for t, ps in bytile.items():
                    ps.sort(key=lambda p: (p[1], p[2]))
                    for i, p in enumerate(ps):
                        if p[0] == crop and a <= p[1] <= b:
                            n += 1
                            nx = ps[i + 1] if i + 1 < len(ps) else None
                            if nx is None or nx[1] > 16:
                                c['none<=d16'] += 1
                            else:
                                k = f'{nx[0][:5]}'
                                c[k] += 1; gap[k].append(nx[1] - (p[10] if p[10] is not None else p[1]))
            if not n:
                continue
            print(f'   {g:5s} n/seat {n/len(seats):4.1f}: ' + ', '.join(
                f'{k} {100*v/n:3.0f}%' + (f' (+{sum(gap[k])/len(gap[k]):.1f}d)' if gap[k] else '')
                for k, v in c.most_common(6)))


if __name__ == '__main__':
    S = load()
    print('seats', {g: len(S.get(g) or []) for g in ORDER})
    for crop in ('WHEAT', 'STRAWBERRY', 'MELON', 'TOMATO', 'CARROT'):
        cohort_table(S, crop)
    wheat_age(S)
    transitions(S)
