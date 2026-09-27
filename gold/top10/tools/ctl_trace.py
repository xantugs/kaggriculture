"""Controller day plans of a full build on one elite-gate seat: tiles, footprint, plantings chosen, hires, unserved.
usage: ctl_trace.py games.jsonl.gz refs.jsonl cand_full.py gid seat [day_from]"""
import sys, os, json, collections
sys.path.insert(0, '/home/user/kaggriculture/arena'); sys.path.insert(0, '/home/user/kaggriculture/gold/harness'); sys.path.insert(0, '/home/user/kaggriculture/gold/elite')
import lean
from eval_elite_routes import install_town, load_games
from transplant import build_agent
from kaggle_environments.envs.kaggriculture import kaggriculture as K

path, refs, cand, gid, seat = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
d0 = int(sys.argv[6]) if len(sys.argv) > 6 else 15
ref = next(r for r in map(json.loads, open(refs, encoding='utf-8')) if r['gid'] == gid and r['seat'] == seat)
d = next(g for g in load_games(path) if g['id'] == gid)
s = ref['seat']
rr = dict(hands=ref['hands'], money=ref['money'], outcomes={int(k): v for k, v in ref['outcomes'].items()}, shops=ref['shops'])
orig = install_town(ref['shops'])
A = lean.load(cand)
G = A.__globals__
Ctl = G['GoldCtl']
opd = Ctl.plan_day
LOG = []
def pd(self, obs):
    r = opd(self, obs)
    day = int(obs['step']) // 24
    farm = obs['farms'][self.me]
    c = collections.Counter(); empt = []
    for y in range(10):
        for x in range(10):
            t = farm['tiles'][y][x]
            q = ('N' if y < 5 else 'S') + ('W' if x < 5 else 'E')
            if t == 'LOCKED': continue
            if t is None: c['empty'] += 1; empt.append((x, y))
            elif t.get('crop'): c[t['crop'][:4]] += 1
            elif t.get('animal'): c['anim'] += 1
            else: c[str(t.get('kind'))[:4]] += 1
    pl = collections.Counter()
    for rt in self.routes:
        for v in rt:
            for a in v.acts:
                if a[0] == 'PLANT': pl[a[1][:4]] += 1
                if a[0] == 'HARVEST':
                    t = farm['tiles'][v.pos[1]][v.pos[0]]
                    if isinstance(t, dict) and t.get('crop') in ('WHEAT', 'CARROT'):
                        pl['h' + t['crop'][:1] + str(day - int(t['planted_day']))] += 1
    LOG.append('day %2d money %6d quads %s | %s | fp %s bonus %s | hires %d unserved %s | planned %s' % (
        day, int(farm['money']), ''.join(q[0] + q[1] for q in farm['unlocked_quadrants']), ' '.join('%s:%d' % kv for kv in sorted(c.items())),
        getattr(self, 'footprint_n', None), getattr(self, 'fp_bonus', 0), self.hires_planned, getattr(self, '_last_unserved', None),
        ' '.join('%s:%d' % kv for kv in sorted(pl.items()))))
    return r
Ctl.plan_day = pd
try:
    ag = [None, None]; ag[s] = build_agent(d['acts'], s, rr, slack_min=20); ag[1 - s] = A
    res = lean.play(None, None, ref['seed'], agent_objs=ag)
finally:
    K._end_of_day = orig
print('gid', gid, 'seat', s, ref['team'], 'elite', res['r'][s], 'us', res['r'][1 - s], 'm %+.0f' % (res['r'][1 - s] - res['r'][s]))
for l in LOG:
    if int(l[4:6]) >= d0: print(l)
tel = A.telemetry
print({k: v for k, v in tel.items() if isinstance(v, (int, float, str)) and v})
