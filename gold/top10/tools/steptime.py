"""Worst agent step of candidates on pinned games, as CPU time of the agent's thread (time.thread_time, robust to other
jobs sharing the machine) and as wall time. One process, games in sequence.
usage: steptime.py corpus.json.d S cand1[,cand2] gid1,gid2,...  [team]"""
import sys, os, json, time
HERE = '/home/user/kaggriculture/moon'
sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
sys.path.insert(0, os.path.join(HERE, '..', 'gold', 'harness'))
import lean  # noqa: E402
from pinned4 import reference, install_pinned, _tape, _prefixed  # noqa: E402
from kaggle_environments.envs.kaggriculture import kaggriculture as K  # noqa: E402


def main():
    split, S, cands, gids = sys.argv[1], int(sys.argv[2]), sys.argv[3].split(','), [int(x) for x in sys.argv[4].split(',')]
    team = sys.argv[5] if len(sys.argv) > 5 else 'offhand'
    files = {}
    for f in os.listdir(split):
        with open(os.path.join(split, f), encoding='utf-8') as fh:
            head = fh.read(400)
        files[int(head.split('"id":')[1].split(',')[0])] = os.path.join(split, f)
    worst = {c: (0.0, None) for c in cands}
    for gid in gids:
        d = json.load(open(files[gid], encoding='utf-8'))[0]
        names = d['info']['TeamNames']; P = names.index(team); O = 1 - P
        spawns, shops, _ = reference(d)
        for c in cands:
            orig = install_pinned(S // 24, O, spawns, shops)
            A = lean.load(c)
            st = {'cpu': 0.0, 'cpu_step': -1}

            def ours(obs, cfg=None, A=A, st=st):
                t0 = time.thread_time()
                a = A(obs, cfg)
                dt = time.thread_time() - t0
                if dt > st['cpu']:
                    st['cpu'] = dt; st['cpu_step'] = int(obs['step'])
                return a
            try:
                ag = [None, None]
                ag[P] = _prefixed(ours, d['acts'], P, S)
                ag[O] = _tape(d['acts'], O)
                r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
            finally:
                K._end_of_day = orig
            print('%d %-40s m %8.0f  cpu max %.3fs @%d  wall max %.3fs' % (gid, c[-40:], r['r'][P] - r['r'][O], st['cpu'],
                  st['cpu_step'], r['tmax'][P]), flush=True)
            if st['cpu'] > worst[c][0]:
                worst[c] = (st['cpu'], gid)
    for c, (t, g) in worst.items():
        print('WORST', c, '%.3fs' % t, g)


if __name__ == '__main__':
    main()
