"""Behaviour cloning v2: observation encoding and numpy forward pass. Relies on bc_codec (UA, NQ, MARKET_HEADS,
MARKET_SIZES) being defined in the same namespace (the builders concatenate bc_codec.py before this file).
Grid channels (C=38 per tile): own category one-hot (13), own numeric (11), rival category one-hot (13), own-unit count.
Global vector: feat.features() globals + hour one-hot + hires/hands/step + carried totals (12).
Unit vector: x one-hot, y one-hot, unit index one-hot (16), carried items (12)."""
import numpy as np

ITEMS = ['WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'MELON', 'EGG', 'MILK', 'WOOL', 'FERTILIZER', 'GOOSE', 'COW', 'SHEEP']
C_GRID = 38
N_UNIT = 10 + 10 + 16 + 12


def encode(obs, p, features):
    """-> grid [C,10,10] float32, glob [G] float32, and the per-unit list [(pos, unit_vec)]."""
    cats, nums, rcats, G = features(obs, p)
    grid = np.zeros((C_GRID, 100), np.float32)
    idx = np.arange(100)
    grid[np.asarray(cats), idx] = 1.0
    grid[13:24, :] = np.asarray(nums, np.float32).T
    grid[24 + np.asarray(rcats), idx] = 1.0
    farm = obs['farms'][p]
    units = [tuple(farm['farmer'])] + [tuple(h) for h in farm['hands']]
    for (x, y) in units:
        grid[37, y * 10 + x] += 1.0 / 3.0
    hour = int(obs['step']) % 24
    hv = np.zeros(24, np.float32); hv[hour] = 1.0
    invs = (obs.get('private') or {}).get('inventories') or []
    carried = np.zeros(12, np.float32)
    uvec = []
    for k, (x, y) in enumerate(units):
        v = np.zeros(N_UNIT, np.float32)
        v[x] = 1.0; v[10 + y] = 1.0; v[20 + min(k, 15)] = 1.0
        inv = invs[k] if k < len(invs) else {}
        for j, it in enumerate(ITEMS):
            c = float(inv.get(it, 0))
            v[36 + j] = c / 10.0
            carried[j] += c
        uvec.append(((x, y), v))
    glob = np.concatenate([np.asarray(G, np.float32), hv,
                           np.asarray([farm.get('hires_today', 0) / 10.0, len(farm['hands']) / 12.0, int(obs['step']) / 720.0], np.float32),
                           carried / 20.0])
    return grid.reshape(C_GRID, 10, 10), glob, uvec


def quantize(grid, glob, uvecs):
    """Apply the training-store rounding (uint8 / float16) so play-time inputs match what the model was fit on."""
    g = grid.reshape(C_GRID, 100).copy()
    g[13:24] = np.clip(g[13:24] * 50.0, 0, 255).astype(np.uint8).astype(np.float32) / 50.0
    g[37] = np.clip(g[37] * 3.0, 0, 255).astype(np.uint8).astype(np.float32) / 3.0
    uq = []
    for u in uvecs:
        u = u.copy(); u[36:48] = np.clip(u[36:48] * 10.0, 0, 255).astype(np.uint8).astype(np.float32) / 10.0; uq.append(u)
    return g.reshape(C_GRID, 10, 10), glob.astype(np.float16).astype(np.float32), uq


def conv3(x, w, b):
    """x [Cin,10,10], w [Cout,Cin,3,3] -> [Cout,10,10] (padding 1) via im2col."""
    cin = x.shape[0]
    xp = np.zeros((cin, 12, 12), np.float32); xp[:, 1:11, 1:11] = x
    cols = np.empty((9, cin, 100), np.float32)
    k = 0
    for dy in range(3):
        for dx in range(3):
            cols[k] = xp[:, dy:dy + 10, dx:dx + 10].reshape(cin, 100)
            k += 1
    wm = w.transpose(0, 2, 3, 1).reshape(w.shape[0], 9 * cin)
    return (wm @ cols.reshape(9 * cin, 100) + b[:, None]).reshape(w.shape[0], 10, 10)


def forward(W, grid, glob, uvecs, upos, n_conv=4):
    """Returns (unit logits [U,A], qty logits [U,NQ], market logits dict)."""
    h = grid
    for i in range(n_conv):
        h = np.maximum(0.0, conv3(h, W['c%d.weight' % i], W['c%d.bias' % i]))
    gv = np.maximum(0.0, W['g.weight'] @ glob + W['g.bias'])
    pooled = h.reshape(h.shape[0], 100).mean(1)
    hp = np.zeros((h.shape[0], 12, 12), np.float32); hp[:, 1:11, 1:11] = h
    U = []
    for (x, y), uv in zip(upos, uvecs):
        loc = [hp[:, y + 1, x + 1], hp[:, y, x + 1], hp[:, y + 2, x + 1], hp[:, y + 1, x + 2], hp[:, y + 1, x]]
        U.append(np.concatenate(loc + [pooled, gv, uv]))
    U = np.asarray(U, np.float32)
    z = np.maximum(0.0, U @ W['u1.weight'].T + W['u1.bias'])
    ua = z @ W['ua.weight'].T + W['ua.bias']
    uq = z @ W['uq.weight'].T + W['uq.bias']
    m = np.maximum(0.0, W['m1.weight'] @ np.concatenate([pooled, gv]) + W['m1.bias'])
    mk = {name: W['mh_%s.weight' % name] @ m + W['mh_%s.bias' % name] for name in MARKET_HEADS}
    return ua, uq, mk
