"""Replay recorded games (both tapes) and report, per game, where the money went for both seats.
usage: lost_report.py games.json [team=offhand] [cand1.py,cand2.py]  (candidates are shadow-run on our seat to find
which build played: first step whose action differs from the recorded one)"""
import sys, os, json, collections
HERE = '/home/user/kaggriculture/moon'
sys.path.insert(0, os.path.join(HERE, '..', 'arena')); sys.path.insert(0, '/home/user/kaggriculture/gold/harness')
sys.argv = [sys.argv[0]] + [os.path.abspath(a) if a.endswith('.json') else a for a in sys.argv[1:]]
os.chdir(HERE)
import lean
from kaggle_environments.envs.kaggriculture import kaggriculture as K
from pinned4 import _tape
PROD = {'COW': 'MILK', 'SHEEP': 'WOOL', 'GOOSE': 'EGG'}


def snap(farm):
    an = collections.Counter(); cr = collections.Counter(); weeds = 0; ripe = collections.Counter()
    for row in farm['tiles']:
        for t in row:
            if isinstance(t, dict):
                if t.get('animal'):
                    an[t['animal']] += 1
                elif t.get('crop'):
                    cr[t['crop']] += 1
                elif t.get('kind') == 'WEED':
                    weeds += 1
                p = t.get('crop') or PROD.get(t.get('animal'))
                if p and int(t.get('yield_units', 0) or 0) > 0:
                    ripe[p] += int(t['yield_units'])
    return dict(money=round(farm['money']), land=list(farm['unlocked_quadrants']), an=dict(an), cr=dict(cr), weeds=weeds,
                ripe=dict(ripe), hires=farm.get('hires_today', 0))


def norm(a):
    if not isinstance(a, dict):
        a = {"farmer": ["PASS"], "hands": [], "market": []}
    return json.dumps(a, sort_keys=True)


def run(d, team, cands):
    names = d['info']['TeamNames']; P = names.index(team) if team in names else 0; O = 1 - P
    led = [collections.defaultdict(lambda: [0, 0.0]) for _ in range(2)]
    SN = {}; LAND = [[], []]; FARMS = [None, None]; STEP = [0]; HIRES = [collections.Counter(), collections.Counter()]
    oc, opm, oh, obl = K._commit_unit, K._process_market, K._do_hire, K._do_buy_land
    def commit(op, item, price, farm, private, market, cap=100):
        ok = oc(op, item, price, farm, private, market, cap)
        if ok and FARMS[0] is not None:
            i = 0 if farm is FARMS[0] else 1
            key = (op, item)
            led[i][key][0] += 1; led[i][key][1] += price
        return ok
    def pm(state, env):
        st = state[0].observation.step
        FARMS[0], FARMS[1] = state[0].observation.farms[0], state[0].observation.farms[1]
        STEP[0] = st
        if st % 24 == 0 or st % 24 == 23:
            SN[st] = [snap(state[0].observation.farms[i]) for i in (0, 1)]
        return opm(state, env)
    def hire(farm, private, bs, mult=1):
        m0 = farm['money']; oh(farm, private, bs, mult)
        if FARMS[0] is not None and farm['money'] < m0:
            i = 0 if farm is FARMS[0] else 1
            led[i][('WAGE', 'HAND')][0] += 1; led[i][('WAGE', 'HAND')][1] += m0 - farm['money']
            HIRES[i][STEP[0] // 24] += 1
    def bl(farm, bs):
        m0 = farm['money']; obl(farm, bs)
        if FARMS[0] is not None and farm['money'] < m0:
            i = 0 if farm is FARMS[0] else 1
            LAND[i].append((STEP[0] // 24, STEP[0], round(m0 - farm['money'])))
    K._commit_unit = commit; K._process_market = pm; K._do_hire = hire; K._do_buy_land = bl
    SH = {c: None for c in cands}
    try:
        ag = [_tape(d['acts'], 0), _tape(d['acts'], 1)]
        if cands:
            objs = {c: lean.load(c) for c in cands}
            base = ag[P]
            def shadow(obs, cfg=None):
                a = base(obs, cfg); t = obs['step']
                for c, A in objs.items():
                    if SH[c] is None:
                        try:
                            b = A(json.loads(json.dumps(obs)), cfg)
                        except Exception as e:
                            b = {'err': repr(e)}
                        if norm(b) != norm(a):
                            SH[c] = t
                return a
            ag[P] = shadow
        r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
    finally:
        K._commit_unit, K._process_market, K._do_hire, K._do_buy_land = oc, opm, oh, obl
    return P, O, r, led, SN, LAND, HIRES, SH


def fmt_counter(c):
    return ' '.join('%s%d' % (k[:2].lower(), v) for k, v in sorted(c.items())) or '-'


def report(d, team, cands):
    P, O, r, led, SN, LAND, HIRES, SH = run(d, team, cands)
    names = d['info']['TeamNames']
    ok = [int(x) for x in r['r']] == [int(x) for x in d['rewards']]
    L = []
    L.append('=' * 100)
    L.append('game %s seed %s  %s (us, seat %d) %d  vs  %s %d  margin %+d  replay_ok=%s' % (
        d['id'], d['info']['seed'], names[P], P, d['rewards'][P], names[O], d['rewards'][O], d['rewards'][P] - d['rewards'][O], ok))
    L.append('shops: ' + ' '.join(s[:4] for s in r.get('shops', [])))
    if cands:
        L.append('shadow (first differing step per candidate): ' + ', '.join('%s=%s' % (os.path.basename(c), SH[c]) for c in cands))
    L.append('land: us %s | rival %s' % (LAND[P], LAND[O]))
    L.append('day | money us / rival | animals us / rival | crops us / rival | weeds | hires us/rival')
    for day in range(30):
        s = SN.get(day * 24)
        if not s:
            continue
        a, b = s[P], s[O]
        L.append('%2d | %7d %7d | %-18s %-18s | %-26s %-26s | %2d %2d | %2d %2d' % (
            day, a['money'], b['money'], fmt_counter(a['an']), fmt_counter(b['an']), fmt_counter(a['cr']), fmt_counter(b['cr']),
            a['weeds'], b['weeds'], HIRES[P][day], HIRES[O][day]))
    keys = sorted(set(led[P]) | set(led[O]), key=lambda k: (k[0], k[1]))
    L.append('ledger (units, $): us | rival | diff')
    tot = [0.0, 0.0]
    for k in keys:
        u = led[P].get(k, [0, 0.0]); v = led[O].get(k, [0, 0.0])
        sgn = 1 if k[0] == 'SELL' else -1
        tot[0] += sgn * u[1]; tot[1] += sgn * v[1]
        L.append('  %-12s %-12s %5d %9.0f | %5d %9.0f | %+9.0f' % (k[0], k[1], u[0], sgn * u[1], v[0], sgn * v[1], sgn * (u[1] - v[1])))
    L.append('  land: us %d rival %d' % (-sum(x[2] for x in LAND[P]), -sum(x[2] for x in LAND[O])))
    return '\n'.join(L), dict(id=d['id'], P=P, ok=ok, r=r['r'], shadow={os.path.basename(c): SH[c] for c in cands},
                               led=[{'%s:%s' % k: v for k, v in led[i].items()} for i in (P, O)], land=[LAND[P], LAND[O]],
                               snaps={k: [v[P], v[O]] for k, v in SN.items()}, hires=[dict(HIRES[P]), dict(HIRES[O])])


if __name__ == '__main__':
    games = json.load(open(sys.argv[1]))
    team = sys.argv[2] if len(sys.argv) > 2 else 'offhand'
    cands = [os.path.abspath(c) for c in sys.argv[3].split(',')] if len(sys.argv) > 3 and sys.argv[3] else []
    out = os.environ.get('OUT')
    rows = []
    for d in games:
        txt, row = report(d, team, cands)
        print(txt, flush=True); rows.append(row)
    if out:
        json.dump(rows, open(out, 'w'))
