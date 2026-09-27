"""Which chassis layers never change play? For each `def agent(` block (its helpers + the def), build the chassis without
it, play a fixed game set, compare action streams with the reference. Blocks whose removal keeps every game identical are
reported. usage: bisect_layers.py base.py ctl_lean.py out.json"""
import sys, json, os, re, ast
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, '/home/user/kaggriculture/arena'); sys.path.insert(0, '/home/user/kaggriculture/gold/elite')
SEEDS = [6000, 6011, 6042, 6077]
OPP = '/home/user/kaggriculture/gold/elite/bases/cand_m4.py'
SP = '/tmp/claude-0/-home-user-kaggriculture/594f4611-9718-50a4-981c-abd2c30d1a91/scratchpad/bis'

def games_list():
    R = [json.loads(l) for l in open('/home/user/kaggriculture/gold/elite/elite_gate_refs.jsonl')][::30][:7]
    return R

def streams(cand):
    import lean
    from eval_elite_routes import install_town, load_games
    from transplant import build_agent
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    out = []
    for s in SEEDS:
        A = lean.load(cand); B = lean.load(OPP)
        r = lean.play(None, None, s, record=True, agent_objs=[A, B])
        out.append(json.dumps([a[0] for a in r['actions']], sort_keys=True))
    R = games_list()
    games = {g['id']: g for g in load_games('/home/user/kaggriculture/moon/elite/games_2026-09-20.jsonl.gz') if g['id'] in {r['gid'] for r in R}}
    for ref in R:
        d = games[ref['gid']]; st = ref['seat']
        rr = dict(hands=ref['hands'], money=ref['money'], outcomes={int(k): v for k, v in ref['outcomes'].items()}, shops=ref['shops'])
        orig = install_town(ref['shops'])
        try:
            ag = [None, None]; ag[st] = build_agent(d['acts'], st, rr, slack_min=20); ag[1 - st] = lean.load(cand)
            r = lean.play(None, None, ref['seed'], record=True, agent_objs=ag)
        finally:
            K._end_of_day = orig
        out.append(json.dumps([x[1 - st] for x in r['actions']], sort_keys=True))
    return out

def job(t):
    i, path = t
    try:
        return i, streams(path)
    except Exception as e:
        return i, ['ERR %r' % e]

if __name__ == '__main__':
    base, ctl, out = sys.argv[1:4]
    os.makedirs(SP, exist_ok=True)
    src = open(base, encoding='utf-8').read(); ctlsrc = open(ctl, encoding='utf-8').read()
    lines = src.split('\n')
    starts = [i for i, l in enumerate(lines) if l.startswith('def agent(')]
    # block k = (end of def k-1 .. end of def k]: helpers + capture + def; the def ends where the next top-level statement starts
    tree = ast.parse(src)
    tops = sorted(s.lineno - 1 for s in tree.body)
    def block_end(defline):  # first top-level statement line after this def (0-based)
        return next((t for t in tops if t > defline), len(lines))
    blocks = []
    prev_end = None
    for k, st in enumerate(starts):
        end = block_end(st)
        beg = block_end(starts[k - 1]) if k > 0 else None
        blocks.append((k, beg, end))
    ref_path = SP + '/ref.py'
    open(ref_path, 'w', encoding='utf-8').write(src.rstrip('\n') + '\n\n' + ctlsrc)
    jobs = [(-1, ref_path)]
    for k, beg, end in blocks:
        if beg is None: continue
        cand = lines[:beg] + lines[end:]
        p = SP + '/no_%02d.py' % k
        open(p, 'w', encoding='utf-8').write('\n'.join(cand).rstrip('\n') + '\n\n' + ctlsrc)
        jobs.append((k, p))
    res = {}
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '4'))) as ex:
        for i, s in ex.map(job, jobs):
            res[i] = s; print('done', i, flush=True)
    ref = res.pop(-1)
    dead = []; alive = []
    for k, beg, end in blocks:
        if k not in res: continue
        same = res[k] == ref
        (dead if same else alive).append(k)
        print('layer %2d lines %5d-%5d (%4d): %s' % (k, beg + 1, end, end - beg, 'DEAD on the set' if same else ('alive' if not str(res[k][0]).startswith('ERR') else res[k][0][:80])))
    json.dump(dict(dead=dead, alive=alive, blocks=blocks), open(out, 'w'))
    print('dead layers:', dead, 'lines:', sum(end - beg for k, beg, end in blocks if k in dead))
