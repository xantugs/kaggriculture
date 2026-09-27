"""Hour-by-hour animal trace of one live game in the pinned world (same world as pinned4.py / scan.py).
usage: esc_probe.py GID S d0 d1 [cand] [corpus]
Prints, for days d0..d1 of OUR farm: the controller's hour-0 plan (routes with animal visits, orders, unserved),
every unit action that touches an animal tile / wheat / animal stock, market orders with animals or wheat,
and the night state of every animal (fed / cared / consecutive_unfed / held) before the engine's refresh.
Loads only the one-game file <corpus>.d/<i>.json (index cached in the scratch dir of the caller, see _find)."""
import sys, os, json
sys.path.insert(0, '/home/user/kaggriculture/arena')
sys.path.insert(0, '/home/user/kaggriculture/gold/harness')
from pinned4 import reference, install_pinned, _tape, _prefixed  # noqa: E402


def print(*a, **k):      # lean.play redirects stdout around agent and engine calls
    k["file"] = sys.__stdout__
    __builtins__.print(*a, **k) if hasattr(__builtins__, "print") else __builtins__["print"](*a, **k)


def _find(corpus, gid):
    split = corpus + '.d'
    for f in sorted(os.listdir(split), key=lambda s: int(s.split('.')[0])):
        with open(os.path.join(split, f), encoding='utf-8') as fh:
            head = fh.read(4096)
        if str(gid) in head:
            g = json.load(open(os.path.join(split, f), encoding='utf-8'))[0]
            if g['id'] == gid:
                return g
    for f in os.listdir(split):
        g = json.load(open(os.path.join(split, f), encoding='utf-8'))[0]
        if g['id'] == gid:
            return g
    raise SystemExit('gid not found')


def main():
    gid, S, d0, d1 = map(int, sys.argv[1:5])
    cand = sys.argv[5] if len(sys.argv) > 5 else 'gold/top10/lean_sf8.py'
    corpus = sys.argv[6] if len(sys.argv) > 6 else 'gold/top10/gates/live191.json'
    import lean
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    d = _find(corpus, gid)
    names = d['info']['TeamNames']; P = names.index('offhand'); O = 1 - P
    print('game', gid, 'vs', names[O], 'seat', P, 'S', S)
    spawns, shops, _ = reference(d)
    orig = install_pinned(S // 24, O, spawns, shops)
    A = lean.load(cand)
    G = A.__globals__
    st = {'step': 0, 'farm': None, 'priv': None}
    o_apply = K._apply_unit_action; o_ra = K._daily_refresh_animals

    def win(day):
        return d0 <= day <= d1

    def apply(farm, private, idx, action, bs, day, tpd, cap=100):
        if farm is st['farm'] and win(day) and isinstance(action, list) and action:
            pos = farm['farmer'] if idx == 0 else (farm['hands'][idx - 1] if idx - 1 < len(farm['hands']) else None)
            if pos is not None:
                t = farm['tiles'][pos[1]][pos[0]]
                inv = private['inventories'][idx] if idx < len(private['inventories']) else {}
                an = isinstance(t, dict) and 'animal' in t
                op = action[0]
                if an or op in ('PLACE', 'BUILD_PASTURE', 'BUILD_COOP') or (op == 'PICKUP' and action[1] in ('WHEAT', 'SHEEP', 'COW', 'GOOSE')):
                    ts = ('%s p%d cu%d F%d C%d y%d' % (t['animal'][:2], t['placed_day'], t['consecutive_unfed'], t['fed_today'],
                                                        t['cared_today'], t['yield_units'])) if an else (t.get('kind') if isinstance(t, dict) else t)
                    print('   s%d h%02d u%-2d @%s %-28s inv=%s tile=%s' % (st['step'], st['step'] % 24, idx, tuple(pos), action,
                                                                     {k: v for k, v in inv.items() if v}, ts))
        return o_apply(farm, private, idx, action, bs, day, tpd, cap)

    def ra(farm, day):
        if farm is st['farm'] and win(day):
            rows = []
            for y, row in enumerate(farm['tiles']):
                for x, t in enumerate(row):
                    if isinstance(t, dict) and 'animal' in t:
                        rows.append('%s%d,%d p%d %s%s cu%d y%d' % (t['animal'][:2], x, y, t['placed_day'], 'F' if t['fed_today'] else 'f',
                                                               'C' if t['cared_today'] else 'c', t['consecutive_unfed'], t['yield_units']))
            unfed = [r for r in rows if ' f' in r]
            print('  NIGHT d%d animals %d  unfed %d: %s' % (day, len(rows), len(unfed), '; '.join(unfed)))
            print('         shed %s' % {k: v for k, v in st['priv']['shed'].items() if v})
        return o_ra(farm, day)
    K._apply_unit_action = apply; K._daily_refresh_animals = ra

    def wrap(inner):
        def f(obs, cfg=None):
            a = inner(obs, cfg)
            s = int(obs['step']); day = s // 24; h = s % 24
            st['step'] = s
            if st['farm'] is None:
                pass
            if win(day) and s >= S:
                farm = obs['farms'][P]; priv = obs['private']
                mk = [o for o in (a.get('market') or []) if o and (o[0] in ('BUY_ANIMAL', 'BUY_PRODUCT', 'HIRE') or o[1:2] == ['WHEAT'])]
                if h == 0:
                    gc = G.get('_GC')
                    print('== d%d h0 money %.0f shed %s hands %d taken %s start %s' % (
                        day, float(farm['money']), {k: v for k, v in priv['shed'].items() if v}, len(farm['hands']),
                        G.get('_GC_RICH', {}).get('taken'), G.get('_GC_REPORT', {}).get('gc_start')))
                    if gc is not None and getattr(gc, 'day_plan', None) == day:
                        print('   orders0 %s orders1 %s hires %s unserved %s herd %s' % (
                            getattr(gc, 'orders0', None), getattr(gc, 'orders1', None), getattr(gc, 'hires_planned', None),
                            getattr(gc, '_last_unserved', None), G['_GC_REPORT'].get('gc_herd')))
                        for u, r in enumerate(getattr(gc, 'routes', []) or []):
                            av = [(v.tag, v.pos, [x[0][:5] for x in v.acts], int(v.must), v.wheat, round(v.value)) for v in r
                                  if v.tag in ('A', 'L') or v.anim]
                            print('   u%-2d n%-2d w%d anim %s' % (u, len(r), sum(v.wheat for v in r), av))
                        # animals on tiles with no visit today
                        vis = {v.pos for r in gc.routes for v in r}
                        miss = []
                        for y, row in enumerate(farm['tiles']):
                            for x, t in enumerate(row):
                                if isinstance(t, dict) and t.get('animal') and (x, y) not in vis:
                                    miss.append('%s%d,%d cu%d' % (t['animal'][:2], x, y, t['consecutive_unfed']))
                        if miss:
                            print('   animals without a planned visit:', miss)
                if mk:
                    print('   s%d h%02d market %s  shedW %s money %.0f' % (s, h, mk, priv['shed'].get('WHEAT'), float(farm['money'])))
            return a
        return f

    class Rec:
        pass
    try:
        ag = [None, None]

        def first(obs, cfg=None, _f=wrap(_prefixed(A, d['acts'], P, S))):
            return _f(obs, cfg)
        ag[P] = first
        ag[O] = _tape(d['acts'], O)
        # grab our farm dicts at the first interpreter call
        o_int = K.interpreter

        def interp(state, env):
            out = o_int(state, env)
            if st['farm'] is None and state[0].observation.get('farms'):
                st['farm'] = state[0].observation.farms[P]; st['priv'] = state[P].observation.private
            return out
        K.interpreter = interp
        r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
    finally:
        K._apply_unit_action = o_apply; K._daily_refresh_animals = o_ra; K.interpreter = o_int
        K._end_of_day = orig
    print('result', r['r'], 'm', (r['r'][P] - r['r'][O]) if None not in r['r'] else None, r['err'], 'tmax', r['tmax'][P])
    print('report', {k: v for k, v in G['_GC_REPORT'].items() if k.startswith('gc_herd') or k in ('gc_start', 'gc_ad_step')})


if __name__ == '__main__':
    main()
