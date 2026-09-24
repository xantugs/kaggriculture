"""Fresh official-engine closed-loop comparison of small v13 parameter packages."""
from pathlib import Path
import json
import statistics
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT.parents[0]/'.venv'/'Lib'/'site-packages'))
sys.path.insert(0,str(ROOT/'arena'))

BASE=str(ROOT/'arena'/'cand'/'omw_v13k.py')
VARIANTS={
    'base':{},
    'gluth8':{'_GLUTH_H':8},
    'conservative':{'_GLUTH_H':8,'_SR_MARGIN':14,'_Y_MARGIN':-12,'_FD_FLUSH':717},
    'schedule':{'_GLUTH_H':8,'_CS_FROM':168,'_HD2_CARE':0.6},
    'screen_combo':{'_GLUTH_H':8,'_SR_MARGIN':14,'_Y_MARGIN':-12,'_FD_FLUSH':717,
                    '_CS_FROM':168,'_HD2_CARE':0.6,'_CA_MARGIN':0.0},
}


def job(args):
    import lean
    seed,seat,label=args
    A=lean.load(BASE);B=lean.load(BASE)
    A.__globals__.update(VARIANTS[label])
    agents=[A,B] if seat==0 else [B,A]
    r=lean.play(None,None,seed,agent_objs=agents)
    us=r['r'][seat];them=r['r'][1-seat]
    return dict(seed=seed,seat=seat,label=label,us=us,them=them,margin=us-them,error=r['err'],tmax=r['tmax'][seat])


if __name__=='__main__':
    chunk=int(sys.argv[1]) if len(sys.argv)>1 else 0
    chunks=int(sys.argv[2]) if len(sys.argv)>2 else 1
    seeds=range(910000001,910000031)
    jobs=[x for i,x in enumerate((
        (seed,seat,label) for seed in seeds for seat in (0,1) for label in VARIANTS
    )) if i%chunks==chunk]
    rows=[job(x) for x in jobs]
    assert not any(any(e is not None for e in r['error']) for r in rows)
    output=HERE/f'v13_fresh_closed_loop_{chunk}.json'
    output.write_text(json.dumps(rows,indent=2))
    summary=[]
    for label in VARIANTS:
        xs=[r for r in rows if r['label']==label]
        margins=[r['margin'] for r in xs]
        summary.append(dict(label=label,n=len(xs),wins=sum(v>0 for v in margins),draws=sum(v==0 for v in margins),
                            mean_margin=statistics.mean(margins),median_margin=statistics.median(margins),
                            mean_cash=statistics.mean(r['us'] for r in xs),max_turn=max(r['tmax'] for r in xs)))
    print(json.dumps({'chunk':chunk,'chunks':chunks,'output':str(output),'summary':summary},indent=2))
