import numpy as np
import bcm, legal
UA, NQ, MARKET_HEADS = bcm.UA, bcm.NQ, bcm.MARKET_HEADS
PASS_I = UA.index("PASS")

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
        rec.append(dict(grid=grid.astype(np.float32), glob=glob.astype(np.float32), upos=np.asarray(upos, np.int8),
                        uv=np.asarray(uvs, np.float32), mask=np.asarray(masks), act=np.asarray(acts, np.int16),
                        qb=np.asarray(qbs, np.int8), q=np.asarray(qs, np.int8), mk=np.asarray([lab[h] for h in MARKET_HEADS], np.int16)))
    return {'farmer': cmds[0], 'hands': cmds[1:], 'market': bcm.decode_market(lab)}


