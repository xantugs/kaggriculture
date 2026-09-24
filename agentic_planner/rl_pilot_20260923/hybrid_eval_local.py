"""Local worker/market decomposition using the downloaded initial model."""
from pathlib import Path
import json
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT.parents[0]/'.venv'/'Lib'/'site-packages'))
sys.path.insert(0,str(HERE/'snapshot'))
import numpy as np
import bcm,lean,policy

STEPS=(672,696)
MODES=('incumbent','learned_all','learned_units','learned_market')
WEIGHTS=HERE/'outputs'/'kaggriculture-codex-rl-pilot-0923'/'initial_model.npz'


def run(seed,seat,start,mode,W):
    A=lean.load(str(HERE/'snapshot'/'v12.py'))
    B=lean.load(str(HERE/'snapshot'/'v12.py'))
    def ours(obs,cfg):
        base=A(obs,cfg)
        if obs['step']<start or mode=='incumbent':
            return base
        learned=policy.policy_act(obs,W,1.0,None,True,None)
        if mode=='learned_all': return learned
        if mode=='learned_units':
            return dict(farmer=learned['farmer'],hands=learned['hands'],market=base['market'])
        return dict(farmer=base['farmer'],hands=base['hands'],market=learned['market'])
    agents=[ours,B] if seat==0 else [B,ours]
    result=lean.play(None,None,seed,agent_objs=agents)
    assert result['err']==[None,None],result
    return dict(seed=seed,seat=seat,start=start,mode=mode,reward=result['r'])


if __name__=='__main__':
    chunk=int(sys.argv[1]); chunks=int(sys.argv[2])
    W={k:v.astype(np.float32) for k,v in dict(np.load(WEIGHTS)).items()}
    jobs=[(s,p,t,m) for s in range(860000001,860000017) for p in (0,1) for t in STEPS for m in MODES]
    jobs=[x for i,x in enumerate(jobs) if i%chunks==chunk]
    rows=[]
    for i,(seed,seat,start,mode) in enumerate(jobs):
        rows.append(run(seed,seat,start,mode,W))
        if (i+1)%16==0: print(chunk,i+1,'/',len(jobs),flush=True)
    path=HERE/('hybrid_local_%d.json'%chunk)
    path.write_text(json.dumps(rows),encoding='utf-8')
    print(path,len(rows))
