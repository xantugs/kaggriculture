def teacher_game(seed):
    """Collect incumbent decisions only on its own late-game trajectory."""
    rows = []
    A = lean.load('/kaggle/working/v12.py')
    B = lean.load('/kaggle/working/v12.py')

    def wrapped(p, inner):
        def act(obs, cfg):
            action = inner(obs, cfg)
            if obs['step'] >= min(S_LIST):
                grid, glob, uvec = bcm.encode(obs, p, bcm.features)
                grid, glob, uv = bcm.quantize(grid, glob, [u[1] for u in uvec])
                commands = [action.get('farmer', ['PASS'])] + list(action.get('hands') or [])
                labels = [bcm.unit_label(commands[k] if k < len(commands) else ['PASS']) for k in range(len(uvec))]
                acts = np.asarray([a for a, q in labels], np.int16)
                qs = np.asarray([q for a, q in labels], np.int8)
                qb = np.asarray([NQ if UA[a].startswith('PICKUP_') else 0 for a in acts], np.int8)
                mk = bcm.market_labels(action.get('market') or [])
                rows.append(dict(grid=grid, glob=glob, upos=np.asarray([u[0] for u in uvec], np.int8),
                                 uv=np.asarray(uv), mask=np.ones((len(uvec), len(UA)), bool),
                                 act=acts, qb=qb, q=qs, mk=np.asarray([mk[h] for h in MARKET_HEADS], np.int16), adv=0.0))
            return action
        return act

    result = lean.play(None, None, seed, agent_objs=[wrapped(0, A), wrapped(1, B)])
    assert result['err'] == [None, None], result['err']
    return rows


def summarize_eval(groups):
    """One row per independent seed, seat, and continuation start."""
    rows = []
    for g in groups:
        assert not g.get('error'), g.get('error')
        assert not any(c.get('errors') or c['r'] is None or None in c['r'] for c in g['children']), 'evaluation failure'
        for S, e in group_stats(g).items():
            assert e['v12'] is not None and e['greedy'] is not None
            rows.append(dict(seed=g['seed'], seat=g['P'], start=S,
                             baseline_margin=e['v12'], policy_margin=e['greedy'],
                             delta=e['greedy'] - e['v12']))
    return rows
