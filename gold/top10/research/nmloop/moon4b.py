"""moon4b.py : MOON4b - FULL-ECONOMY evolution (ChatGPT L28): the MOON4 genome widened with the day-0 herd, hires, crew, cash
reserve, liquidation days and feed, seeded with radically different parents (NMp44, g128, new-meta-like, crop-heavy, herd-heavy,
dairy, goose economy) plus mutants and random genomes. Derived from moon4.py: MOON4 - evolutionary best-response search for the 960-band opening (ChatGPT L27, owner's go 30 Sep).

A genome of 22 genes (crop / herd / land / priority / melon-rule / strawberry-rule choices) becomes the p1e open-profile overrides
for the 960 band; the candidate is built with build_nmp_d15.py (c2tr + NM branch + day-6 melon gate + day-12-15 strawberry
top-up). Day-0 purchases stay as NMp13's (every day-0 change broke the cash path in earlier rounds). Successive halving:
  gen N SEED   : write N random genomes + the NMp44 baseline (genome 0) to moon4/genomes.json and build their candidates
  s1           : every genome on the S1 panel (10 hard band games: the 6 ladder mini-gate games + 4 close ladder losses)
  s2 TOPK      : the TOPK S1 genomes (+ baseline) on the S2 panel (the other 26 ladder band games + 14 close fresh960 losses)
  rank STAGE   : ranking (wins, then the sum of margins clipped to +-20k)
Results: nmloop/moon4/s1.jsonl, s2.jsonl (one row per genome x game)."""
import sys, os, json, gzip, copy, random, subprocess, collections
sys.path.insert(0, os.path.join(os.getcwd(), 'arena')); sys.path.insert(0, os.path.join(os.getcwd(), 'gold/harness')); sys.path.insert(0, os.path.join(os.getcwd(), 'gold/elite'))
from concurrent.futures import ProcessPoolExecutor
N = 'gold/top10/research/nmloop/'; M = N + 'moon4b/'; G = 'gold/top10/gates/'; C = 'gold/top10/cands/moon4b/'
PY = '../.venv/Scripts/python.exe'
BASE = {"straw_max": 26, "straw_hf": {"early": {"4": 3, "5": 5}, "ne": [6, 5], "sw": [6, 4, -0.25]}, "melon": 12,
        "anim_cond": {"COW": ["milk", {"0": 3, "3": [4, 4.6], "4": [4, 5.6], "5": [4, 6.5], "6": [5, 6.5, 9], "7": [6, 7, 10], "8": [6.5, 7.5, 10.5]}],
                      "SHEEP": ["yarn", {"0": 2, "3": [2, 3], "4": [2.4, 4], "5": [2.4, 5], "6": [2.4, 6.5, 8.5], "7": [2.9, 7.5, 9.5], "8": [4, 10, 12], "9": [5.5, 10, 14]}],
                      "GOOSE": ["egg", {"2": 2, "4": [2.5, 3], "6": [4, 5, 6], "7": [5, 6, 7], "9": [7, 8, 8]}]},
        "anim_day_max": 4, "melon0": 6, "melon_last": 7, "mid_melon": True, "melon_sell_now": 1, "melon_day": {"min_units": 12, "slack": 4}}
# gene name -> (options, baseline index)
GENES = [
    ('day0_cow', [1, 2, 3, 4], 2),
    ('day0_sheep', [0, 1, 2, 3], 2),
    ('day2_goose', [0, 1, 2, 3], 2),
    ('hires0', [3, 4, 5, 6], 2),
    ('wheat0', [5, 9, 13, 17, 21], 2),
    ('melon0', [0, 3, 6, 9], 2),
    ('melon', [0, 6, 12, 15, 18], 2),
    ('melon_last', [2, 4, 7, 9], 2),
    ('mid_melon', [True, False], 0),
    ('straw_early', [[0, 0], [2, 3], [3, 5], [5, 8]], 2),
    ('straw_ne', [[3, 3], [6, 5], [8, 7], [10, 9]], 1),
    ('straw_sw', [[3, 2], [6, 4], [9, 6]], 1),
    ('straw_max', [12, 16, 20, 26, 32, 38], 3),
    ('cow_scale', [0.5, 0.8, 1.0, 1.25, 1.5, 2.0], 2),
    ('goose_scale', [0.5, 1.0, 1.5, 2.0, 2.5, 3.0], 1),
    ('sheep_scale', [0.3, 0.6, 1.0, 1.5], 2),
    ('anim_day_max', [2, 3, 4, 6, 8], 2),
    ('land_ne', [5, 6, 7, 9], 1),
    ('land_sw', [7, 8, 9, 11], 1),
    ('mid_wheat_from', [4, 6, 8, 10, 99], 2),
    ('anim_prio', [[True, 3], [True, 6], [False, 3]], 0),
    ('herd_cap', [10, 16, 20, 26, 32], 2),
    ('melon_rule', ['gate12', 'always', 'never'], 0),
    ('straw_top', [[26, 3], [30, 3], [22, 2], [0, 99]], 0),
    ('land_wheat', [0, 8, 15], 2),
    ('liq_days', [[6, 8, 9], [], [8, 10], [7, 9, 11]], 0),
    ('crew_hi', [9, 11, 13], 1),
    ('crew_a', [2.5, 3.3, 4.5], 1),
    ('cash_keep', [0, 20, 100, 300], 1),
    ('feed0_kinds', [['SHEEP'], ['SHEEP', 'COW'], []], 0),
]
BASE_CREW = {'a': 3.3, 'tiles': 0.045, 'anim': 0.18, 'shed': 0.38, 'plant': 0.13, 'lo': 4, 'hi': 11, 'below': 0, 'cap': 0}
GI = {name: k for k, (name, _, _) in enumerate(GENES)}


def decode(g):
    """genome (list of option indices) -> (over dict, gate threshold, top-up cap, top-up min buyers)"""
    v = {name: opts[i] for (name, opts, _), i in zip(GENES, g)}
    over = copy.deepcopy(BASE)
    over['melon0'] = v['melon0']; over['melon'] = max(v['melon'], v['melon0']); over['melon_last'] = v['melon_last']
    over['mid_melon'] = v['mid_melon']; over['wheat0'] = v['wheat0']
    e = v['straw_early']
    over['straw_hf'] = {"early": {"4": e[0], "5": e[1]}, "ne": list(v['straw_ne']), "sw": [v['straw_sw'][0], v['straw_sw'][1], -0.25]}
    over['straw_max'] = v['straw_max']
    for kind, key in (('COW', 'cow_scale'), ('SHEEP', 'sheep_scale'), ('GOOSE', 'goose_scale')):
        tab = over['anim_cond'][kind][1]
        for day, val in list(tab.items()):
            if day == '0' or (kind == 'GOOSE' and day == '2'):
                continue   # the day-0 cows/sheep and the day-2 geese are their own genes
            tab[day] = [round(x * v[key], 2) for x in val] if isinstance(val, list) else round(val * v[key], 2)
    over['anim_cond']['COW'][1]['0'] = v['day0_cow']
    over['anim_cond']['SHEEP'][1]['0'] = v['day0_sheep']
    over['anim_cond']['GOOSE'][1]['2'] = v['day2_goose']
    over['anim_day_max'] = v['anim_day_max']
    over['land'] = {"NE": v['land_ne'], "SW": max(v['land_sw'], v['land_ne'])}
    over['mid_wheat_from'] = v['mid_wheat_from']
    over['anim_before_straw'], over['abs_last'] = v['anim_prio'][0], v['anim_prio'][1]
    over['herd_cap'] = v['herd_cap']; over['land_wheat'] = v['land_wheat']; over['hires0'] = v['hires0']
    over['liq_days'] = list(v['liq_days'])
    over['crew'] = dict(BASE_CREW, hi=v['crew_hi'], a=v['crew_a'])
    over['cash_keep'] = v['cash_keep']
    over['feed0_kinds'] = list(v['feed0_kinds'])
    thr = 12
    if v['melon_rule'] == 'always':
        thr = 99
    elif v['melon_rule'] == 'never':
        over['melon_sell_now'] = 0; over['melon_day'] = None; thr = 99
    cap, minb = v['straw_top']
    return over, thr, cap, minb


def parent(**kw):
    g = [b for _, _, b in GENES]
    for name, val in kw.items():
        g[GI[name]] = GENES[GI[name]][1].index(val)
    return g


PARENTS = [
    parent(),                                                                   # NMp44 baseline
    parent(melon=15, straw_ne=[10, 9], straw_max=20, cow_scale=0.8, land_sw=11, mid_wheat_from=99, anim_prio=[False, 3],
           herd_cap=16, straw_top=[22, 2], land_wheat=8),                      # MOON4 g128
    parent(day0_cow=1, day0_sheep=3, day2_goose=0, wheat0=17, cow_scale=1.25, goose_scale=2.0, anim_day_max=6,
           mid_wheat_from=6, straw_max=20, herd_cap=26),                        # new-meta-like
    parent(day0_cow=1, day0_sheep=0, day2_goose=0, cow_scale=0.5, goose_scale=0.5, sheep_scale=0.3, herd_cap=10, straw_max=38,
           straw_ne=[10, 9], straw_sw=[9, 6], melon=18, melon0=9, wheat0=17, anim_prio=[False, 3]),   # crop-heavy, no herd
    parent(day0_cow=4, day0_sheep=3, day2_goose=3, cow_scale=1.5, goose_scale=2.5, sheep_scale=1.5, herd_cap=32, anim_day_max=8,
           straw_max=16, melon=6, melon0=3, wheat0=21, mid_wheat_from=4),       # herd-heavy
    parent(day0_cow=4, day0_sheep=1, day2_goose=0, cow_scale=2.0, goose_scale=0.5, herd_cap=26, straw_max=20),   # dairy
    parent(day0_cow=2, day0_sheep=1, day2_goose=3, goose_scale=3.0, cow_scale=0.8, wheat0=21, mid_wheat_from=4, herd_cap=32,
           anim_day_max=8),                                                     # goose economy
]


def build(idx, g):
    over, thr, cap, minb = decode(g)
    out = C + 'g%03d.py' % idx
    r = subprocess.run([PY, N + 'build_nmp_d15.py', out, json.dumps(over), json.dumps({"melon_sell_now": 0, "melon_day": None}), str(thr), str(cap or 26), '12', str(minb)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-500:])
    return out


def panel_keys():
    """S1 / S2 panels: (source, gid, seat) keys."""
    def cls_band(r):
        m = r['money'][1] if len(r['money']) > 1 else -1; h = r['hands'][1] if len(r['hands']) > 1 else -1
        return h == 0 and 940 <= m <= 980
    lad = [json.loads(l) for l in open(G + 'lad_v33_refs.jsonl', encoding='utf-8')]
    lad_band = [r for r in lad if cls_band(r)]
    res = {(x['gid'], x['seat']): x['m'] for x in (json.loads(l) for l in open(N + 'lad_NMp44T.jsonl', encoding='utf-8')) if x.get('m') is not None}
    orig = [115333932, 115335380, 115338309, 115336805, 115345249, 115332494]
    s1 = [('lad', r['gid'], r['seat']) for r in lad_band if r['gid'] in orig]
    close = sorted([r for r in lad_band if r['gid'] not in orig and -12000 <= res.get((r['gid'], r['seat']), 1) < -1000],
                   key=lambda r: res[(r['gid'], r['seat'])], reverse=True)
    s1 += [('lad', r['gid'], r['seat']) for r in close[:4]]
    s1set = {(g, s) for _, g, s in s1}
    s2 = [('lad', r['gid'], r['seat']) for r in lad_band if (r['gid'], r['seat']) not in s1set]
    f960 = {(x['gid'], x['seat']): x['m'] for x in (json.loads(l) for l in open(N + 'f960_NMp44.jsonl', encoding='utf-8')) if x.get('m') is not None}
    cand = sorted(k for k, m in f960.items() if -10000 <= m < 0)
    random.Random(5).shuffle(cand)
    s2 += [('f960', g, s) for g, s in cand[:14]]
    return s1, s2


_W = {}


def _init(keys):
    import elite_gate  # noqa
    want = collections.defaultdict(set)
    for src, g, s in keys:
        want[src].add((g, s))
    files = {'lad': (G + 'lad_v33_games.jsonl.gz', G + 'lad_v33_refs.jsonl'), 'f960': (G + 'fresh960_games.jsonl.gz', G + 'fresh960_refs.jsonl')}
    for src, ks in want.items():
        gids = {g for g, _ in ks}
        with gzip.open(files[src][0], 'rt', encoding='utf-8') as fh:
            for l in fh:
                d = json.loads(l)
                if d['id'] in gids: _W[('game', src, d['id'])] = d
        for l in open(files[src][1], encoding='utf-8'):
            r = json.loads(l)
            if (r['gid'], r['seat']) in ks: _W[('ref', src, r['gid'], r['seat'])] = r


def _task(t):
    import elite_gate
    idx, cand, (src, g, s) = t
    try:
        x = elite_gate._play((_W[('game', src, g)], _W[('ref', src, g, s)], cand))
        return dict(genome=idx, src=src, gid=g, seat=s, m=x['m'], us=x['us'], them=x['tape'], err=x['err'], tmax=x['tmax'])
    except Exception as e:
        return dict(genome=idx, src=src, gid=g, seat=s, m=None, error=repr(e)[:200])


def run_stage(stage, genome_ids, keys, nproc=16):
    gen = json.load(open(M + 'genomes.json'))
    tasks = [(i, C + 'g%03d.py' % i, k) for i in genome_ids for k in keys]
    done = set()
    out = M + '%s.jsonl' % stage
    if os.path.exists(out):
        for l in open(out, encoding='utf-8'):
            r = json.loads(l); done.add((r['genome'], r['src'], r['gid'], r['seat']))
    tasks = [t for t in tasks if (t[0], t[2][0], t[2][1], t[2][2]) not in done]
    print('%s: %d genomes x %d games = %d tasks to run' % (stage, len(genome_ids), len(keys), len(tasks)), flush=True)
    with ProcessPoolExecutor(nproc, initializer=_init, initargs=(keys,)) as ex, open(out, 'a', encoding='utf-8') as fo:
        for n, r in enumerate(ex.map(_task, tasks, chunksize=2)):
            fo.write(json.dumps(r) + '\n'); fo.flush()
            if n % 100 == 0: print('  %d/%d' % (n, len(tasks)), flush=True)


def rank(stage, top=15):
    rows = [json.loads(l) for l in open(M + '%s.jsonl' % stage, encoding='utf-8')]
    by = collections.defaultdict(list)
    for r in rows:
        if r.get('m') is not None: by[r['genome']].append(r['m'])
    sc = sorted(((sum(m > 0 for m in ms), sum(max(-20000, min(20000, m)) for m in ms), len(ms), g) for g, ms in by.items()), reverse=True)
    base = next((s for s in sc if s[3] == 0), None)
    print('%s ranking (wins, clipped margin sum, n, genome); baseline NMp44 = genome 0: %s' % (stage, base))
    for s in sc[:top]:
        print('  genome %3d: wins %2d  clipped %+8.0f  n %d' % (s[3], s[0], s[1], s[2]))
    return [s[3] for s in sc]


if __name__ == '__main__':
    os.makedirs(M, exist_ok=True); os.makedirs(C, exist_ok=True)
    cmd = sys.argv[1]
    if cmd == 'gen':
        n, seed = int(sys.argv[2]), int(sys.argv[3])
        rnd = random.Random(seed)
        gens = [list(p) for p in PARENTS]   # genome 0 = the NMp44 baseline, 1-6 = the seed parents
        for p in PARENTS[1:]:
            for _ in range(8):   # mutants: 3-6 genes re-drawn
                g = list(p)
                for k in rnd.sample(range(len(GENES)), rnd.randint(3, 6)):
                    g[k] = rnd.randrange(len(GENES[k][1]))
                if g not in gens: gens.append(g)
        while len(gens) < n + 1:
            g = [rnd.randrange(len(opts)) for _, opts, _ in GENES]
            if g not in gens: gens.append(g)
        json.dump(gens, open(M + 'genomes.json', 'w'))
        with ProcessPoolExecutor(8) as ex:
            list(ex.map(build, range(len(gens)), gens))
        print('built', len(gens), 'candidates in', C)
    elif cmd == 's1':
        s1, _ = panel_keys()
        print('S1 panel:', s1)
        run_stage('s1', list(range(len(json.load(open(M + 'genomes.json'))))), s1)
        rank('s1')
    elif cmd == 's2':
        topk = int(sys.argv[2])
        order = rank('s1', top=0)
        ids = order[:topk] + ([0] if 0 not in order[:topk] else [])
        _, s2 = panel_keys()
        print('S2 panel: %d games; genomes %s' % (len(s2), ids))
        run_stage('s2', ids, s2)
        rank('s2')
    elif cmd == 'rank':
        rank(sys.argv[2], top=30)
