"""Which layer adds (or removes) SELL units of ITEMS: every parent in the AD chain is wrapped, and per step the SELL qty
after each layer is recorded; deltas are attributed to the layer that produced them. Pinned from S on N games of a class.
usage: layertrace.py cand S ITEMS D0 D1 [MIRROR|DIVERGENT] [N]"""
import sys, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
from concurrent.futures import ProcessPoolExecutor


def _sell(a, items):
    out = collections.Counter()
    if isinstance(a, dict):
        for o in a.get('market') or []:
            if o and o[0] == 'SELL' and len(o) >= 3 and o[1] in items:
                out[o[1]] += int(o[2])
    return out


def job(t):
    fn, cand, S, items, D0, D1 = t
    import lean, pinned
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    d = json.load(open(fn, encoding='utf-8'))[0]
    P = d['info']['TeamNames'].index('offhand'); O = 1 - P
    spawns, shops, _ = pinned.reference(d)
    orig = pinned.install_pinned(S // 24, O, spawns, shops)
    A = lean.load(cand); g = A.__globals__
    chain = list(g['_AD_CFG']['chain'])
    rec = {}
    def wrap(fn_, name):
        def w(obs, cfg=None):
            a = fn_(obs, cfg)
            s = int(obs['step'])
            if D0 * 24 <= s < (D1 + 1) * 24:
                rec.setdefault(s, {})[name] = _sell(a, items)
            return a
        return w
    for name in chain:
        g[name] = wrap(g[name], name)
    def top(obs, cfg=None):
        a = A(obs, cfg); s = int(obs['step'])
        if D0 * 24 <= s < (D1 + 1) * 24:
            rec.setdefault(s, {})['FINAL'] = _sell(a, items)
        return a
    try:
        ag = [None, None]; ag[P] = pinned._prefixed(top, d['acts'], P, S); ag[O] = pinned._tape(d['acts'], O)
        lean.play(None, None, d['info']['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig
    agg = collections.Counter()
    for s, last in rec.items():
        prev = collections.Counter()
        for name in chain + ['FINAL']:
            if name not in last:
                continue
            c = last[name]
            for it in items:
                dlt = c[it] - prev[it]
                if dlt:
                    agg[(it, s % 24, name)] += dlt
            prev = c
    return {'|'.join(map(str, k)): v for k, v in agg.items()}


if __name__ == '__main__':
    cand, S, items, D0, D1 = sys.argv[1], int(sys.argv[2]), tuple(sys.argv[3].split(',')), int(sys.argv[4]), int(sys.argv[5])
    klass = sys.argv[6] if len(sys.argv) > 6 else 'DIVERGENT'; N = int(sys.argv[7]) if len(sys.argv) > 7 else 30
    cls = json.load(open(os.path.join(HERE, 'gameclass.json')))
    files = [f for f in json.load(open(os.path.join(HERE, 'g2800_list.json')))
             if (cls.get(os.path.basename(f)[:-5], 0) >= 0.8) == (klass == 'MIRROR')][:N]
    path = os.path.join(HERE, '..', 'arena', 'cand', cand + '.py')
    tot = collections.Counter()
    with ProcessPoolExecutor(int(os.environ.get('WORKERS', '8'))) as ex:
        for r in ex.map(job, [(f, path, S, items, D0, D1) for f in files]):
            for k, v in r.items():
                tot[k] += v
    g = len(files)
    by_layer = collections.Counter()
    for k, v in tot.items():
        it, h, name = k.split('|'); by_layer[(it, name)] += v
    print(f'{cand} {klass} games {g} days {D0}-{D1}: SELL units added per game by layer (the named parent is the layer BELOW the one that added them)')
    for (it, name), v in sorted(by_layer.items(), key=lambda kv: (kv[0][0], -abs(kv[1]))):
        if abs(v) / g >= 0.5:
            hrs = sorted(((int(k.split('|')[1]), tot[k] / g) for k in tot if k.startswith(it + '|') and k.endswith('|' + name) and abs(tot[k]) / g >= 0.5), key=lambda x: -abs(x[1]))[:6]
            print(f'  {it:10s} {name:22s} {v / g:+7.1f}   top hours {[(h, round(x, 1)) for h, x in hrs]}')
