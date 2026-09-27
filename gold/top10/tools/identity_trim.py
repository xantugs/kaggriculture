"""Identity check for trim_fix: run the base and the candidate on pinned games (one process), record our seat's action at
every step, and report the first step where they differ next to the first step where the trim rules would leave different
queues (the fire detector of pin_tmax.py, run on the candidate). Before the first fire both must act identically.
usage: identity_trim.py corpus.json.d S base cand gid1,gid2,... [team]"""
import sys, os, json
HERE = '/home/user/kaggriculture/moon'
sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
sys.path.insert(0, os.path.join(HERE, '..', 'gold', 'harness'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lean  # noqa: E402
from pinned4 import reference, install_pinned, _tape, _prefixed  # noqa: E402
from kaggle_environments.envs.kaggriculture import kaggriculture as K  # noqa: E402


def run(d, P, O, S, spawns, shops, cand, detect):
    orig = install_pinned(S // 24, O, spawns, shops)
    A = lean.load(cand)
    box = {}; acts = []
    if detect:
        G = A.__globals__; C = G['GoldCtl']; GP = G['GC_P']; o_tq = C._trim_queue; cur = {'step': -1}

        def tq(self, q, pos, turns_left):
            if getattr(self, 'final', False):
                return o_tq(self, q, pos, turns_left)
            alt = turns_left - 1 if GP.get('trim_fix') else turns_left + 1
            qc = list(q); o_tq(self, qc, pos, alt)
            out = o_tq(self, q, pos, turns_left)
            if [id(it[2]) for it in qc] != [id(it[2]) for it in q] and 'first' not in box:
                box['first'] = cur['step']
            return out
        C._trim_queue = tq
    else:
        cur = {'step': -1}

    def ours(obs, cfg=None):
        cur['step'] = int(obs['step'])
        a = A(obs, cfg)
        acts.append(json.dumps(a, sort_keys=True))
        return a
    try:
        ag = [None, None]
        ag[P] = _prefixed(ours, d['acts'], P, S)
        ag[O] = _tape(d['acts'], O)
        r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig
    return acts, box.get('first'), r['r'][P] - r['r'][O]


def main():
    split, S, base, cand, gids = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4], [int(x) for x in sys.argv[5].split(',')]
    team = sys.argv[6] if len(sys.argv) > 6 else 'offhand'
    files = {}
    for f in os.listdir(split):
        with open(os.path.join(split, f), encoding='utf-8') as fh:
            head = fh.read(400)
        files[int(head.split('"id":')[1].split(',')[0])] = os.path.join(split, f)
    ok = 0
    for gid in gids:
        d = json.load(open(files[gid], encoding='utf-8'))[0]
        names = d['info']['TeamNames']; P = names.index(team); O = 1 - P
        spawns, shops, _ = reference(d)
        a0, _, m0 = run(d, P, O, S, spawns, shops, base, False)
        a1, fire, m1 = run(d, P, O, S, spawns, shops, cand, True)
        diff = next((i for i in range(min(len(a0), len(a1))) if a0[i] != a1[i]), None)
        # the agent is called once per step from step 0; a fire at step s changes the action returned at step s at the earliest
        good = (fire is None and diff is None) or (fire is not None and diff is not None and diff >= fire)
        ok += good
        print('%d  base m %8.0f  cand m %8.0f  first fire step %s (d%s h%s)  first differing action step %s (d%s h%s)  %s' % (
            gid, m0, m1, fire, None if fire is None else fire // 24, None if fire is None else fire % 24,
            diff, None if diff is None else diff // 24, None if diff is None else diff % 24, 'OK' if good else 'MISMATCH'), flush=True)
    print('identical before the first fire: %d of %d' % (ok, len(gids)))


if __name__ == '__main__':
    main()
