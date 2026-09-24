

# ===================================== RL driver: group rollouts from forked v12 states =====================================
# v12 plays both seats up to a start step S. There the rollout process forks: one child continues with v12 (baseline),
# one with the greedy policy, K with the sampled policy. Children share the exact state and world, so their margins
# differ only through our seat's decisions (and v12's reaction to them). Sampled children train the policy with
# group-relative advantages and a PPO-clipped, KL-to-reference update.
import pickle, copy
import numpy as np
sys.path.insert(0, '/kaggle/working')
import bcm, legal, lean
UA, NQ, MARKET_HEADS, MARKET_SIZES = bcm.UA, bcm.NQ, bcm.MARKET_HEADS, bcm.MARKET_SIZES
PASS_I = UA.index('PASS')


class _Fork(BaseException):
    pass


_WCACHE = {}


def load_w(path):
    if path not in _WCACHE:
        z = np.load(path)
        _WCACHE.clear(); _WCACHE[path] = {k: z[k].astype(np.float32) for k in z.files}
    return _WCACHE[path]


def _pick(logits, rng, greedy):
    if greedy:
        return int(np.argmax(logits))
    l = logits - logits.max(); p = np.exp(l); p /= p.sum()
    return int(rng.choice(len(p), p=p))


def policy_act(obs, W, tau, rng, greedy, rec):
    p = int(obs['player']); farm = obs['farms'][p]; priv = obs.get('private') or {}
    grid, glob, uvec = bcm.encode(obs, p, bcm.features)
    upos = [u[0] for u in uvec]
    grid, glob, uvs = bcm.quantize(grid, glob, [u[1] for u in uvec])
    ua, uq, mk = bcm.forward(W, grid, glob, uvs, upos)
    shed_left = dict(priv.get('shed') or {}); seeds_left = dict(priv.get('seeds') or {})
    invs = priv.get('inventories') or []
    cmds, masks, acts, qbs, qs = [], [], [], [], []
    for k, (x, y) in enumerate(upos):
        tile = farm['tiles'][y][x]; locked = tile == 'LOCKED'
        inv = invs[k] if k < len(invs) else {}
        m = np.array([legal._bc_legal(a, (x, y), None if locked else tile, inv, shed_left, seeds_left, locked) for a in UA], bool)
        if not m.any():
            m[PASS_I] = True
        c = _pick(np.where(m, ua[k] / tau, -1e9), rng, greedy)
        a = UA[c]; qb = 0; q = 0
        if a.startswith('PICKUP_'):
            item = a[7:]; qb = max(1, min(NQ, int(shed_left.get(item, 0))))
            q = _pick(uq[k][:qb] / tau, rng, greedy)
            shed_left[item] = shed_left.get(item, 0) - (q + 1)
        if a.startswith('PLANT_'):
            seeds_left[a[6:]] = seeds_left.get(a[6:], 0) - 1
        cmds.append(bcm.decode_unit(c, q, inv)); masks.append(m); acts.append(c); qbs.append(qb); qs.append(q)
    lab = {h: _pick(mk[h] / tau, rng, greedy) for h in MARKET_HEADS}
    if rec is not None:
        rec.append(dict(grid=grid.astype(np.float16), glob=glob.astype(np.float32), upos=np.asarray(upos, np.int8),
                        uv=np.asarray(uvs, np.float32), mask=np.asarray(masks), act=np.asarray(acts, np.int16),
                        qb=np.asarray(qbs, np.int8), q=np.asarray(qs, np.int8), mk=np.asarray([lab[h] for h in MARKET_HEADS], np.int16)))
    return {'farmer': cmds[0], 'hands': cmds[1:], 'market': bcm.decode_market(lab)}


def rollout_group(job):
    seed, P, S_list, K, tau, wpath = job
    W = load_w(wpath)
    A = lean.load('/kaggle/working/v12.py'); B = lean.load('/kaggle/working/v12.py')
    st = dict(kind=None, children=[], errors=0, last_error=None)
    S_set = sorted(S_list)
    t0 = time.time()

    def ours(obs, cfg=None):
        t = int(obs['step'])
        if st['kind'] is None and t in S_set:
            for i in range(K + 2):
                path = '/tmp/rl_%d_%d_%d.pkl' % (os.getpid(), t, i)
                pid = os.fork()
                if pid == 0:
                    st['kind'] = 'v12' if i == 0 else ('greedy' if i == 1 else 'sample')
                    st['rng'] = np.random.default_rng([seed & 0x7fffffff, t, i])
                    st['rec'] = [] if i >= 2 else None
                    st['S'] = t; st['path'] = path; st['t0'] = time.time()
                    break
                st['children'].append((pid, path, t, i))
            if st['kind'] is None and t == S_set[-1]:
                raise _Fork()
        if st['kind'] in (None, 'v12'):
            return A(obs, cfg)
        try:
            return policy_act(obs, W, tau, st['rng'], st['kind'] == 'greedy', st['rec'])
        except Exception as e:
            st['errors'] += 1; st['last_error'] = repr(e)[:200]
            farm = obs['farms'][int(obs['player'])]
            return {'farmer': ['PASS'], 'hands': [['PASS'] for _ in farm['hands']], 'market': []}
    ag = [None, None]; ag[P] = ours; ag[1 - P] = B
    r = None
    try:
        r = lean.play(None, None, seed, agent_objs=ag)
    except _Fork:
        pass
    except Exception as e:
        if st['kind'] is None:
            return dict(seed=seed, P=P, children=[], error=repr(e)[:300])
    if st['kind'] is not None:
        try:
            out = dict(kind=st['kind'], S=st['S'], r=(r or {}).get('r'), errors=st['errors'], last_error=st['last_error'],
                       rec=st['rec'], wall=time.time() - st['t0'])
            with open(st['path'] + '.tmp', 'wb') as fh:
                pickle.dump(out, fh, protocol=4)
            os.replace(st['path'] + '.tmp', st['path'])
        finally:
            os._exit(0)
    res = []
    for pid, path, t, i in st['children']:
        os.waitpid(pid, 0)
        try:
            with open(path, 'rb') as fh:
                res.append(pickle.load(fh))
            os.remove(path)
        except Exception as e:
            res.append(dict(kind='lost', S=t, r=None, errors=1, last_error=repr(e)[:200], rec=None))
    return dict(seed=seed, P=P, children=res, wall=time.time() - t0)


def group_stats(g):
    """Per start step: margins of the v12 continuation, the greedy policy and the sampled policy."""
    P = g['P']; out = {}
    for c in g['children']:
        if c['r'] is None or c['r'][0] is None or c['r'][1] is None:
            continue
        m = c['r'][P] - c['r'][1 - P]
        e = out.setdefault(c['S'], dict(v12=None, greedy=None, sample=[], recs=[], errors=0))
        e['errors'] += c['errors'] or 0
        if c['kind'] == 'sample':
            e['sample'].append(m); e['recs'].append(c['rec'])
        elif c['kind'] in ('v12', 'greedy'):
            e[c['kind']] = m
    return out


def main():
    import multiprocessing as mp
    from concurrent.futures import ProcessPoolExecutor
    t_start = time.time()
    ncpu = os.cpu_count() or 4
    nw = max(1, ncpu // max(2, (K_SAMPLES + 2) // 2))
    ex = ProcessPoolExecutor(nw, mp_context=mp.get_context('fork'))
    print('cpus', ncpu, 'rollout workers', nw, flush=True)
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    dev = 'cuda' if torch.cuda.is_available() else 'cpu'
    init = sorted(glob.glob('/kaggle/input/**/%s' % INIT_NAME, recursive=True))[0]
    W0 = dict(np.load(init))
    H = W0['c0.weight'].shape[0]; NG = W0['g.weight'].shape[1]; NA = len(UA); C = W0['c0.weight'].shape[1]
    print('init', init, 'hidden', H, 'globals', NG, 'device', dev, flush=True)

    class Net(nn.Module):
        def __init__(self):
            super().__init__()
            self.c0 = nn.Conv2d(C, H, 3, padding=1); self.c1 = nn.Conv2d(H, H, 3, padding=1)
            self.c2 = nn.Conv2d(H, H, 3, padding=1); self.c3 = nn.Conv2d(H, H, 3, padding=1)
            self.g = nn.Linear(NG, H)
            self.u1 = nn.Linear(5 * H + H + H + bcm.N_UNIT, 256); self.ua = nn.Linear(256, NA); self.uq = nn.Linear(256, NQ)
            self.m1 = nn.Linear(2 * H, 256)
            self.mh = nn.ModuleDict({('mh_' + n): nn.Linear(256, s) for n, s in zip(MARKET_HEADS, MARKET_SIZES)})

    net = Net().to(dev)
    net.load_state_dict({('mh.' + k if k.startswith('mh_') else k): torch.as_tensor(v) for k, v in W0.items()})
    ref = copy.deepcopy(net).eval()
    for p_ in ref.parameters():
        p_.requires_grad_(False)
    opt = torch.optim.Adam(net.parameters(), lr=LR)

    def export(path):
        W = {k.replace('mh.mh_', 'mh_'): v.detach().cpu().numpy().astype(np.float32) for k, v in net.state_dict().items()}
        np.savez(path, **W)

    def batch(steps):
        grid = torch.as_tensor(np.stack([s['grid'] for s in steps]).astype(np.float32), device=dev)
        gl = torch.as_tensor(np.stack([s['glob'] for s in steps]), device=dev)
        li = np.concatenate([np.full(len(s['act']), j) for j, s in enumerate(steps)])
        up = np.concatenate([s['upos'] for s in steps]).astype(np.int64)
        T = lambda a, dt=torch.long: torch.as_tensor(a, device=dev, dtype=dt)
        return dict(grid=grid, glob=gl, li=T(li), x=T(up[:, 0]), y=T(up[:, 1]),
                    uv=T(np.concatenate([s['uv'] for s in steps]), torch.float32), mask=T(np.concatenate([s['mask'] for s in steps]), torch.bool),
                    act=T(np.concatenate([s['act'] for s in steps]).astype(np.int64)), qb=T(np.concatenate([s['qb'] for s in steps]).astype(np.int64)),
                    q=T(np.concatenate([s['q'] for s in steps]).astype(np.int64)), mk=T(np.stack([s['mk'] for s in steps]).astype(np.int64)),
                    adv=T(np.asarray([s['adv'] for s in steps], np.float32), torch.float32))

    def dists(model, b):
        h = b['grid']
        for c in (model.c0, model.c1, model.c2, model.c3):
            h = F.relu(c(h))
        gv = F.relu(model.g(b['glob'])); pooled = h.mean((2, 3))
        hp = F.pad(h, (1, 1, 1, 1)); li, x, y = b['li'], b['x'], b['y']
        feats = [hp[li, :, y + 1, x + 1], hp[li, :, y, x + 1], hp[li, :, y + 2, x + 1], hp[li, :, y + 1, x + 2], hp[li, :, y + 1, x]]
        z = F.relu(model.u1(torch.cat(feats + [pooled[li], gv[li], b['uv']], 1)))
        lpa = F.log_softmax((model.ua(z) / TAU).masked_fill(~b['mask'], -1e9), 1)
        ar = torch.arange(NQ, device=dev)[None]
        lpq = F.log_softmax((model.uq(z) / TAU).masked_fill(ar >= b['qb'].clamp(min=1)[:, None], -1e9), 1)
        m = F.relu(model.m1(torch.cat([pooled, gv], 1)))
        lpm = [F.log_softmax(model.mh['mh_' + n](m) / TAU, 1) for n in MARKET_HEADS]
        return lpa, lpq, lpm

    def taken(b, lpa, lpq, lpm):
        la = lpa.gather(1, b['act'][:, None])[:, 0]
        lq = lpq.gather(1, b['q'][:, None])[:, 0]
        lm = torch.stack([lpm[j].gather(1, b['mk'][:, j:j + 1])[:, 0] for j in range(len(MARKET_HEADS))], 1)
        return la, lq, lm

    def kl(lp, lr):
        return (lp.exp() * (lp - lr)).sum(-1)

    history = []
    for it in range(ITERS):
        if time.time() - t_start > TIME_BUDGET:
            print('time budget reached', flush=True); break
        wpath = '/kaggle/working/w_%d.npz' % it
        export(wpath)
        rs = np.random.RandomState(1000 + it)
        jobs = [(int(rs.randint(1, 2 ** 31 - 1)), int(rs.randint(2)), S_LIST, K_SAMPLES, TAU, wpath) for _ in range(GROUPS)]
        t0 = time.time()
        groups = list(ex.map(rollout_group, jobs))
        t_roll = time.time() - t0
        steps = []; diag = {S: dict(g=[], s=[], best=[], v=[], gw=0, vw=0, n=0) for S in S_LIST}; errs = 0; lost = 0
        for g in groups:
            if g.get('error'):
                print('group error', g['error'], flush=True); continue
            lost += sum(1 for c in g['children'] if c['kind'] == 'lost')
            for S, e in group_stats(g).items():
                errs += e['errors']
                if e['v12'] is not None and e['greedy'] is not None and e['sample']:
                    d = diag[S]; d['n'] += 1
                    d['g'].append(e['greedy'] - e['v12']); d['s'].append(np.mean(e['sample']) - e['v12'])
                    d['best'].append(max(e['sample']) - e['v12']); d['v'].append(e['v12'])
                    d['gw'] += e['greedy'] > 0; d['vw'] += e['v12'] > 0
                if len(e['sample']) >= 2:
                    R = np.asarray(e['sample'], np.float64) / MARGIN_SCALE + WIN_W * np.sign(e['sample'])
                    adv = (R - R.mean()) / max(R.std(), SIGMA_MIN)
                    for a, rec in zip(adv, e['recs']):
                        for s in rec or []:
                            s['adv'] = float(a); steps.append(s)
        for S, d in diag.items():
            if d['n']:
                print('it %d S %d n %d | greedy-v12 %+.0f  sample-v12 %+.0f  best-v12 %+.0f | wins greedy %d v12 %d | v12 margin %+.0f' % (
                    it, S, d['n'], np.mean(d['g']), np.mean(d['s']), np.mean(d['best']), d['gw'], d['vw'], np.mean(d['v'])), flush=True)
        # PPO update
        stats = dict(pg=0.0, kl=0.0, n=0)
        if steps:
            random.shuffle(steps)
            with torch.no_grad():
                olds = []
                for i in range(0, len(steps), MB):
                    b = batch(steps[i:i + MB]); olds.append(taken(b, *dists(net, b)))
            for ep in range(PPO_EPOCHS):
                for bi, i in enumerate(range(0, len(steps), MB)):
                    b = batch(steps[i:i + MB]); oa, oq, om = olds[bi]
                    lpa, lpq, lpm = dists(net, b)
                    la, lq, lm = taken(b, lpa, lpq, lpm)
                    A_u = b['adv'][b['li']]; pick = (b['qb'] > 0).float()
                    def clip_obj(new, old, adv):
                        r = torch.exp(new - old)
                        return torch.min(r * adv, torch.clamp(r, 1 - CLIP, 1 + CLIP) * adv)
                    obj = clip_obj(la, oa, A_u).sum() + (clip_obj(lq, oq, A_u) * pick).sum() + clip_obj(lm, om, b['adv'][:, None]).sum()
                    with torch.no_grad():
                        ra, rq, rm = dists(ref, b)
                    k = kl(lpa, ra).sum() + (kl(lpq, rq) * pick).sum() + sum(kl(lpm[j], rm[j]).sum() for j in range(len(MARKET_HEADS)))
                    n = len(b['adv'])
                    loss = (-obj + KL_BETA * k) / n
                    opt.zero_grad(); loss.backward()
                    torch.nn.utils.clip_grad_norm_(net.parameters(), 1.0); opt.step()
                    stats['pg'] += float(obj) / n; stats['kl'] += float(k) / n; stats['n'] += 1
        rec = dict(it=it, groups=len(groups), steps=len(steps), roll_s=round(t_roll), errors=errs, lost=lost,
                   pg=round(stats['pg'] / max(1, stats['n']), 4), kl=round(stats['kl'] / max(1, stats['n']), 4),
                   diag={S: dict(n=d['n'], greedy=round(float(np.mean(d['g'])), 1) if d['n'] else None,
                                 sample=round(float(np.mean(d['s'])), 1) if d['n'] else None) for S, d in diag.items()},
                   elapsed=round(time.time() - t_start))
        history.append(rec)
        print('ITER', json.dumps(rec), flush=True)
        export('/kaggle/working/rl_model.npz')
        json.dump(history, open('/kaggle/working/rl_history.json', 'w'))
        if os.path.exists(wpath):
            os.remove(wpath)
    ex.shutdown(wait=False, cancel_futures=True)
    print('done', round(time.time() - t_start), 's', flush=True)


if __name__ == '__main__':
    main()
