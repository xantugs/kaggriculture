"""Shop unlock days of recorded ladder games (replays both tapes; the town draws depend on the seed and play).
usage: live_shops.py games.json out.jsonl
Per game: [[day, shop], ...] in unlock order, plus the final list."""
import sys, os, json
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, '/home/user/kaggriculture/arena'); sys.path.insert(0, '/home/user/kaggriculture/gold/harness')


def job(path):
    import lean
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    from pinned4 import _tape
    d = json.load(open(path, encoding='utf-8'))[0]
    seen = []; opm = K._process_market
    def pm(state, env):
        st = state[0].observation.step; sh = list(state[0].observation.town.get('unlocked_shops', []))
        while len(seen) < len(sh):
            seen.append([st // 24, sh[len(seen)]])
        return opm(state, env)
    K._process_market = pm
    try:
        lean.play(None, None, d['info']['seed'], agent_objs=[_tape(d['acts'], 0), _tape(d['acts'], 1)])
    finally:
        K._process_market = opm
    return dict(gid=d['id'], shops=seen)


if __name__ == '__main__':
    src, out = sys.argv[1], sys.argv[2]
    split = src + '.d'
    files = sorted(os.path.join(split, f) for f in os.listdir(split) if f.startswith('a'))
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '4'))) as ex, open(out, 'w', encoding='utf-8') as fh:
        for r in ex.map(job, files):
            fh.write(json.dumps(r) + '\n'); fh.flush()
    print('done', len(files))
