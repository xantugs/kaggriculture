"""gold/harness/pinned4.py rows plus the candidate's worst step time (tmax, s) and wall time, run from the one-game files
<corpus>.d/<i>.json (never the whole corpus: each worker loads only its own game). Resumable by (gid, cand).
usage: pin_tmax.py corpus.json.d S cand1[,cand2] out.jsonl [team]   (env NPROC, PIN_GIDS, FIRE_TRIM)"""
import sys, os, json, time
from concurrent.futures import ProcessPoolExecutor, as_completed
HERE = '/home/user/kaggriculture/moon'
sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
sys.path.insert(0, os.path.join(HERE, '..', 'gold', 'harness'))


def _fire_trim(A, box):
    """FIRE_TRIM=1: count _trim_queue calls where trim_fix's rule (24 - hour on days 0-28) and sf8's (23 - hour) leave
    different queues (the real call runs unchanged; the other rule runs on a copy). A game with fire == 0 plays the
    same with the knob on or off."""
    G = A.__globals__; C = G['GoldCtl']; GP = G['GC_P']
    o_tq = C._trim_queue

    def tq(self, q, pos, turns_left):
        if getattr(self, 'final', False):
            return o_tq(self, q, pos, turns_left)
        alt = turns_left - 1 if GP.get('trim_fix') else turns_left + 1
        qc = list(q)
        o_tq(self, qc, pos, alt)
        out = o_tq(self, q, pos, turns_left)
        if [id(it[2]) for it in qc] != [id(it[2]) for it in q]:
            box['fire'] = box.get('fire', 0) + 1
            if 'fire_first' not in box:
                box['fire_first'] = [int(getattr(self, 'day', -1)), 24 - turns_left if GP.get('trim_fix') else 23 - turns_left]
        return out
    C._trim_queue = tq


def job(t):
    import lean
    import pinned4
    path, team, cand, S = t
    t0 = time.time(); box = {}
    o_play = lean.play

    def play(*a, **k):
        r = o_play(*a, **k)
        box['r'] = r
        return r
    lean.play = play
    o_load = lean.load
    if os.environ.get('FIRE_TRIM'):
        def load(pth):
            A = o_load(pth)
            _fire_trim(A, box)
            return A
        lean.load = load
    try:
        row = pinned4.job((path, 0, team, cand, S))
    finally:
        lean.play = o_play; lean.load = o_load
    if os.environ.get('FIRE_TRIM'):
        row['fire'] = box.get('fire', 0); row['fire_first'] = box.get('fire_first')
    r = box.get('r') or {}
    names = None
    try:
        P = row.get('seat')
    except Exception:
        P = None
    tm = r.get('tmax', [None, None])
    # our seat: pinned4 rows carry no seat; recover it from the one-game file's team names
    if P is None:
        with open(path, encoding='utf-8') as fh:
            names = json.load(fh)[0]['info']['TeamNames']      # this worker's own one-game file
        P = names.index(team) if team in names else 0
    row['tmax'] = tm[P] if isinstance(tm, list) else None
    row['wall'] = round(time.time() - t0, 1)
    return row


if __name__ == '__main__':
    split, S, cands, out = sys.argv[1], int(sys.argv[2]), sys.argv[3].split(','), sys.argv[4]
    team = sys.argv[5] if len(sys.argv) > 5 else 'offhand'
    want = set(int(x) for x in open(os.environ['PIN_GIDS']).read().split()) if os.environ.get('PIN_GIDS') else None
    done = set()
    if os.path.exists(out):
        for line in open(out, encoding='utf-8'):
            try:
                r = json.loads(line)
                if r.get('m') is not None:
                    done.add((r['gid'], r['cand']))
            except ValueError:
                pass
    games = []
    for f in sorted(os.listdir(split), key=lambda s: int(s.split('.')[0])):
        p = os.path.join(split, f)
        with open(p, encoding='utf-8') as fh:
            head = fh.read(600)
        gid = int(head.split('"id":')[1].split(',')[0])
        if team not in head.split('"TeamNames":', 1)[1].split(']', 1)[0]:
            continue
        if want is None or gid in want:
            games.append((p, gid))
    jobs = [(p, team, c, S) for p, g in games for c in cands if (g, c) not in done]
    print('games', len(games), 'jobs', len(jobs), 'done', len(done), flush=True)
    t0 = time.time(); n = 0
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '3'))) as ex, open(out, 'a', encoding='utf-8') as fh:
        futs = [ex.submit(job, j) for j in jobs]
        for fu in as_completed(futs):
            try:
                r = fu.result()
            except Exception as e:
                print('JOB FAILED', repr(e)[:200], flush=True)
                continue
            n += 1
            fh.write(json.dumps(r, ensure_ascii=False) + '\n'); fh.flush()
            print(r['gid'], r['opp'], r['cand'][-24:], 'm', r['m'], 'tmax', r.get('tmax'), 'fire', r.get('fire'),
                  '[%d/%d %.0fs]' % (n, len(jobs), time.time() - t0), flush=True)
