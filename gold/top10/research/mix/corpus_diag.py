"""Stream a daily top-tier corpus (jsonl / jsonl.gz, one game per line), replay each game exactly (both tapes) with the
wheat_diag instruments and write a compact per-seat, per-day record: plantings by crop, end-of-day tiles by crop/animal,
units and $ sold per product, units bought, hires and hire $, land. Bounded in-flight jobs (no corpus in memory).
usage: corpus_diag.py corpus out.jsonl [max_games] [teams_file]   (NPROC env, default 2)"""
import sys, os, json, gzip, time, collections
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
sys.path.insert(0, '/home/user/kaggriculture/arena'); sys.path.insert(0, '/home/user/kaggriculture/gold/harness')
sys.path.insert(0, '/home/user/kaggriculture/gold/elite'); sys.path.insert(0, '/home/user/kaggriculture/gold/top10/tools')


def _compact(days):
    out = []
    for r in days:
        pl = collections.Counter()
        for k, v in r['plant'].items(): pl[k.split('@')[0]] += v
        out.append(dict(pl=dict(pl), t=r['tiles'], su={k: int(v) for k, v in r['sold'].items()},
                        sd={k: round(v) for k, v in r['sold_d'].items()}, bu={k: int(v) for k, v in r['bought'].items()},
                        h=r['hires'], hc=round(r['hire_cost']), land=r['land']))
    return out


def fast_play(acts, seed):
    """lean.play for two recorded tapes without per-step observation clones (tapes only read the step)."""
    import lean, contextlib, io
    from kaggle_environments.utils import Struct, structify
    K = lean.K
    env = lean._Env(seed)
    state = [Struct(observation=Struct(step=0, remainingOverageTime=60, player=i), action=None,
                    reward=0, status="ACTIVE", info=Struct()) for i in range(2)]
    with contextlib.redirect_stdout(io.StringIO()):
        K.interpreter(state, env)
    step = 0
    PASS = {"farmer": ["PASS"], "hands": [], "market": []}
    while True:
        t = state[0].observation.step
        for i in range(2):
            state[i]["action"] = None
            if state[i].status != "ACTIVE": continue
            a = acts[t + 1][i] if t + 1 < len(acts) else None
            if not isinstance(a, dict): a = PASS
            state[i]["action"] = structify(json.loads(json.dumps(a)))
            state[i].action = state[i]["action"]
        with contextlib.redirect_stdout(io.StringIO()):
            K.interpreter(state, env)
        step += 1
        state[0].observation.step = step
        for s_ in state:
            if s_.status in ("ERROR", "INVALID", "TIMEOUT"): s_.reward = None
        if state[0].observation.step >= env.configuration.episodeSteps - 1:
            for s_ in state:
                if s_.status in ("ACTIVE", "INACTIVE"): s_.status = "DONE"
        if all(s_.status != "ACTIVE" for s_ in state): break
    return {"r": [state[0].reward, state[1].reward], "shops": list(state[0].observation.town.get("unlocked_shops", []))}


def one(line):
    import lean, pinned4
    from wheat_diag import _instrument
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    d = json.loads(line)
    if len(d.get('acts') or []) != 720:
        return None
    recs, FARMS, restore = _instrument(K)
    t0 = time.time()
    try:
        if os.environ.get('FAST', '1') == '1':
            r = fast_play(d['acts'], d['info']['seed'])
        else:
            r = lean.play(None, None, d['info']['seed'], agent_objs=[pinned4._tape(d['acts'], 0), pinned4._tape(d['acts'], 1)])
    finally:
        restore()
    ok = [round(x or 0) for x in r['r']] == [round(x or 0) for x in d['rewards']]
    return dict(id=d['id'], names=d['info']['TeamNames'], rew=d['rewards'], r=r['r'], ok=ok, shops=r['shops'],
                seed=d['info']['seed'], wall=round(time.time() - t0, 1),
                f=[_compact(recs[id(FARMS[0])]), _compact(recs[id(FARMS[1])])])


def lines(path):
    op = gzip.open if path.endswith('.gz') else open
    with op(path, 'rt', encoding='utf-8') as fh:
        for l in fh:
            if l.strip(): yield l


if __name__ == '__main__':
    path, out = sys.argv[1], sys.argv[2]
    maxg = int(sys.argv[3]) if len(sys.argv) > 3 else 10 ** 6
    teams = set(open(sys.argv[4], encoding='utf-8').read().splitlines()) if len(sys.argv) > 4 else None
    nproc = int(os.environ.get('NPROC', '2'))
    done = set()
    if os.path.exists(out):
        for l in open(out, encoding='utf-8'):
            try: done.add(json.loads(l)['id'])
            except Exception: pass
    t0 = time.time(); n = 0; sub = 0
    with ProcessPoolExecutor(nproc) as ex, open(out, 'a', encoding='utf-8') as fh:
        pend = set()
        for l in lines(path):
            if sub >= maxg: break
            head = l[:400]
            try:
                gid = int(head.split('"id":')[1].split(',')[0])
            except Exception:
                gid = None
            if gid in done: continue
            if teams is not None and not any(('"%s"' % t) in head for t in teams): continue
            pend.add(ex.submit(one, l)); sub += 1
            while len(pend) >= 2 * nproc:
                dn, pend = wait(pend, return_when=FIRST_COMPLETED)
                for f in dn:
                    x = f.result()
                    if x: fh.write(json.dumps(x, ensure_ascii=False) + '\n'); fh.flush(); n += 1
        for f in pend:
            x = f.result()
            if x: fh.write(json.dumps(x, ensure_ascii=False) + '\n'); fh.flush(); n += 1
    print('done', n, 'wall %.0fs' % (time.time() - t0), flush=True)
