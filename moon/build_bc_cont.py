"""Kaggle notebook: continuation test of the cloned policy on held-out teacher games. The teacher's recorded actions
play until step S, then the clone plays; the opponent replays its recording; from day S//24 the recorded shops and the
opponent's recorded weeds are pinned. Reports clone final cash minus the teacher's recorded cash per start step.
usage: build_bc_cont.py out.py dataset_day(YYYY-MM-DD) n_games starts(comma)"""
import sys, os, json, zlib, base64
HERE = os.path.dirname(os.path.abspath(__file__))
out, day, ngames, starts = sys.argv[1], sys.argv[2], int(sys.argv[3]), [int(x) for x in sys.argv[4].split(',')]
layer = open(os.path.join(HERE, 'bc_layer.py'), encoding='utf-8').read()
src = '\n\n'.join(open(os.path.join(HERE, f), encoding='utf-8').read() for f in ('feat.py', 'bc_codec.py', 'bc_core.py'))
lean_src = open(os.path.join(HERE, '..', 'arena', 'lean.py'), encoding='utf-8').read()
pinned_src = open(os.path.join(HERE, 'pinned.py'), encoding='utf-8').read()
blob = base64.b85encode(zlib.compress(json.dumps(dict(layer=layer, src=src, lean=lean_src, pinned=pinned_src)).encode(), 9)).decode()
script = '''# Kaggriculture BC continuation test on held-out teacher games.
import os
os.environ['OMP_NUM_THREADS'] = '1'; os.environ['OPENBLAS_NUM_THREADS'] = '1'; os.environ['MKL_NUM_THREADS'] = '1'
import subprocess, sys, json, glob, zlib, base64, time, re, random
import importlib.metadata as _md
if _md.version('kaggle-environments') != '1.32.7':
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '--force-reinstall', '--no-deps', 'kaggle-environments==1.32.7'], check=False)
_PK = json.loads(zlib.decompress(base64.b85decode(%r)))
open('/kaggle/working/lean.py', 'w').write(_PK['lean'])
open('/kaggle/working/pinned.py', 'w').write(_PK['pinned'])
sys.path.insert(0, '/kaggle/working')
TEACHERS = ['DSM', 'Vadim Vasilenko']
DAY = %r
NGAMES = %d
STARTS = %r


def build():
    npz = sorted(glob.glob('/kaggle/input/**/bc_model.npz', recursive=True))[0]
    w = base64.b85encode(zlib.compress(open(npz, 'rb').read(), 9)).decode()
    stub = "def kaggle_submission_agent(observation, configuration=None):\\n    return {'farmer': ['PASS'], 'hands': [], 'market': []}\\n"
    lay = _PK['layer'].replace('__BC_SRC__', repr(_PK['src'])).replace('__BC_W__', repr(w)).replace('__BC_START__', '0')
    open('/kaggle/working/clone.py', 'w').write(stub + lay)


def header_teams(path):
    head = open(path, 'rb').read(200000).decode('utf-8', 'ignore')
    m = re.search(r'"TeamNames"\\s*:\\s*\\[([^\\]]*)\\]', head)
    return json.loads('[' + m.group(1) + ']') if m else None


def job(t):
    import lean, pinned
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    path, P, S = t
    rep = json.load(open(path, encoding='utf-8'))
    acts = [[(x.get('action') if isinstance(x, dict) and isinstance(x.get('action'), dict) else None) for x in s] for s in rep['steps']]
    d = dict(id=int(os.path.basename(path)[:-5]), info=dict(TeamNames=rep['info']['TeamNames'], seed=rep['info']['seed']), rewards=rep['rewards'], acts=acts)
    O = 1 - P
    spawns, shops, rref = pinned.reference(d)
    orig = pinned.install_pinned(S // 24, O, spawns, shops)
    try:
        A = lean.load('/kaggle/working/clone.py')
        def ours(obs, cfg=None):
            if obs['step'] < S:
                a = acts[obs['step'] + 1][P] if obs['step'] + 1 < len(acts) else None
                return a if isinstance(a, dict) else {'farmer': ['PASS'], 'hands': [], 'market': []}
            return A(obs, cfg)
        ag = [None, None]; ag[P] = ours; ag[O] = pinned._tape(acts, O)
        t0 = time.time()
        r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
        wall = time.time() - t0
    finally:
        K._end_of_day = orig
    tel = A.telemetry
    return dict(gid=d['id'], team=rep['info']['TeamNames'][P], S=S, clone=r['r'][P], teacher=rep['rewards'][P], opp=rep['rewards'][O],
                clone_opp=r['r'][O], rec_ok=[int(x) for x in rref] == [int(x) for x in rep['rewards']],
                bc_steps=tel.get('bc_steps'), bc_errors=tel.get('bc_errors'), ms_per_step=1000 * tel.get('bc_time', 0) / max(1, tel.get('bc_steps', 1)), wall=wall)


if __name__ == '__main__':
    build()
    files = sorted(f for f in glob.glob('/kaggle/input/**/*.json', recursive=True) if os.path.basename(f)[:-5].isdigit() and DAY in f)
    random.seed(1); random.shuffle(files)
    jobs = []
    for f in files:
        h = header_teams(f)
        if not h: continue
        for P, n in enumerate(h):
            if n in TEACHERS:
                jobs += [(f, P, S) for S in STARTS]
                break
        if len(jobs) >= NGAMES * len(STARTS): break
    from concurrent.futures import ProcessPoolExecutor
    res = []
    with ProcessPoolExecutor(os.cpu_count() or 4) as ex:
        for r in ex.map(job, jobs):
            res.append(r); print(json.dumps(r, ensure_ascii=False), flush=True)
    for S in STARTS:
        rs = [r for r in res if r['S'] == S and r['clone'] is not None]
        if not rs: continue
        n = len(rs)
        print('SUMMARY start step %%d (day %%d): n %%d  clone-teacher cash %%+.0f  clone wins vs recorded opponent %%d/%%d  (teacher won %%d/%%d)  ms/step %%.1f' %% (
            S, S // 24, n, sum(r['clone'] - r['teacher'] for r in rs) / n, sum(r['clone'] > r['clone_opp'] for r in rs), n,
            sum(r['teacher'] > r['opp'] for r in rs), n, sum(r['ms_per_step'] for r in rs) / n), flush=True)
''' % (blob, day, ngames, starts)
open(out, 'w', encoding='utf-8').write(script)
compile(script, out, 'exec')
print('built', out, len(script))
