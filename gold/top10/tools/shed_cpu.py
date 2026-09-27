"""CPU time per step (time.process_time: robust to other jobs on the machine, unlike the wall-clock tmax) of our agent
in the live pinned world (S=288), for several candidates on the same games, run one after the other in one process.
usage: shed_cpu.py gid1,gid2 cand1,cand2 [corpus.json.d]"""
import sys, os, json, time
sys.path.insert(0, '/home/user/kaggriculture/arena'); sys.path.insert(0, '/home/user/kaggriculture/gold/harness')
from pinned4 import reference, install_pinned, _tape, _prefixed
import lean
gids = [int(x) for x in sys.argv[1].split(',')]; cands = sys.argv[2].split(',')
corpus = sys.argv[3] if len(sys.argv) > 3 else 'gold/top10/gates/live191.json.d'
games = {}
for fn in os.listdir(corpus):
    x = json.load(open(os.path.join(corpus, fn), encoding='utf-8'))[0]
    if x['id'] in gids:
        games[x['id']] = x
for gid in gids:
    d = games[gid]
    names = d['info']['TeamNames']; P = names.index('offhand'); O = 1 - P
    spawns, shops, rref = reference(d)
    for cand in cands:
        orig = install_pinned(12, O, spawns, shops)
        A = lean.load(cand)
        cpu = []
        def timed(obs, cfg=None, _A=A):
            t = time.process_time(); a = _A(obs, cfg); cpu.append(time.process_time() - t); return a
        ag = [None, None]; ag[P] = _prefixed(timed, d['acts'], P, 288); ag[O] = _tape(d['acts'], O)
        from kaggle_environments.envs.kaggriculture import kaggriculture as K
        try:
            r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
        finally:
            K._end_of_day = orig
        c = cpu[288:]
        print('%s %-40s m %8.0f  cpu/step max %.3f s  p99 %.3f  total %.2f s  (wall tmax %.3f)' % (
            gid, cand[-40:], r['r'][P] - r['r'][O], max(c), sorted(c)[int(0.99 * (len(c) - 1))], sum(c), r['tmax'][P]), flush=True)
