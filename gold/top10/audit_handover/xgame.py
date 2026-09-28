"""Cross-game state: play game 1 then game 2 with the SAME loaded agent module (as a process that reuses the agent
across episodes would), and report what game 2 starts with: ADAPT's off flag at step 0, the controller's takeover step,
whether div_over is in force, and game 2's margin (compare with a fresh module).
usage: xgame.py cand gid1 gid2"""
import sys, os, json
sys.path.insert(0, '/home/user/kaggriculture/arena')
sys.path.insert(0, '/home/user/kaggriculture/gold/harness')
from pinned4 import reference, install_pinned, _tape, _prefixed  # noqa: E402
IDX = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gid_index.json')))
import lean  # noqa: E402
from kaggle_environments.envs.kaggriculture import kaggriculture as K  # noqa: E402


def play(A, gid, S=288):
    d = json.load(open(IDX[str(gid)], encoding='utf-8'))[0]
    names = d['info']['TeamNames']; P = names.index('offhand'); O = 1 - P
    spawns, shops, _ = reference(d)
    orig = install_pinned(S // 24, O, spawns, shops)
    G = A.__globals__; GP = G['GC_P']; AD = G['_AD_STATE']
    log = {}
    inner = _prefixed(A, d['acts'], P, S)

    def f(obs, cfg=None):
        s = int(obs['step'])
        if s in (0, 1):
            log['ad_off_before_%d' % s] = bool(AD.get('off'))
        a = inner(obs, cfg)
        if s in (0, 1, 400, 530):
            log['s%d' % s] = dict(ad_off=bool(AD.get('off')), melon_on=GP.get('melon_on'), tick_defer=GP.get('tick_defer'),
                                  final_cap=GP.get('final_cap'), herd_on=GP.get('herd_on'),
                                  div_applied=bool(G['_GC_RICH'].get('div_applied')), taken=bool(G['_GC_RICH'].get('taken')))
        return a
    try:
        ag = [None, None]; ag[P] = f; ag[O] = _tape(d['acts'], O)
        r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig
    return r['r'][P] - r['r'][O], log


if __name__ == '__main__':
    cand, g1, g2 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    A = lean.load(cand)
    m1, l1 = play(A, g1)
    print('game1', g1, 'm', m1, 'ad_step', A.__globals__['_AD_REPORT'].get('ad_step'), json.dumps(l1))
    m2, l2 = play(A, g2)
    print('game2 (same module)', g2, 'm', m2, json.dumps(l2))
    B = lean.load(cand)
    m3, l3 = play(B, g2)
    print('game2 (fresh module)', g2, 'm', m3, json.dumps(l3))
