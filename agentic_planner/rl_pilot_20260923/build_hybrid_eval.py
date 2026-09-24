"""Build a private Kaggle diagnostic that decomposes unit and market policy loss."""
from pathlib import Path
import base64
import json
import zlib

HERE=Path(__file__).resolve().parent
SNAP=HERE/'snapshot'
files={p.stem:p.read_text(encoding='utf-8') for p in SNAP.glob('*.py')}
blob=base64.b85encode(zlib.compress(json.dumps(files).encode(),9)).decode()
head=f'''# Private diagnostic; no competition submission.
import os
os.environ['OMP_NUM_THREADS']='1'; os.environ['OPENBLAS_NUM_THREADS']='1'; os.environ['MKL_NUM_THREADS']='1'
import sys, subprocess, json, glob, base64, zlib, copy, pickle, time
import importlib.metadata as metadata
if metadata.version('kaggle-environments')!='1.32.7':
 subprocess.run([sys.executable,'-m','pip','install','-q','--force-reinstall','--no-deps','kaggle-environments==1.32.7'],check=True)
assert metadata.version('kaggle-environments')=='1.32.7'
for name,content in json.loads(zlib.decompress(base64.b85decode({blob!r}))).items():
 open('/kaggle/working/%s.py'%name,'w',encoding='utf-8').write(content)
sys.path.insert(0,'/kaggle/working')
import numpy as np, bcm, lean, policy
STEPS=(672,696)
SEEDS=range(860000001,860000017)
MODES=('incumbent','learned_all','learned_units','learned_market')
WEIGHTS=sorted(glob.glob('/kaggle/input/**/bc_model.npz',recursive=True))[0]
'''
body=r'''
class Fork(BaseException): pass

def job(args):
 seed,seat=args
 W={k:v.astype(np.float32) for k,v in dict(np.load(WEIGHTS)).items()}
 A=lean.load('/kaggle/working/v12.py'); B=lean.load('/kaggle/working/v12.py')
 state=dict(mode=None,children=[])
 def ours(obs,cfg):
  t=obs['step']
  if state['mode'] is None and t in STEPS:
   for mode in MODES:
    path='/tmp/h_%d_%d_%s.pkl'%(os.getpid(),t,mode)
    pid=os.fork()
    if pid==0:
     state['mode']=mode;state['path']=path;state['start']=t
     break
    state['children'].append((pid,path,t,mode))
   if state['mode'] is None and t==STEPS[-1]: raise Fork()
  base=A(obs,cfg)
  if state['mode'] in (None,'incumbent'): return base
  learned=policy.policy_act(obs,W,1.0,None,True,None)
  if state['mode']=='learned_all': return learned
  if state['mode']=='learned_units':
   return dict(farmer=learned['farmer'],hands=learned['hands'],market=base['market'])
  return dict(farmer=base['farmer'],hands=base['hands'],market=learned['market'])
 agents=[None,None];agents[seat]=ours;agents[1-seat]=B
 result=None
 try: result=lean.play(None,None,seed,agent_objs=agents)
 except Fork: pass
 if state['mode'] is not None:
  out=dict(seed=seed,seat=seat,start=state['start'],mode=state['mode'],reward=result['r'],error=result['err'])
  with open(state['path'],'wb') as f: pickle.dump(out,f)
  os._exit(0)
 rows=[]
 for pid,path,start,mode in state['children']:
  os.waitpid(pid,0)
  with open(path,'rb') as f: rows.append(pickle.load(f))
  os.remove(path)
 return rows

if __name__=='__main__':
 import multiprocessing as mp
 from concurrent.futures import ProcessPoolExecutor
 jobs=[(s,p) for s in SEEDS for p in (0,1)]
 with ProcessPoolExecutor(2,mp_context=mp.get_context('spawn')) as ex:
  rows=[r for rs in ex.map(job,jobs) for r in rs]
 assert len(rows)==len(jobs)*len(STEPS)*len(MODES),len(rows)
 assert not any(any(e is not None for e in r['error']) for r in rows)
 by={(r['seed'],r['seat'],r['start'],r['mode']):r for r in rows}
 summary=[]
 for start in STEPS:
  for mode in MODES:
   values=[];wins=0
   for seed,seat in jobs:
    r=by[seed,seat,start,mode];b=by[seed,seat,start,'incumbent']
    margin=r['reward'][seat]-r['reward'][1-seat]
    baseline=b['reward'][seat]-b['reward'][1-seat]
    values.append(margin-baseline);wins+=margin>0
   summary.append(dict(start=start,mode=mode,n=len(values),wins=wins,mean_delta=float(np.mean(values)),median_delta=float(np.median(values)),min_delta=float(np.min(values)),max_delta=float(np.max(values))))
 print('FINAL',json.dumps(summary),flush=True)
 json.dump(dict(summary=summary,rows=rows),open('/kaggle/working/hybrid_results.json','w'),indent=2)
'''
out=head+body
compile(out,'hybrid_eval.py','exec')
(HERE/'hybrid_eval.py').write_text(out,encoding='utf-8')
print('built',len(out.encode()))

