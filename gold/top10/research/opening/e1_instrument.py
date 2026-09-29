"""e1_instrument.py CAND gid elite_seat : days 5-11 of a repaired elite game with CAND in our seat: per day, our and the elite's
WOOL / MILK sales (hour:units@price), our held-unit telemetry, cash at hour 23, land purchases and animal counts."""
import sys, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__)); OM = os.path.join(os.path.dirname(HERE), 'openmine')
sys.path.insert(0, OM)
for p in ('arena', 'gold/harness', 'gold/elite'): sys.path.insert(0, os.path.join(os.getcwd(), p))
import lean, extract
from eval_elite_routes import install_town
from transplant import build_agent, reference_log
from kaggle_environments.envs.kaggriculture import kaggriculture as K
cand, gid, s = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
files = {r['gid']: os.path.join(extract.GAMES, r['file']) for r in extract._index()}
d = extract._load(files[gid]); ref = reference_log(d, s)
rr = dict(hands=ref['hands'], money=ref['money'], outcomes=ref['outcomes'], shops=ref['shops'])
orig = install_town(ref['shops'])
A = lean.load(cand); EL = build_agent(d['acts'], s, rr, slack_min=20)
LOG = collections.defaultdict(lambda: dict(us=collections.defaultdict(list), el=collections.defaultdict(list), cash=None, elcash=None, land=[], anim=None, held=None, need=None))
def mk(ag, side):
    def w(obs, cfg=None):
        act = ag(obs, cfg); st = int(obs['step']); day, hour = divmod(st, 24)
        if 5 <= day <= 11:
            L = LOG[day]; px = obs['market']['prices']; me = int(obs['player'])
            for o in (act.get('market') or []) if isinstance(act, dict) else []:
                if isinstance(o, list) and len(o) >= 3 and o[0] == 'SELL' and o[1] in ('WOOL', 'MILK', 'MELON'):
                    L[side][o[1]].append('%d:%d@%d' % (hour, int(o[2]), int(px[o[1]])))
                if side == 'us' and isinstance(o, list) and o and o[0] == 'BUY_LAND':
                    L['land'].append(hour)
            if hour == 23:
                f = obs['farms'][me]
                if side == 'us':
                    L['cash'] = int(float(f['money']))
                    c = collections.Counter(t['animal'][0] for row in f['tiles'] for t in row if isinstance(t, dict) and 'animal' in t)
                    L['anim'] = ''.join('%s%d' % kv for kv in sorted(c.items()))
                    tel = getattr(A, 'telemetry', {}) or {}
                    L['held'] = tel.get('gc_e1_held_units'); L['need'] = tel.get('gc_urg_over')
                else:
                    L['elcash'] = int(float(f['money']))
        return act
    return w
try:
    ag = [None, None]; ag[s] = mk(EL, 'el'); ag[1 - s] = mk(A, 'us')
    r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
finally:
    K._end_of_day = orig
print('%s gid %d: us %.0f elite %.0f (%+.0f)' % (os.path.basename(cand), gid, r['r'][1 - s], r['r'][s], r['r'][1 - s] - r['r'][s]))
for day in sorted(LOG):
    L = LOG[day]
    print(' d%-2d cash %6s elite %6s anim %-10s land %s | our wool %s milk %s | elite wool %s milk %s' % (day, L['cash'], L['elcash'], L['anim'], L['land'], ' '.join(L['us']['WOOL']) or '-', ' '.join(L['us']['MILK']) or '-', ' '.join(L['el']['WOOL']) or '-', ' '.join(L['el']['MILK']) or '-'))
