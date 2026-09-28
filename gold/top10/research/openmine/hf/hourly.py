"""Hourly trace of our seat in one gate game: every step's unit actions, market orders, cash, shed.
usage: hourly.py cand.py gid seat d0-d1 [tel]"""
import sys, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__))
OM = os.path.dirname(HERE)
KG = os.path.normpath(os.path.join(OM, '..', '..', '..', '..'))
sys.path.insert(0, OM)
for p in ('arena', 'gold/harness', 'gold/elite'):
    sys.path.insert(0, os.path.join(KG, p))


def main():
    cand, gid, s = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    d0, d1 = (int(v) for v in sys.argv[4].split('-'))
    import lean, extract
    from eval_elite_routes import install_town
    from transplant import build_agent, reference_log
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    files = {r['gid']: os.path.join(extract.GAMES, r['file']) for r in extract._index()}
    d = extract._load(files[gid])
    ref = reference_log(d, s)
    rr = dict(hands=ref['hands'], money=ref['money'], outcomes=ref['outcomes'], shops=ref['shops'])
    orig_eod = install_town(ref['shops'])
    A = lean.load(cand)
    log = []

    def wrap(obs, cfg=None):
        a = A(obs, cfg)
        st = int(obs['step'])
        if d0 * 24 <= st < (d1 + 1) * 24:
            me = obs['player']; f = obs['farms'][me]
            log.append((st, float(f['money']), dict(obs['private']['shed']), [tuple(f['farmer'])] + [tuple(h) for h in f['hands']],
                        [dict(i) for i in obs['private']['inventories']], a))
        return a
    try:
        ag = [None, None]; ag[s] = build_agent(d['acts'], s, rr, slack_min=20); ag[1 - s] = wrap
        r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig_eod
    print('result', r['r'], 'us', r['r'][1 - s])
    for st, m, shed, pos, invs, a in log:
        day, h = divmod(st, 24)
        units = [a.get('farmer')] + list(a.get('hands') or [])
        us = ' '.join('%s%s:%s%s' % (u, pos[u] if u < len(pos) else '', (x[0][:5] + ('/' + str(x[1])[:4] if len(x) > 1 else '')) if isinstance(x, list) and x else x,
                                     ('{' + ','.join('%s%d' % (k[:2], v) for k, v in invs[u].items() if v) + '}') if u < len(invs) and any(invs[u].values()) else '')
                      for u, x in enumerate(units))
        print('d%d h%02d $%7.0f shed{%s} mk=%s' % (day, h, m, ','.join('%s%d' % (k[:3], v) for k, v in shed.items() if v), a.get('market')))
        print('      ' + us)
    if len(sys.argv) > 5:
        tel = getattr(A, 'telemetry', {})
        print({k: v for k, v in tel.items() if k.startswith("gc_open") or "err" in k or k.startswith("gc_dbg")})


main()
