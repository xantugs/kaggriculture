"""Within-team variants (weak evidence, opponents differ): Boey day-0 3C2S vs 2C3S; TFC with vs without day-2 geese
(20-26 Sep); CBF/Yiz vs herd-first teams. Reports win rate, final money, margin, herd-product net revenue d0-11, SW day."""
import collections
from lib import *
rows = load(role={'rec'})


def herdrev(r, a0, a1):
    t = 0
    for d in range(a0, a1 + 1):
        day = r['days'][d]
        for p in ('EGG', 'MILK', 'WOOL', 'FERTILIZER'):
            t += (day['sell'].get(p) or [0, 0])[1]
        t -= (day['bp'].get('FERTILIZER') or [0, 0])[1]
    return t


def swd(r):
    for day in r['days']:
        for q, h, c in day['land']:
            if q == 'SW':
                return day['d'] + h / 24
    return 30


def show(name, rs):
    print('%-34s n=%3d win %3.0f%% final $%6.0f margin %+6.0f | herd net rev d0-11 $%5.0f d12-29 $%5.0f | SW %.2f | dates %s' % (
        name, len(rs), 100 * mean(r['rew'][0] > r['rew'][1] for r in rs), mean(r['rew'][0] for r in rs),
        mean(r['rew'][0] - r['rew'][1] for r in rs), mean(herdrev(r, 0, 11) for r in rs), mean(herdrev(r, 12, 29) for r in rs),
        mean(min(swd(r), 30) for r in rs), dict(collections.Counter(r['date'][-2:] for r in rs))))


B = [r for r in rows if r['team'] == 'Boey']
show('Boey 3C2S day0', [r for r in B if nbuy(r['days'][0], 'COW') == 3])
show('Boey 2C3S day0', [r for r in B if nbuy(r['days'][0], 'COW') == 2])
show('Boey geese by d3', [r for r in B if sum(nbuy(r['days'][d], 'GOOSE') for d in range(4))])
show('Boey no geese by d3', [r for r in B if not sum(nbuy(r['days'][d], 'GOOSE') for d in range(4))])
T = [r for r in rows if r['team'] == 'THIRD FARM CLUB']
show('TFC geese by d3', [r for r in T if sum(nbuy(r['days'][d], 'GOOSE') for d in range(4))])
show('TFC no geese by d3', [r for r in T if not sum(nbuy(r['days'][d], 'GOOSE') for d in range(4))])
# same opponents only: TFC vs opponents faced by both variants
opp_g = collections.defaultdict(lambda: [[], []])
for r in T:
    g = 1 if sum(nbuy(r['days'][d], 'GOOSE') for d in range(4)) else 0
    opp_g[r['opp']][g].append(r)
both = [o for o, v in opp_g.items() if len(v[0]) >= 3 and len(v[1]) >= 3]
w0 = [mean(r['rew'][0] - r['rew'][1] for r in opp_g[o][0]) for o in both]
w1 = [mean(r['rew'][0] - r['rew'][1] for r in opp_g[o][1]) for o in both]
f0 = [mean(r['rew'][0] for r in opp_g[o][0]) for o in both]
f1 = [mean(r['rew'][0] for r in opp_g[o][1]) for o in both]
print('TFC opponent-matched (%d opponents with >=3 games each variant): margin no-geese %+.0f vs geese %+.0f ; final %.0f vs %.0f' % (len(both), mean(w0), mean(w1), mean(f0), mean(f1)))
