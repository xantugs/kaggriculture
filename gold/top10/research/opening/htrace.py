"""htrace.py cand gid seat_of_elite d0 d1 : per-step trace of our units (action, position) and shed melons on days d0..d1,
in the elite-gate set-up (repaired elite rival in its town)."""
import sys, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__))
OM = os.path.join(os.path.dirname(HERE), 'openmine')
KG = os.path.normpath(os.path.join(OM, '..', '..', '..', '..'))
sys.path.insert(0, OM)
for p in ('arena', 'gold/harness', 'gold/elite'):
    sys.path.insert(0, os.path.join(KG, p))
import lean, extract
from eval_elite_routes import install_town
from transplant import build_agent, reference_log
from kaggle_environments.envs.kaggriculture import kaggriculture as K
cand, gid, s, d0, d1 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
files = {r['gid']: os.path.join(extract.GAMES, r['file']) for r in extract._index()}
d = extract._load(files[gid])
ref = reference_log(d, s)
rr = dict(hands=ref['hands'], money=ref['money'], outcomes=ref['outcomes'], shops=ref['shops'])
orig_eod = install_town(ref['shops'])
A = lean.load(cand)
LOG = []
def wrapped(obs, cfg=None):
    act = A(obs, cfg)
    st = int(obs['step']); day = st // 24
    if d0 <= day <= d1:
        me = int(obs['player']); farm = obs['farms'][me]
        shed = obs['private']['shed']
        pos = [tuple(farm['farmer'])] + [tuple(p) for p in farm['hands']]
        LOG.append((st, float(farm['money']), int(shed.get('MELON', 0)), [(pos[i] if i < len(pos) else None, (a[0][:4] + (':' + a[1][:3] if len(a) > 1 and isinstance(a[1], str) else '')) if isinstance(a, list) and a else '?') for i, a in enumerate([act.get('farmer')] + list(act.get('hands', [])))], [o for o in act.get('market', []) if o and o[0] == 'SELL' and o[1] == 'MELON']))
    return act
try:
    ag = [None, None]; ag[s] = build_agent(d['acts'], s, rr, slack_min=20); ag[1 - s] = wrapped
    r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
finally:
    K._end_of_day = orig_eod
print('result', r['r'])
for st, money, mel, units, sells in LOG:
    print('s%3d h%2d $%6.0f shedM %3d sellM %s | %s' % (st, st % 24, money, mel, [o[2] for o in sells], '  '.join('%s%s' % (('%d,%d' % p) if p else '--', ':' + a) for p, a in units)))
