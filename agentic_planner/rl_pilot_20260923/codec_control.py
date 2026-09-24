"""Measure incumbent continuation damage from the retained codec, without a net."""
from pathlib import Path
import importlib.util
import json
import sys
from concurrent.futures import ProcessPoolExecutor

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'snapshot'))
import lean
spec = importlib.util.spec_from_file_location('codec', HERE.parents[1] / 'moon' / 'bc_codec.py')
codec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(codec)


def job(args):
    seed, seat, start, transformed = args
    A = lean.load(str(HERE/'snapshot'/'v12.py'))
    B = lean.load(str(HERE/'snapshot'/'v12.py'))
    def ours(obs, cfg):
        a = A(obs, cfg)
        if transformed and obs['step'] >= start:
            a = codec.roundtrip(a, obs['private']['inventories'])
        return a
    agents = [ours, B] if seat == 0 else [B, ours]
    r = lean.play(None, None, seed, agent_objs=agents)
    assert r['err'] == [None, None], r
    return dict(seed=seed,seat=seat,start=start,transformed=transformed,
                margin=r['r'][seat]-r['r'][1-seat],cash=r['r'][seat])


if __name__ == '__main__':
    jobs = [(s,p,t,c) for s in range(850000001,850000005) for p in (0,1) for t in (672,696) for c in (False,True)]
    rows = [job(args) for args in jobs]
    (HERE/'codec_control.json').write_text(json.dumps(rows,indent=2))
    for t in (672,696):
        d=[]
        for s in range(850000001,850000005):
            for p in (0,1):
                pair={r['transformed']:r['margin'] for r in rows if r['seed']==s and r['seat']==p and r['start']==t}
                d.append(pair[True]-pair[False])
        print(json.dumps(dict(start=t,n=len(d),mean_delta=sum(d)/len(d),min_delta=min(d),max_delta=max(d))))
