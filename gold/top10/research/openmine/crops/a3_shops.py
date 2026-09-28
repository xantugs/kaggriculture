"""Crop decisions conditional on shops known (town unlocked_shops at hour 0 of the decision day).
Shops unlock at the end of days 2, 5, 8, 11, 14 (known from days 3, 6, 9, 12, 15).
usage: a3_shops.py"""
import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from a1_plant import G, AB, TEAMS, CR, plants

order = TEAMS + ['T7']
BUY = {'STRAWBERRY': {'BRUNCH_SPOT', 'ICE_CREAM_SHOP', 'SMOOTHIE_SHOP', 'FARMERS_MARKET'},
       'TOMATO': {'PIZZA_SHOP', 'FARMERS_MARKET'}, 'CARROT': {'PET_CAFE', 'FARMERS_MARKET'},
       'WHEAT': {'BAKERY', 'PIZZA_SHOP', 'BRUNCH_SPOT', 'ICE_CREAM_SHOP', 'FARMERS_MARKET'},
       'MILK': {'PIZZA_SHOP', 'ICE_CREAM_SHOP', 'SMOOTHIE_SHOP'}, 'WOOL': {'YARN_STORE'},
       'EGG': {'BAKERY', 'BRUNCH_SPOT'}}


def nbuy(row, item):
    return sum(1 for s in (row['shops'] or []) if s in BUY[item])


def tab(title, crop, a, b, cond_day, item, buckets=((0, 0), (1, 1), (2, 9))):
    print(f'\n== {title}: {crop} planted d{a}-{b}, by # {item} buyers known on day {cond_day}  [mean (share>0) n]')
    print('buyers ' + ''.join(f'{AB[t]:>20s}' for t in order))
    for lo, hi in buckets:
        line = f' {lo}-{hi}   '
        for t in order:
            xs = [sum(plants(r[d], crop) for d in range(a, b + 1)) for r in G[t] if lo <= nbuy(r[cond_day], item) <= hi]
            n = len(xs)
            line += f'{(sum(xs)/n if n else 0):6.1f} ({(100*sum(x>0 for x in xs)/n if n else 0):3.0f}) {n:4d}  '
        print(line)


if __name__ == '__main__':
    tab('early strawberries (first shop known d3)', 'STRAWBERRY', 3, 5, 3, 'STRAWBERRY', ((0, 0), (1, 1)))
    tab('day-2 strawberries (no shop known yet; outcome split)', 'STRAWBERRY', 2, 2, 3, 'STRAWBERRY', ((0, 0), (1, 1)))
    tab('NE strawberry batch', 'STRAWBERRY', 6, 7, 6, 'STRAWBERRY', ((0, 0), (1, 1), (2, 2)))
    tab('SW strawberries', 'STRAWBERRY', 8, 11, 9, 'STRAWBERRY', ((0, 0), (1, 1), (2, 3)))
    tab('late strawberries', 'STRAWBERRY', 12, 15, 12, 'STRAWBERRY', ((0, 0), (1, 1), (2, 4)))
    tab('tomatoes', 'TOMATO', 9, 15, 9, 'TOMATO', ((0, 0), (1, 1), (2, 3)))
    tab('tomatoes (d12 shops)', 'TOMATO', 12, 15, 12, 'TOMATO', ((0, 0), (1, 1), (2, 4)))
    tab('carrots', 'CARROT', 8, 15, 9, 'CARROT', ((0, 0), (1, 1), (2, 3)))
    tab('carrots (d12 shops)', 'CARROT', 12, 15, 12, 'CARROT', ((0, 0), (1, 1), (2, 4)))
    tab('wheat d8-11', 'WHEAT', 8, 11, 9, 'WHEAT', ((0, 0), (1, 1), (2, 3)))
    tab('wheat d6-7', 'WHEAT', 6, 7, 6, 'WHEAT', ((0, 0), (1, 1), (2, 2)))
    tab('melon replant d10-15', 'MELON', 10, 15, 12, 'STRAWBERRY', ((0, 0), (1, 1), (2, 4)))
    tab('melons d1-3 (by d3 straw shop)', 'MELON', 1, 3, 3, 'STRAWBERRY', ((0, 0), (1, 1)))
