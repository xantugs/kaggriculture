

# ===================================== behaviour cloning driver =====================================
import glob, time, random, re


def header_teams(path):
    with open(path, 'rb') as fh:
        head = fh.read(200000).decode('utf-8', 'ignore')
    m = re.search(r'"TeamNames"\s*:\s*\[([^\]]*)\]', head)
    if not m:
        return None
    return json.loads('[' + m.group(1) + ']')


def new_store():
    return dict(cats=[], rcats=[], nums=[], ucnt=[], glob=[], mk=[], u_step=[], u_x=[], u_y=[], u_k=[], u_inv=[], u_a=[], u_q=[])


def record_step(s, obs, p, a):
    import numpy as np
    grid, g, uvec = encode(obs, p, features)
    gr = grid.reshape(C_GRID, 100)
    s['cats'].append(np.argmax(gr[0:13], 0).astype(np.uint8))
    s['rcats'].append(np.argmax(gr[24:37], 0).astype(np.uint8))
    s['nums'].append(np.clip(gr[13:24] * 50.0, 0, 255).astype(np.uint8))
    s['ucnt'].append(np.clip(gr[37] * 3.0, 0, 255).astype(np.uint8))
    s['glob'].append(g.astype(np.float16))
    ml = market_labels(a.get('market') or [])
    s['mk'].append(np.asarray([ml[h] for h in MARKET_HEADS], np.uint8))
    cmds = [a.get('farmer')] + list(a.get('hands') or [])
    si = len(s['cats']) - 1
    for k, ((x, y), uv) in enumerate(uvec):
        c, q = unit_label(cmds[k] if k < len(cmds) else ['PASS'])
        s['u_step'].append(si); s['u_x'].append(x); s['u_y'].append(y); s['u_k'].append(min(k, 15))
        s['u_inv'].append(np.clip(uv[36:48] * 10.0, 0, 255).astype(np.uint8)); s['u_a'].append(c); s['u_q'].append(q)


def pack_store(s, gid, team, won, margin):
    import numpy as np
    return dict(gid=gid, team=team, won=won, margin=margin,
                cats=np.stack(s['cats']), rcats=np.stack(s['rcats']), nums=np.stack(s['nums']), ucnt=np.stack(s['ucnt']),
                glob=np.stack(s['glob']), mk=np.stack(s['mk']),
                u_step=np.asarray(s['u_step'], np.int32), u_x=np.asarray(s['u_x'], np.uint8), u_y=np.asarray(s['u_y'], np.uint8),
                u_k=np.asarray(s['u_k'], np.uint8), u_inv=np.stack(s['u_inv']), u_a=np.asarray(s['u_a'], np.uint8),
                u_q=np.asarray(s['u_q'], np.uint8))


def extract_selfplay(seed):
    """v12 vs v12 from a fresh seed; both seats recorded from step SP_MIN_STEP on (v12-generated states)."""
    try:
        A = load('/kaggle/working/v12.py'); B = load('/kaggle/working/v12.py')
        store = {0: new_store(), 1: new_store()}
        def rec(p, inner):
            def f(obs, cfg=None):
                a = inner(obs, cfg)
                a = json.loads(json.dumps(a)) if isinstance(a, dict) else {"farmer": ["PASS"], "hands": [], "market": []}
                if int(obs['step']) >= SP_MIN_STEP:
                    record_step(store[p], obs, p, a)
                return a
            return f
        r = play(None, None, seed, agent_objs=[rec(0, A), rec(1, B)])
        rew = r['r']
        return [pack_store(store[p], -seed, 'v12', int(rew[p] > rew[1 - p]), float(rew[p] - rew[1 - p])) for p in (0, 1) if store[p]['cats']]
    except Exception:
        import traceback
        return ['ERR ' + traceback.format_exc()[-500:]]


def extract_teacher(path):
    """Replay one game; for each teacher seat return compact per-step arrays."""
    import numpy as np
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    try:
        rep = json.load(open(path, encoding='utf-8'))
        names = (rep.get('info') or {}).get('TeamNames') or []
        seats = [i for i, n in enumerate(names) if n in TEACHERS]
        if not seats:
            return []
        acts = [[(x.get('action') if isinstance(x, dict) and isinstance(x.get('action'), dict) else None) for x in s]
                for s in rep.get('steps') or []]
        seed = (rep.get('info') or {}).get('seed')
        rew = rep.get('rewards')
        store = {p: new_store() for p in seats}

        def tape(p):
            def f(obs, cfg=None):
                t = obs['step']
                a = acts[t + 1][p] if t + 1 < len(acts) else None
                a = a if isinstance(a, dict) else {"farmer": ["PASS"], "hands": [], "market": []}
                if p in store:
                    record_step(store[p], obs, p, a)
                return a
            return f
        r = play(None, None, seed, agent_objs=[tape(0), tape(1)])
        if [int(v) for v in r['r']] != [int(v) for v in rew]:
            return ['ERR not reproduced']
        out = []
        for p, s in store.items():
            won = int(rew[p] > rew[1 - p])
            out.append(pack_store(s, int(os.path.basename(path)[:-5]), names[p], won, float(rew[p] - rew[1 - p])))
        return out
    except Exception:
        import traceback
        return ['ERR ' + traceback.format_exc()[-500:]]


def main():
    import numpy as np
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from concurrent.futures import ProcessPoolExecutor
    t0 = time.time()
    files = sorted(glob.glob('/kaggle/input/**/*.json', recursive=True))
    files = [f for f in files if os.path.basename(f)[:-5].isdigit()]
    with ProcessPoolExecutor(os.cpu_count() or 4) as ex:
        heads = list(ex.map(header_teams, files, chunksize=32))
    tf = [f for f, h in zip(files, heads) if h and any(n in TEACHERS for n in h)]
    print('replays', len(files), 'with teachers', len(tf), round(time.time() - t0), 's', flush=True)
    random.seed(0); random.shuffle(tf); tf = tf[:MAX_GAMES]
    games = []; errs = 0
    with ProcessPoolExecutor(os.cpu_count() or 4) as ex:
        for k, res in enumerate(ex.map(extract_teacher, tf, chunksize=2)):
            for g in res:
                if isinstance(g, str):
                    errs += 1
                    if errs <= 3: print(g, flush=True)
                elif g['won'] or not WINS_ONLY:
                    games.append(g)
            if k % 50 == 0:
                print('extracted', k, 'teacher seats', len(games), 'errors', errs, round(time.time() - t0), 's', flush=True)
    if SELFPLAY:
        with ProcessPoolExecutor(os.cpu_count() or 4) as ex:
            for k, res in enumerate(ex.map(extract_selfplay, [7_000_000 + i for i in range(SELFPLAY)])):
                for g in res:
                    if isinstance(g, str):
                        errs += 1
                        if errs <= 6: print(g, flush=True)
                    else:
                        games.append(g)
                if k % 20 == 0:
                    print('self-play', k, 'seats', len(games), 'errors', errs, round(time.time() - t0), 's', flush=True)
    print('teacher seats', len(games), 'teams', {t: sum(1 for g in games if g['team'] == t) for t in TEACHERS + ['v12']}, flush=True)
    gids = sorted(set(g['gid'] for g in games)); random.shuffle(gids)
    vset = set(gids[:max(2, len(gids) // 20)])
    val = [g for g in games if g['gid'] in vset]; tr = [g for g in games if g['gid'] not in vset]
    print('split by episode: train seats', len(tr), 'val seats', len(val), flush=True)

    def cat_games(gs):
        off = 0; U = {k: [] for k in ('u_step', 'u_x', 'u_y', 'u_k', 'u_inv', 'u_a', 'u_q')}
        S = {k: [] for k in ('cats', 'rcats', 'nums', 'ucnt', 'glob', 'mk')}
        for g in gs:
            for k in S: S[k].append(g[k])
            U['u_step'].append(g['u_step'] + off)
            for k in ('u_x', 'u_y', 'u_k', 'u_inv', 'u_a', 'u_q'): U[k].append(g[k])
            off += len(g['cats'])
        S = {k: np.concatenate(v) for k, v in S.items()}; U = {k: np.concatenate(v) for k, v in U.items()}
        return S, U
    Str, Utr = cat_games(tr); Sva, Uva = cat_games(val)
    print('train steps', len(Str['cats']), 'unit samples', len(Utr['u_a']), 'val steps', len(Sva['cats']), flush=True)
    dev = 'cuda'
    NA, NG = len(UA), Str['glob'].shape[1]
    H = HIDDEN

    class Net(nn.Module):
        def __init__(self):
            super().__init__()
            self.c0 = nn.Conv2d(C_GRID, H, 3, padding=1); self.c1 = nn.Conv2d(H, H, 3, padding=1)
            self.c2 = nn.Conv2d(H, H, 3, padding=1); self.c3 = nn.Conv2d(H, H, 3, padding=1)
            self.g = nn.Linear(NG, H)
            self.u1 = nn.Linear(5 * H + H + H + N_UNIT, 256); self.ua = nn.Linear(256, NA); self.uq = nn.Linear(256, NQ)
            self.m1 = nn.Linear(2 * H, 256)
            self.mh = nn.ModuleDict({('mh_' + n): nn.Linear(256, s) for n, s in zip(MARKET_HEADS, MARKET_SIZES)})

        def trunk(self, grid, glob):
            h = grid
            for c in (self.c0, self.c1, self.c2, self.c3):
                h = F.relu(c(h))
            return h, F.relu(self.g(glob)), h.mean((2, 3))

    net = Net().to(dev)
    opt = torch.optim.Adam(net.parameters(), lr=1e-3)

    def grids(S, idx):
        cats = torch.as_tensor(S['cats'][idx], device=dev).long(); rc = torch.as_tensor(S['rcats'][idx], device=dev).long()
        nums = torch.as_tensor(S['nums'][idx], device=dev).float() / 50.0
        uc = torch.as_tensor(S['ucnt'][idx], device=dev).float() / 3.0
        B = len(idx)
        g = torch.zeros(B, C_GRID, 100, device=dev)
        g.scatter_(1, cats[:, None, :], 1.0)
        g[:, 13:24] = nums
        g.scatter_(1, (rc + 24)[:, None, :], 1.0)
        g[:, 37] = uc
        return g.view(B, C_GRID, 10, 10), torch.as_tensor(S['glob'][idx].astype(np.float32), device=dev)

    # unit samples grouped by step
    def unit_index(U, nsteps):
        order = np.argsort(U['u_step'], kind='stable')
        starts = np.searchsorted(U['u_step'][order], np.arange(nsteps + 1))
        return order, starts
    otr, sttr = unit_index(Utr, len(Str['cats'])); ova, stva = unit_index(Uva, len(Sva['cats']))
    wa = torch.ones(NA, device=dev)

    def batch_loss(S, U, order, starts, idx, train=True):
        grid, glob = grids(S, idx)
        h, gv, pooled = net.trunk(grid, glob)
        hp = F.pad(h, (1, 1, 1, 1))
        sel = np.concatenate([order[starts[i]:starts[i + 1]] for i in idx]) if len(idx) else np.zeros(0, np.int64)
        local = np.concatenate([np.full(starts[i + 1] - starts[i], j) for j, i in enumerate(idx)]) if len(idx) else np.zeros(0, np.int64)
        if len(sel) == 0:
            return None
        li = torch.as_tensor(local, device=dev).long()
        x = torch.as_tensor(U['u_x'][sel].astype(np.int64), device=dev); y = torch.as_tensor(U['u_y'][sel].astype(np.int64), device=dev)
        feats = [hp[li, :, y + 1, x + 1], hp[li, :, y, x + 1], hp[li, :, y + 2, x + 1], hp[li, :, y + 1, x + 2], hp[li, :, y + 1, x]]
        uv = torch.zeros(len(sel), N_UNIT, device=dev)
        uv[torch.arange(len(sel)), x] = 1.0; uv[torch.arange(len(sel)), 10 + y] = 1.0
        uv[torch.arange(len(sel)), 20 + torch.as_tensor(U['u_k'][sel].astype(np.int64), device=dev)] = 1.0
        uv[:, 36:48] = torch.as_tensor(U['u_inv'][sel].astype(np.float32), device=dev) / 10.0
        z = F.relu(net.u1(torch.cat(feats + [pooled[li], gv[li], uv], 1)))
        ya = torch.as_tensor(U['u_a'][sel].astype(np.int64), device=dev); yq = torch.as_tensor(U['u_q'][sel].astype(np.int64), device=dev)
        la = F.cross_entropy(net.ua(z), ya, weight=wa)
        pick = (ya >= UA_I['PICKUP_WHEAT']) & (ya <= UA_I['PICKUP_SHEEP'])
        lq = F.cross_entropy(net.uq(z)[pick], yq[pick]) if pick.any() else torch.zeros((), device=dev)
        m = F.relu(net.m1(torch.cat([pooled, gv], 1)))
        mk = torch.as_tensor(S['mk'][idx].astype(np.int64), device=dev)
        lm = sum(F.cross_entropy(net.mh['mh_' + n](m), mk[:, j]) for j, n in enumerate(MARKET_HEADS))
        stats = None
        if not train:
            pa = net.ua(z).argmax(1); pq = net.uq(z).argmax(1)
            full = (pa == ya) & (~pick | (pq == yq))
            mkp = [net.mh['mh_' + n](m).argmax(1) for n in MARKET_HEADS]
            stats = dict(correct=(pa == ya).float().sum().item(), full=full.float().sum().item(), n=len(ya),
                         cls=[(int(a), int(b)) for a, b in zip(ya.tolist(), pa.tolist())],
                         mk=[((mkp[j] > 0) & (mk[:, j] > 0)).sum().item() for j in range(len(MARKET_HEADS))],
                         mk_pred=[(mkp[j] > 0).sum().item() for j in range(len(MARKET_HEADS))],
                         mk_true=[(mk[:, j] > 0).sum().item() for j in range(len(MARKET_HEADS))],
                         mk_exact=[((mkp[j] == mk[:, j]) & (mk[:, j] > 0)).sum().item() for j in range(len(MARKET_HEADS))])
        return la + lq + 0.3 * lm, stats

    nsteps = len(Str['cats']); B = 128
    for ep in range(EPOCHS):
        net.train(); perm = np.random.permutation(nsteps); tl = 0.0; nb = 0
        for i in range(0, nsteps, B):
            out = batch_loss(Str, Utr, otr, sttr, perm[i:i + B])
            if out is None: continue
            loss, _ = out
            opt.zero_grad(); loss.backward(); opt.step(); tl += float(loss); nb += 1
        net.eval(); corr = full = n = 0; conf = {}
        MK = np.zeros((4, len(MARKET_HEADS)))
        with torch.no_grad():
            for i in range(0, len(Sva['cats']), 256):
                out = batch_loss(Sva, Uva, ova, stva, np.arange(i, min(i + 256, len(Sva['cats']))), train=False)
                if out is None: continue
                st = out[1]; corr += st['correct']; full += st['full']; n += st['n']
                MK += np.asarray([st['mk'], st['mk_pred'], st['mk_true'], st['mk_exact']], np.float64)
                for a, b in st['cls']:
                    e = conf.setdefault(UA[a], [0, 0]); e[0] += int(a == b); e[1] += 1
        prec = MK[0] / np.maximum(1, MK[1]); rec = MK[0] / np.maximum(1, MK[2]); exact = MK[3] / np.maximum(1, MK[2])
        print('epoch', ep, 'loss', round(tl / max(1, nb), 4), 'val class acc', round(corr / max(1, n), 4), 'full-command acc', round(full / max(1, n), 4),
              'per-class', {k: round(v[0] / v[1], 3) for k, v in sorted(conf.items(), key=lambda kv: -kv[1][1])[:16]}, round(time.time() - t0), 's', flush=True)
        print('   market nonzero precision/recall/exact:', {nm: (round(float(p_), 2), round(float(r_), 2), round(float(x_), 2), int(t_))
              for nm, p_, r_, x_, t_ in zip(MARKET_HEADS, prec, rec, exact, MK[2])}, flush=True)
    W = {k: v.detach().cpu().numpy().astype(np.float32) for k, v in net.state_dict().items()}
    W = {k.replace('mh.mh_', 'mh_'): v for k, v in W.items()}
    np.savez_compressed('/kaggle/working/bc_model.npz', **W)
    # exported numpy forward must match the trained torch model on identical inputs
    net.eval(); worst = 0.0
    with torch.no_grad():
        for i in range(0, min(len(Sva['cats']), 40), 7):
            grid, glob = grids(Sva, np.asarray([i]))
            h, gv, pooled = net.trunk(grid, glob)
            sel = ova[stva[i]:stva[i + 1]]
            if len(sel) == 0: continue
            upos = list(zip(Uva['u_x'][sel].tolist(), Uva['u_y'][sel].tolist()))
            uvecs = []
            for jj in sel:
                v = np.zeros(N_UNIT, np.float32); v[Uva['u_x'][jj]] = 1; v[10 + Uva['u_y'][jj]] = 1; v[20 + Uva['u_k'][jj]] = 1
                v[36:48] = Uva['u_inv'][jj].astype(np.float32) / 10.0; uvecs.append(v)
            ua_np, uq_np, mk_np = forward(W, grid[0].cpu().numpy(), glob[0].cpu().numpy(), uvecs, upos)
            hp = F.pad(h, (1, 1, 1, 1)); li = torch.zeros(len(sel), dtype=torch.long, device=dev)
            x = torch.as_tensor([p[0] for p in upos], device=dev); y = torch.as_tensor([p[1] for p in upos], device=dev)
            feats = [hp[li, :, y + 1, x + 1], hp[li, :, y, x + 1], hp[li, :, y + 2, x + 1], hp[li, :, y + 1, x + 2], hp[li, :, y + 1, x]]
            uv = torch.as_tensor(np.asarray(uvecs), device=dev)
            z = F.relu(net.u1(torch.cat(feats + [pooled[li], gv[li], uv], 1)))
            worst = max(worst, float(np.abs(net.ua(z).cpu().numpy() - ua_np).max()))
            m = F.relu(net.m1(torch.cat([pooled, gv], 1)))
            for nm in MARKET_HEADS:
                worst = max(worst, float(np.abs(net.mh['mh_' + nm](m).cpu().numpy()[0] - mk_np[nm]).max()))
    print('EXPORT CHECK max |torch - numpy| logit difference', worst, flush=True)
    print('saved', round(time.time() - t0), 's', flush=True)


if __name__ == '__main__':
    main()
