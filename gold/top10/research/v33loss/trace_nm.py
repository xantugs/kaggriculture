"""trace_nm.py GID CAND : play CAND in our seat of ladder game GID vs the repaired rival (ladder_refs), logging both farms per
day with the openmine Logger; print herd / crops / cash / hands / failed actions at key days for us and for the rival."""
import sys, os, json, collections
sys.path.insert(0, os.path.join(os.getcwd(), 'arena')); sys.path.insert(0, os.path.join(os.getcwd(), 'gold/harness')); sys.path.insert(0, os.path.join(os.getcwd(), 'gold/elite')); sys.path.insert(0, 'gold/top10/research/temporal')
import lean, extract_t as X
from eval_elite_routes import install_town
from transplant import build_agent
from kaggle_environments.envs.kaggriculture import kaggriculture as K
sys.stdout.reconfigure(encoding='utf-8')
gid, cand = int(sys.argv[1]), sys.argv[2]
D = 'gold/top10/research/v33loss/'
games = {r['id']: r for r in (json.loads(l) for l in open('gold/top10/research/opening/live_v33.jsonl', encoding='utf-8') if l.startswith('{'))}
ref = [json.loads(l) for l in open(D + 'ladder_refs.jsonl', encoding='utf-8') if json.loads(l)['gid'] == gid][0]
d = games[gid]; s = ref['seat']
rr = dict(hands=ref['hands'], money=ref['money'], outcomes={int(k): v for k, v in ref['outcomes'].items()}, shops=ref['shops'])
orig = install_town(ref['shops'])
L = X.Logger(); L.install()
try:
    ag = [None, None]; ag[s] = build_agent(d['acts'], s, rr, slack_min=20); ag[1 - s] = lean.load(cand)
    r = lean.play(None, None, ref['seed'], agent_objs=ag)
finally:
    L.uninstall(); K._end_of_day = orig
print('result us %.0f rival %.0f' % (r['r'][1 - s], r['r'][s]))
for who, p in (('US', 1 - s), ('RIVAL', s)):
    rows, seat = L.rows(p, dict(gid=gid, seat=p, team=who, opp='', role='x', cand=None), r['r'][p])
    byd = {x['d']: x for x in rows}; cum = collections.Counter()
    for dd in range(30):
        x = byd.get(dd)
        if not x: continue
        for k, v in (x.get('sell') or {}).items(): cum[k] += v[1]
        if dd in (1, 2, 3, 5, 7, 9, 12, 15, 17, 20, 25):
            h = x.get('herd') or {}; c = x.get('crops') or {}
            print('%-5s d%-2d $%6.0f hands %2s herd C%d S%d G%d | W%d St%d M%d T%d Ca%d | shed %s | fail %s' % (who, dd, x.get('m0') or 0, x.get('hands'), h.get('COW', 0), h.get('SHEEP', 0), h.get('GOOSE', 0),
                  c.get('WHEAT', 0), c.get('STRAWBERRY', 0), c.get('MELON', 0), c.get('TOMATO', 0), c.get('CARROT', 0), x.get('shed'), x.get('fail')))
    print('%-5s sold: %s' % (who, ', '.join('%s %.0f' % (k, v) for k, v in sorted(cum.items(), key=lambda kv: -kv[1]))))
