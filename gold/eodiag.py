"""End-of-day shed + carried for both seats (hour 23, before the auto-drop), and shed at hour 0."""
import sys
sys.path.insert(0, '/home/user/kaggriculture/arena')
import lean, decouple
decouple.install(0)
A = lean.load(sys.argv[1]); B = lean.load(sys.argv[2]); seed = int(sys.argv[3])
log = []
def wrap(ag, seat):
    def f(obs, cfg=None):
        a = ag(obs, cfg)
        if obs['hour'] == 23 and obs['day'] >= 12:
            sh = obs['private']['shed']; inv = obs['private']['inventories']
            log.append((obs['day'], seat, sum(sh.values()), sum(sum(i.values()) for i in inv), {k: v for k, v in sh.items() if v}))
        return a
    return f
lean.play(None, None, seed, agent_objs=[wrap(A, 0), wrap(B, 1)])
for d, s, shv, car, sh in log:
    if d in (14, 17, 20, 23, 26):
        print('day %d seat %d shed %3d carried %3d  shed=%s' % (d, s, shv, car, sh))
