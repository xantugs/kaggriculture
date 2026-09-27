"""Idle (PASS) windows of our units in v16's final commands, days D0-D1, pinned. usage: idlehands.py cand gameidx D0 D1"""
import sys, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
import lean, pinned
cand, gi, D0, D1 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
fn = json.load(open(os.path.join(HERE, 'g2800_list.json')))[gi]
d = json.load(open(fn, encoding='utf-8'))[0]
P = d['info']['TeamNames'].index('offhand'); O = 1 - P
spawns, shops, _ = pinned.reference(d)
orig = pinned.install_pinned(4, O, spawns, shops)
A = lean.load(os.path.join(HERE, '..', 'arena', 'cand', cand + '.py'))
log = collections.defaultdict(dict)   # day -> unit -> list of (hour, cmd, pos)
def f(obs, cfg=None):
    a = A(obs, cfg); s = obs['step']
    if D0 * 24 <= s < (D1 + 1) * 24:
        me = obs['farms'][obs['player']]; pos = [me['farmer']] + me['hands']
        for i, c in enumerate([a.get('farmer') or ['PASS']] + list(a.get('hands') or [])):
            if i < len(pos):
                log[s // 24].setdefault(i, []).append((s % 24, (c or ['PASS'])[0], tuple(pos[i])))
    return a
ag = [None, None]; ag[P] = pinned._prefixed(f, d['acts'], P, 96); ag[O] = pinned._tape(d['acts'], O)
lean.play(None, None, d['info']['seed'], agent_objs=ag)
tot = collections.Counter()
for day in sorted(log):
    rows = []
    for i, seq in sorted(log[day].items()):
        n = len(seq); idle = sum(1 for h, c, p in seq if c == 'PASS')
        # longest PASS run staying on one tile
        best = run = 0; lastp = None
        for h, c, p in seq:
            if c == 'PASS' and (run == 0 or p == lastp):
                run += 1
            elif c == 'PASS':
                run = 1
            else:
                run = 0
            lastp = p; best = max(best, run)
        tot['steps'] += n; tot['idle'] += idle
        rows.append(f'{i}:{idle}/{n}(max{best})')
    print('day', day, ' '.join(rows))
print('idle share', round(tot['idle'] / max(1, tot['steps']), 3), 'idle unit-steps/day', round(tot['idle'] / (D1 - D0 + 1), 1))
