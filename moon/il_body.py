

# ===================================== notebook driver =====================================
import glob, time, math, random, pickle


def tile_inputs(c, n, r, G):
    """Per-tile input rows (100 x D) built from extracted/observed features; identical at play time."""
    NC = len(CATS)
    rows = []
    for i in range(100):
        x, y = i % 10, i // 10
        v = [0.0] * NC; v[c[i]] = 1.0
        v += list(n[i])
        rv = [0.0] * NC; rv[r[i]] = 1.0
        nb = [0.0] * NC
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                xx, yy = x + dx, y + dy
                if (dx or dy) and 0 <= xx < 10 and 0 <= yy < 10:
                    nb[c[yy * 10 + xx]] += 1.0 / 8.0
        xo = [0.0] * 10; xo[x] = 1.0
        yo = [0.0] * 10; yo[y] = 1.0
        rows.append(v + rv + nb + xo + yo)
    return rows   # the global vector G is appended by the model separately


def load_replay(path):
    rep = json.load(open(path, encoding='utf-8'))
    acts = [[(x.get('action') if isinstance(x, dict) and isinstance(x.get('action'), dict) else None) for x in s]
            for s in rep.get('steps') or []]
    info = rep.get('info') or {}
    eid = int(os.path.basename(path)[:-5]) if os.path.basename(path)[:-5].isdigit() else rep.get('id')
    return json.dumps(dict(id=eid, info=dict(TeamNames=info.get('TeamNames'), seed=info.get('seed')),
                           rewards=rep.get('rewards'), statuses=rep.get('statuses'), acts=acts))


def extract_file(path):
    try:
        rows = one(load_replay(path))
        return rows if rows else ['ERR not reproduced ' + os.path.basename(path)]
    except Exception as e:
        import traceback
        return ['ERR ' + os.path.basename(path) + ' ' + traceback.format_exc()[-600:]]


def main():
    import numpy as np
    import torch
    import torch.nn as nn
    from concurrent.futures import ProcessPoolExecutor
    t0 = time.time()
    rows = []
    prev = sorted(glob.glob('/kaggle/input/**/il_rows.jsonl.gz', recursive=True)) if ROWS_SRC else []
    if prev:
        import gzip
        for pth in prev:
            rows.extend(l for l in gzip.open(pth, 'rt', encoding='utf-8').read().split('
') if l.strip())
        print('loaded previous rows', len(rows), flush=True)
    files = sorted(glob.glob('/kaggle/input/**/*.json', recursive=True)) if not prev else []
    files = [f for f in files if os.path.basename(f)[:-5].isdigit()]
    random.seed(0); random.shuffle(files)
    files = files[:MAX_GAMES]
    print('replay files', len(files), flush=True)
    ok = 0
    with ProcessPoolExecutor(os.cpu_count() or 4) as ex:
        errs = 0
        for k, rs in enumerate(ex.map(extract_file, files, chunksize=4)):
            if rs and not rs[0].startswith('ERR'):
                ok += 1; rows.extend(rs)
            else:
                errs += 1
                if errs <= 5:
                    print(rs[0] if rs else 'ERR empty', flush=True)
            if k % 100 == 0:
                print('extracted', k, 'games ok', ok, 'rows', len(rows), round(time.time() - t0), 's', flush=True)
    import gzip
    with gzip.open('/kaggle/working/il_rows.jsonl.gz', 'wt', encoding='utf-8') as fh:
        fh.write('\n'.join(rows))
    print('extraction done', ok, 'games', len(rows), 'rows', round(time.time() - t0), 's', flush=True)

    recs = [json.loads(x) for x in rows]
    if TEAMS:
        recs = [x for x in recs if x['team'] in TEAMS and MIN_DAY <= x['d'] <= 28]
    else:
        recs = [x for x in recs if x['w'] == 1 and MIN_DAY <= x['d'] <= 28]
    print('training samples', len(recs), 'teams', TEAMS or 'winners', flush=True)
    gids = sorted(set(x['g'] for x in recs)); random.shuffle(gids)
    val_g = set(gids[:max(1, len(gids) // 10)])
    NL = len(LABELS)

    def tensors(rs):
        X = np.zeros((len(rs) * 100, len(tile_inputs([0] * 100, [[0.0] * N_NUM] * 100, [0] * 100, [])[0])), np.float32)
        Gm = np.zeros((len(rs) * 100, len(GLOBAL_NAMES)), np.float32)
        Y = np.zeros((len(rs) * 100, NL), np.float32)
        for j, x in enumerate(rs):
            X[j * 100:(j + 1) * 100] = np.asarray(tile_inputs(x['c'], x['n'], x['r'], x['G']), np.float32)
            Gm[j * 100:(j + 1) * 100] = np.asarray(x['G'], np.float32)[None, :]
            yb = np.asarray(x['y'], np.int64)
            for l in range(NL):
                Y[j * 100:(j + 1) * 100, l] = (yb >> l) & 1
        return X, Gm, Y

    tr = [x for x in recs if x['g'] not in val_g]; va = [x for x in recs if x['g'] in val_g]
    Xtr, Gtr, Ytr = tensors(tr); Xva, Gva, Yva = tensors(va)
    # skip locked tiles (never acted on)
    keep_tr = Xtr[:, CAT_I['LOCKED']] < 0.5; keep_va = Xva[:, CAT_I['LOCKED']] < 0.5
    Xtr, Gtr, Ytr = Xtr[keep_tr], Gtr[keep_tr], Ytr[keep_tr]
    Xva, Gva, Yva = Xva[keep_va], Gva[keep_va], Yva[keep_va]
    gmu, gsd = Gtr.mean(0), Gtr.std(0) + 1e-3
    xmu, xsd = Xtr.mean(0), Xtr.std(0) + 1e-3
    print('train tiles', len(Xtr), 'val tiles', len(Xva), 'label rates', dict(zip(LABELS, np.round(Ytr.mean(0), 4).tolist())), flush=True)

    dev = 'cuda' if torch.cuda.is_available() else 'cpu'
    DX, DG, H = Xtr.shape[1], Gtr.shape[1], HIDDEN

    class Net(nn.Module):
        def __init__(self):
            super().__init__()
            self.wx = nn.Linear(DX, H); self.wg = nn.Linear(DG, H, bias=False)
            self.l2 = nn.Linear(H, H); self.out = nn.Linear(H, NL)

        def forward(self, x, g):
            h = torch.relu(self.wx(x) + self.wg(g))
            h = torch.relu(self.l2(h))
            return self.out(h)

    net = Net().to(dev)
    opt = torch.optim.Adam(net.parameters(), lr=2e-3)
    pos = torch.tensor(np.clip((1 - Ytr.mean(0)) / np.maximum(Ytr.mean(0), 1e-4), 1, 30) ** 0.5, device=dev)
    lossf = nn.BCEWithLogitsLoss(pos_weight=pos)
    T = lambda a: torch.tensor(a, device=dev)
    Xt, Gt, Yt = T((Xtr - xmu) / xsd), T((Gtr - gmu) / gsd), T(Ytr)
    Xv, Gv, Yv = T((Xva - xmu) / xsd), T((Gva - gmu) / gsd), T(Yva)
    n = len(Xt); bs = 8192
    for ep in range(EPOCHS):
        net.train(); perm = torch.randperm(n, device=dev); tl = 0.0
        for i in range(0, n, bs):
            b = perm[i:i + bs]
            loss = lossf(net(Xt[b], Gt[b]), Yt[b])
            opt.zero_grad(); loss.backward(); opt.step(); tl += float(loss) * len(b)
        if ep % 5 == 4 or ep == EPOCHS - 1:
            net.eval()
            with torch.no_grad():
                pv = torch.sigmoid(net(Xv, Gv)).cpu().numpy()
            yv = Yva
            f1s = []
            for l in range(NL):
                best = (0, 0.5)
                for th in np.linspace(0.05, 0.95, 19):
                    pr = pv[:, l] > th; tp = (pr & (yv[:, l] > 0.5)).sum(); fp = (pr & (yv[:, l] < 0.5)).sum(); fn = ((~pr) & (yv[:, l] > 0.5)).sum()
                    f1 = 2 * tp / max(1, 2 * tp + fp + fn)
                    if f1 > best[0]: best = (f1, th)
                f1s.append(best)
            print('epoch', ep, 'train loss', round(tl / n, 4), 'val F1', {LABELS[l]: round(f1s[l][0], 3) for l in range(NL)}, flush=True)
    W = {k: v.detach().cpu().numpy().tolist() for k, v in net.state_dict().items()}
    model = dict(labels=LABELS, cats=CATS, global_names=GLOBAL_NAMES, hidden=H, weights=W,
                 xmu=xmu.tolist(), xsd=xsd.tolist(), gmu=gmu.tolist(), gsd=gsd.tolist(),
                 thresholds=[f1s[l][1] for l in range(NL)], val_f1=[f1s[l][0] for l in range(NL)],
                 games=len(gids), min_day=MIN_DAY)
    json.dump(model, open('/kaggle/working/il_model.json', 'w'))
    print('saved model; total', round(time.time() - t0), 's', flush=True)


if __name__ == '__main__':
    main()
