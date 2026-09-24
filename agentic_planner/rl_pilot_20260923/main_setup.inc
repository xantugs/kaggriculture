    import shutil
    history = []
    evaluations = []
    best_score = None
    best_label = None
    selection_labels = []

    def joint(b, la, lq, lm):
        out = lm.sum(1)
        return out.index_add(0, b['li'], la + lq * (b['qb'] > 0).float())

    def assert_export_parity(model, b):
        """NumPy behavior versus Torch learner, all conditional log probabilities."""
        W = {k.replace('mh.mh_', 'mh_'): v.detach().cpu().numpy() for k, v in model.state_dict().items()}
        lpa, lpq, lpm = dists(model, b)
        worst = 0.0
        for step in range(min(3, len(b['adv']))):
            indexes = (b['li'] == step).nonzero().flatten()
            upos = list(zip(b['x'][indexes].tolist(), b['y'][indexes].tolist()))
            ua, uq, mk = bcm.forward(W, b['grid'][step].cpu().numpy(), b['glob'][step].cpu().numpy(),
                                     b['uv'][indexes].cpu().numpy(), upos)
            def logp(a):
                a = a - a.max(); return a - np.log(np.exp(a).sum())
            for j, u in enumerate(indexes.tolist()):
                mask = b['mask'][u].cpu().numpy()
                expected = logp(np.where(mask, ua[j] / TAU, -1e9))
                worst = max(worst, float(np.abs(expected[mask] - lpa[u].detach().cpu().numpy()[mask]).max()))
                qbound = max(1, int(b['qb'][u]))
                expectedq = logp(uq[j][:qbound] / TAU)
                worst = max(worst, float(np.abs(expectedq - lpq[u, :qbound].detach().cpu().numpy()).max()))
            for h, name in enumerate(MARKET_HEADS):
                worst = max(worst, float(np.abs(logp(mk[name] / TAU) - lpm[h][step].detach().cpu().numpy()).max()))
        assert worst < 0.002, ('export probability mismatch', worst)
        print('PARITY', worst, flush=True)

    def evaluate(label, path, seeds, select=False):
        nonlocal best_score, best_label
        jobs = [(seed, p, S_LIST, 0, TAU, path) for seed in seeds for p in (0, 1)]
        rows = summarize_eval(list(ex.map(rollout_group, jobs)))
        wins = sum(r['policy_margin'] > 0 for r in rows)
        draws = sum(r['policy_margin'] == 0 for r in rows)
        score = (wins + .5 * draws, float(np.mean([r['delta'] for r in rows])))
        out = dict(label=label, n=len(rows), wins=wins, draws=draws, mean_delta=score[1],
                   rows=rows, elapsed=round(time.time() - t_start), weights_sha256=hashlib.sha256(open(path, 'rb').read()).hexdigest())
        evaluations.append(out)
        json.dump(evaluations, open('/kaggle/working/evaluations.json', 'w'), indent=2)
        print('EVAL', json.dumps({k:v for k,v in out.items() if k != 'rows'}), flush=True)
        if select:
            selection_labels.append(label)
            if best_score is None or score > best_score:
                best_score, best_label = score, label
                shutil.copyfile(path, '/kaggle/working/best_model.npz')
        return out

    export('/kaggle/working/initial_model.npz')
    evaluate('initial_bc', '/kaggle/working/initial_model.npz', VAL_SEEDS, select=True)
    warm_rows = []
    for rows in ex.map(teacher_game, WARM_SEEDS):
        warm_rows.extend(rows)
    print('WARM_DATA', len(warm_rows), 'steps', len(WARM_SEEDS), 'seeds', flush=True)
    assert_export_parity(net, batch(warm_rows[:MB]))
    warm_opt = torch.optim.Adam(net.parameters(), lr=1e-4)
    for ep in range(WARM_EPOCHS):
        random.shuffle(warm_rows)
        losses = []
        for i in range(0, len(warm_rows), MB):
            b = batch(warm_rows[i:i+MB])
            la, lq, lm = taken(b, *dists(net, b))
            pick = (b['qb'] > 0).float()
            # Positive market events receive extra weight; validation decides whether this helps.
            market_weights = 1.0 + 2.0 * (b['mk'] > 0).float()
            loss = -la.mean() - (lq * pick).sum()/pick.sum().clamp(min=1) - 0.3*(lm*market_weights).sum(1).mean()
            warm_opt.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(net.parameters(), 1.0)
            warm_opt.step(); losses.append(float(loss))
        print('WARM', ep+1, float(np.mean(losses)), round(time.time()-t_start), flush=True)
    export('/kaggle/working/warm_model.npz')
    evaluate('warm_bc', '/kaggle/working/warm_model.npz', VAL_SEEDS, select=True)
    # Preserve the warmed policy as the reference for RL. Initial and warm checkpoints remain candidates.
    ref = copy.deepcopy(net).eval()
    for parameter in ref.parameters():
        parameter.requires_grad_(False)
    del warm_rows
