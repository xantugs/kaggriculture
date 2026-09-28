"""Step trace of our seat in one goldg/top10g game: actions, market orders, cash, queue heads.
usage: trace.py games.gz refs cand gid step0 step1 [tilefilter]"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
KG = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..', '..'))
for p in ('arena', 'gold/harness', 'gold/elite', 'gold/top10/research/openmine'):
    sys.path.insert(0, os.path.join(KG, p))
import lean
from eval_elite_routes import install_town, load_games
from transplant import build_agent
from kaggle_environments.envs.kaggriculture import kaggriculture as K
path, refs, cand, gid, s0, s1 = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])
ref = [json.loads(l) for l in open(refs, encoding='utf-8') if json.loads(l)['gid'] == gid][0]
d = [g for g in load_games(path) if g['id'] == gid][0]
s = ref['seat']
rr = dict(hands=ref['hands'], money=ref['money'], outcomes={int(k): v for k, v in ref['outcomes'].items()}, shops=ref['shops'])
orig = install_town(ref['shops'])
A = lean.load(cand)
OUT = open(os.path.join(HERE, 'out', 'trace.txt'), 'w', encoding='utf-8')
def print(*a):
    OUT.write(' '.join(str(x) for x in a) + chr(10)); OUT.flush()
G = A.__globals__
def wrap_old(obs, cfg=None):
    a = A(obs, cfg)
    st = int(obs['step'])
    if s0 <= st <= s1:
        me = int(obs['player']); f = obs['farms'][me]
        gc = G.get('_GC')
        qs = {u: [(tuple(t), a_[0] + (':' + str(a_[1]) if len(a_) > 1 else '')) for t, a_, v in (q or [])[:4]] for u, q in (gc.queues or {}).items()} if gc else {}
        units = [f['farmer']] + list(f['hands'])
        print('s%d d%d h%d $%.0f inv=%s' % (st, st // 24, st % 24, f['money'], [dict((k, v) for k, v in dict(i).items() if v) for i in obs['private']['inventories']]))
        print('   acts farmer=%s hands=%s' % (a.get('farmer'), a.get('hands')))
        print('   mkt=%s' % a.get('market'))
        for u, p in enumerate(units):
            print('   u%d @%s q=%s' % (u, tuple(p), qs.get(u)))
    return a

def wrap(obs, cfg=None):
    a = A(obs, cfg)
    st = int(obs['step'])
    if s0 <= st <= s1 and st % 24 in (0, 12, 23):
        me = int(obs['player']); f = obs['farms'][me]
        rows = []
        for y in range(10):
            for x in range(10):
                t = f['tiles'][y][x]
                if isinstance(t, dict) and (t.get('crop') in ('STRAWBERRY', 'TOMATO') or t.get('kind') == 'WEED'):
                    rows.append('%s%d,%d:p%s/cu%s/w%d/y%s' % ((t.get('crop') or 'WEED')[:2], x, y, t.get('planted_day'), t.get('consecutive_unwatered'), 1 if t.get('watered_today') else 0, t.get('yield_units')))
        print('s%d d%d h%d hands=%d unserved=%s  %s' % (st, st // 24, st % 24, len(f['hands']), (G.get('_GC').__dict__.get('_last_unserved')), ' '.join(rows)))
    return a
ag = [None, None]; ag[s] = build_agent(d['acts'], s, rr, slack_min=20); ag[1 - s] = wrap
r = lean.play(None, None, ref['seed'], agent_objs=ag, max_steps=s1 + 1)
