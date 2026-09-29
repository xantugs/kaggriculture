"""herd_features.py : days 0-10 public features of each herd-poor agent, in a game vs the controller (c0tp) and vs the tape
(T8fcWt), seed 7500, our seat 0. Records the agent's census (animals, crops), quadrants, cash at the end of each day, its
first WOOL / MILK sales (day, hour, units) and its units sold per product through day 10, and the same census for us."""
import sys, os, json, collections
from concurrent.futures import ProcessPoolExecutor
GOOD = ['kaggriculture-adaptive-public-state-multi-route', 'kaggriculture-breaking-the-tie', 'kaggriculture-strongest-farmer-of-today']
BAD = ['kaggriculture-x544-nah-i-d-win', 'kaggriculture-findings-from-zero-to-top-meta', 'kaggriculture-limit-breaker-agent',
       'two-reinforcement-learning-examples-from-kaito-v27', 'kaggriculture-weedproof-clone-market']
MID = ['counter-cyclical-orchard', 'kaggriculture-c01-scenario-v7-reproduction', 'kaggriculture-precomputed-schedule-policy']
US = {'ctl': 'gold/top10/cands/full_OP_c0tp.py', 'tape': 'gold/top10/cands/full_T8fcWt.py'}
def census(f):
    c = collections.Counter()
    for row in f['tiles']:
        for t in row:
            if isinstance(t, dict):
                if 'animal' in t: c[t['animal'][0]] += 1
                elif t.get('kind') == 'PLANT': c[t['crop'][:2].lower()] += 1
    return c
def one(task):
    name, who = task
    sys.path.insert(0, os.path.join(os.getcwd(), 'arena'))
    import lean
    path = '../pubnb/x_%s.py' % name
    A = lean.load(US[who]); B = lean.load(path)
    rec = dict(days={}, first={}, sold=collections.Counter(), us={})
    def wa(obs, cfg=None):
        return A(obs, cfg)
    def wb(obs, cfg=None):
        act = B(obs, cfg)
        st = int(obs['step']); d, h = divmod(st, 24); me = int(obs['player'])
        if d <= 10:
            for o in (act.get('market') or []) if isinstance(act, dict) else []:
                if isinstance(o, list) and len(o) >= 3 and o[0] == 'SELL':
                    rec['sold'][o[1]] += int(o[2])
                    if o[1] in ('WOOL', 'MILK', 'MELON') and o[1] not in rec['first']:
                        rec['first'][o[1]] = '%d@%d x%d' % (d, h, int(o[2]))
            if h == 23:
                f = obs['farms'][me]; u = obs['farms'][1 - me]
                rec['days'][d] = dict(cash=int(float(f['money'])), quads=len(f['unlocked_quadrants']), hands=len(f['hands']), c=dict(census(f)))
                rec['us'][d] = dict(cash=int(float(u['money'])), c=dict(census(u)))
        return act
    r = lean.play(None, None, 7500, agent_objs=[wa, wb])
    rec['final'] = (r['r'][0], r['r'][1])
    rec['sold'] = dict(rec['sold'])
    return name, who, rec
if __name__ == '__main__':
    tasks = [(n, w) for n in GOOD + MID + BAD for w in ('ctl', 'tape')]
    out = {}
    with ProcessPoolExecutor(4) as ex:
        for name, who, rec in ex.map(one, tasks):
            out['%s|%s' % (name, who)] = rec
    json.dump(out, open('gold/top10/research/opening/herd_features.json', 'w'), indent=0)
    def cs(c): return ' '.join('%s%d' % (k, v) for k, v in sorted(c.items()))
    for grp, names in (('GOOD for controller', GOOD), ('MIDDLE', MID), ('BAD for controller', BAD)):
        print('==== %s' % grp)
        for n in names:
            for who in ('ctl', 'tape'):
                rec = out['%s|%s' % (n, who)]; D = rec['days']
                print('%-44s vs %-4s final us %6.0f them %6.0f | first sales %s | sold d0-10 %s' % (n[-44:], who, rec['final'][0], rec['final'][1], rec['first'], {k: v for k, v in rec['sold'].items() if k in ('WOOL', 'MILK', 'MELON', 'EGG', 'STRAWBERRY')}))
                for d in (1, 2, 4, 6, 8, 10):
                    if d in D:
                        print('      d%-2d them cash %6d q%d h%-2d %-32s | us cash %6d %s' % (d, D[d]['cash'], D[d]['quads'], D[d]['hands'], cs(D[d]['c']), rec['us'][d]['cash'], cs(rec['us'][d]['c'])))
