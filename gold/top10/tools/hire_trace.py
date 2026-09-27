"""Hire-search trace of a full build on one elite-gate seat: per controller day and candidate hand count h, the
unserved must/optional visits, planned end-of-day overflow, popped visits and the wage; marks the chosen h.
usage: hire_trace.py games.jsonl.gz refs.jsonl cand_full.py gid seat [day_from]"""
import sys, os, json, collections
sys.path.insert(0, '/home/user/kaggriculture/arena'); sys.path.insert(0, '/home/user/kaggriculture/gold/harness'); sys.path.insert(0, '/home/user/kaggriculture/gold/elite')
import lean
from eval_elite_routes import install_town, load_games
from transplant import build_agent
from kaggle_environments.envs.kaggriculture import kaggriculture as K

path, refs, cand, gid, seat = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
d0 = int(sys.argv[6]) if len(sys.argv) > 6 else 16
ref = next(r for r in map(json.loads, open(refs, encoding='utf-8')) if r['gid'] == gid and r['seat'] == seat)
d = next(g for g in load_games(path) if g['id'] == gid)
s = ref['seat']
rr = dict(hands=ref['hands'], money=ref['money'], outcomes={int(k): v for k, v in ref['outcomes'].items()}, shops=ref['shops'])
orig = install_town(ref['shops'])
A = lean.load(cand)
G = A.__globals__
Ctl = G['GoldCtl']; GC_P = G['GC_P']
LOG = []
ovrp = Ctl._vrp; ops = Ctl._plan_stops
CUR = {}
def vrp(self, visits, h, starts=None, caps=None):
    r = ovrp(self, visits, h, starts, caps)
    if starts is None and caps is None:
        CUR['h'] = h; CUR['un'] = r[2]; CUR['nv'] = len(visits)
        CUR['tags'] = collections.Counter((v.tag, v.must) for v in visits)
    return r
def ps(self, routes, spawns):
    r = ops(self, routes, spawns)
    if 'h' in CUR:
        un = CUR.pop('un'); h = CUR.pop('h')
        LOG.append((self.day, h, sum(1 for v in un if v.must), round(sum(v.value for v in un)), sorted(collections.Counter(v.tag for v in un).items()), r[0], r[1],
                    sum(G['_gc_fib'](q) for q in range(h))))
    return r
Ctl._vrp = vrp; Ctl._plan_stops = ps
orh = Ctl._route_and_hire
CH = {}
def rah(self, visits, cash, final, day):
    r = orh(self, visits, cash, final, day)
    CH[day] = (r[1], CUR.get('nv'), dict(CUR.get('tags', {})))
    return r
Ctl._route_and_hire = rah
try:
    ag = [None, None]; ag[s] = build_agent(d['acts'], s, rr, slack_min=20); ag[1 - s] = A
    res = lean.play(None, None, ref['seed'], agent_objs=ag)
finally:
    K._end_of_day = orig
print('gid', gid, 'seat', s, ref['team'], 'elite', res['r'][s], 'us', res['r'][1 - s], 'm %+.0f' % (res['r'][1 - s] - res['r'][s]), 'ovf_value', GC_P['ovf_value'], 'hire_w', GC_P['hire_cost_w'])
for day in sorted(CH):
    if day < d0: continue
    hc, nv, tags = CH[day]
    print('day %d chosen h=%d  visits %s  %s' % (day, hc, nv, ' '.join('%s%s:%d' % (t, '!' if m else '', n) for (t, m), n in sorted(tags.items()))))
    for (dd, h, nm, uv, ut, ovf, popped, cost) in LOG:
        if dd == day and h >= hc - 2:
            print('    h %2d  unserved must %d value %5d %s  ovf %3d popped %3d  wage %4d%s' % (h, nm, uv, ut, ovf, popped, cost, '  <==' if h == hc else ''))
