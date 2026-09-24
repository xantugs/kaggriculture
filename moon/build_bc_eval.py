"""Kaggle evaluation notebook: BC agent (v12 + bc layer, weights from the training kernel output) vs v12, closed loop.
usage: build_bc_eval.py out.py seeds(a-b) [start_step] [opponent: v12|self]"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
out = sys.argv[1]
a, b = sys.argv[2].split('-')
start = int(sys.argv[3]) if len(sys.argv) > 3 else 0
v12 = open(os.path.join(HERE, '..', 'arena', 'cand', 'omw_v12.py'), encoding='utf-8').read()
layer = open(os.path.join(HERE, 'bc_layer.py'), encoding='utf-8').read()
src = '\n\n'.join(open(os.path.join(HERE, f), encoding='utf-8').read() for f in ('feat.py', 'bc_codec.py', 'bc_core.py'))
lean_src = open(os.path.join(HERE, '..', 'arena', 'lean.py'), encoding='utf-8').read()
dec_src = open(os.path.join(HERE, '..', 'arena', 'decouple.py'), encoding='utf-8').read()
import json, zlib, base64
blob = base64.b85encode(zlib.compress(json.dumps(dict(v12=v12, layer=layer, src=src, lean=lean_src, dec=dec_src)).encode(), 9)).decode()
script = '''# Kaggriculture BC evaluation: cloned policy vs v12, closed loop, both seats.
import os
os.environ['OMP_NUM_THREADS'] = '1'; os.environ['OPENBLAS_NUM_THREADS'] = '1'; os.environ['MKL_NUM_THREADS'] = '1'
import subprocess, sys, json, glob, zlib, base64, time
import importlib.metadata as _md
if _md.version('kaggle-environments') != '1.32.7':
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '--force-reinstall', '--no-deps', 'kaggle-environments==1.32.7'], check=False)
_BLOB = %r
_PK = json.loads(zlib.decompress(base64.b85decode(_BLOB)))
V12, LAYER, SRC = _PK['v12'], _PK['layer'], _PK['src']
open('/kaggle/working/lean.py', 'w').write(_PK['lean'])
open('/kaggle/working/decouple.py', 'w').write(_PK['dec'])
sys.path.insert(0, '/kaggle/working')
SEEDS = list(range(%d, %d + 1))
START = %d


def build():
    npz = sorted(glob.glob('/kaggle/input/**/bc_model.npz', recursive=True))[0]
    w = base64.b85encode(zlib.compress(open(npz, 'rb').read(), 9)).decode()
    lay = LAYER.replace('__BC_SRC__', repr(SRC)).replace('__BC_W__', repr(w)).replace('__BC_START__', str(START))
    open('/kaggle/working/v12.py', 'w').write(V12)
    open('/kaggle/working/bc.py', 'w').write(V12.rstrip() + '\\n' + lay)
    print('agents built; bc.py', os.path.getsize('/kaggle/working/bc.py'), flush=True)


def job(t):
    import lean, decouple
    seed, seat = t
    decouple.install(0)
    A = lean.load('/kaggle/working/bc.py'); B = lean.load('/kaggle/working/v12.py')
    r = lean.play(None, None, seed, agent_objs=[A, B] if seat == 0 else [B, A])
    us, them = r['r'][seat], r['r'][1 - seat]
    return dict(seed=seed, seat=seat, us=us, them=them, m=(us - them) if us is not None and them is not None else None,
                err=r['err'], tmax=r['tmax'][seat], tel={k: v for k, v in A.telemetry.items() if isinstance(v, (int, float, str))})


if __name__ == '__main__':
    build()
    from concurrent.futures import ProcessPoolExecutor
    t0 = time.time(); res = []
    with ProcessPoolExecutor(os.cpu_count() or 4) as ex:
        for r in ex.map(job, [(s, st) for s in SEEDS for st in (0, 1)]):
            res.append(r); print(json.dumps(r), flush=True)
    ok = [r for r in res if r['m'] is not None]
    w = sum(r['m'] > 0 for r in ok)
    print('SUMMARY bc vs v12: %%d-%%d of %%d  margin %%+.0f  us %%.0f  them %%.0f  tmax %%.3f  wall %%ds' %% (
        w, len(ok) - w, len(ok), sum(r['m'] for r in ok) / max(1, len(ok)), sum(r['us'] for r in ok) / max(1, len(ok)),
        sum(r['them'] for r in ok) / max(1, len(ok)), max(r['tmax'] for r in res), time.time() - t0), flush=True)
    json.dump(res, open('/kaggle/working/eval.json', 'w'))
''' % (blob, int(a), int(b), start)
open(out, 'w', encoding='utf-8').write(script)
compile(script, out, 'exec')
print('built', out, len(script))
