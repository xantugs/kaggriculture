"""Paired closed-loop runs in the decoupled engine: agents x opponents x seeds x seats.
usage: pairs.py agents opps seeds out.jsonl"""
import sys, json, os, lean, decouple
from concurrent.futures import ProcessPoolExecutor
def job(t):
    decouple.install(0)
    ag, opp, seed, seat = t
    A = lean.load(ag); B = lean.load(opp)
    r = lean.play(None, None, seed, agent_objs=[A, B] if seat == 0 else [B, A])
    rep = {}
    for k in ('_KTT_REPORT', '_TB_REPORT', '_KSUB_REPORT', '_WRT_REPORT', '_DRIP_REPORT', '_SLOT_REPORT', '_EB_REPORT', '_GLUTH_REPORT'):
        if k in A.__globals__: rep.update({kk: v for kk, v in A.__globals__[k].items() if isinstance(v, (int, float)) and v})
    us, them = r['r'][seat], r['r'][1 - seat]
    return dict(agent=ag, opp=opp, seed=seed, seat=seat, us=us, m=(us - them) if us is not None and them is not None else None, rep=rep)
if __name__ == '__main__':
    agents = sys.argv[1].split(','); opps = sys.argv[2].split(','); seeds = [int(s) for s in sys.argv[3].split(',')]; out = sys.argv[4]
    done = set()
    if os.path.exists(out):
        for l in open(out):
            r = json.loads(l); done.add((r['agent'], r['opp'], r['seed'], r['seat']))
    jobs = [(a, o, s, st) for s in seeds for o in opps for st in (0, 1) for a in agents if (a, o, s, st) not in done]
    print(len(jobs), 'jobs', flush=True)
    with ProcessPoolExecutor(2) as ex, open(out, 'a') as fh:
        for r in ex.map(job, jobs):
            fh.write(json.dumps(r) + '\n'); fh.flush()
