"""One-at-a-time knob sweep of the knob-ified v13 (omw_v13k.py) on the pinned strong-team gate.
Every variant is the base with one module global overridden; the base itself runs as label 'base'.
usage: [TUNE_BASE=file] tune.py out.jsonl S [knob,knob,...|all|round2] [games=all|train|test|screen]
Summary: tune.py --sum out.jsonl"""
import sys, os, re, json, statistics as st, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
BASE = os.environ.get('TUNE_BASE') or os.path.join(HERE, '..', 'arena', 'cand', 'omw_v13k.py')

# round 2 around v15b (TUNE_BASE=../arena/cand/omw_v15bk.py): finer steps on the knobs that fired in round 1
KNOBS2 = {
    '_GLUTH_H': [6, 7, 9, 10], '_SR_MARGIN': [11, 18, 24], '_HD2_CARE': [0.5, 0.6, 0.7],
    '_K_R68_A': [1.2, 1.3], '_K_R68_B': [50.0, 90.0], '_OR2_SLOT_H': [5, 7, 8],
    '_CA_MARGIN': [-3.0, -7.0], '_CA_BUFFER': [7, 9], '_V92_P_H': [36],
}
# knob -> alternative values (base value is whatever the file holds)
KNOBS = {
    '_GLUTH_H': [6, 8, 14],
    '_CA_FROM': [4, 6], '_CA_TO': [26, 28], '_CA_MARGIN': [-10.0, 0.0], '_CA_BUFFER': [4, 12], '_CA_CASH': [400, 1500],
    '_RACE_HORIZON_CLONE': [6, 12], '_RACE_HORIZON_ESCALATED': [16, 36], '_RACE_HORIZON_MIRROR': [16, 36],
    '_HD2_RATIO': [1.1, 1.6], '_HD2_MIN_GAIN': [300.0, 1000.0], '_HD2_CARE': [0.6, 1.0], '_HD2_FROM': [168, 216], '_HD2_TO': [312, 408],
    '_CS_RATIO': [1.1, 1.6], '_CS_MIN_GAIN': [300.0, 1000.0], '_CS_FROM': [120, 168], '_CS_TO': [168, 216],
    '_SR_MARGIN': [4, 14],
    '_OR2_SLOT_MARGIN': [10.0, 35.0], '_OR2_SLOT_H': [4, 10], '_OR2_SN_H': [12, 36],
    '_V92_P_H': [24, 72], '_V92_Q_H': [24, 72], '_V92_Q_PF': [0.8, 1.2], '_V92_Q_PM': [0.3, 0.7],
    '_R37_HINGE_GAIN': [4.0, 14.0], '_V231_CAP': [3, 5], '_Y_MARGIN': [-12, 0],
    '_FD_FLUSH': [714, 717],
    '_WRT_CFG': [{'mode': 'same', 'kmax': 1}, {'mode': 'same', 'kmax': 3}], '_WF_CFG': [{'max_add': 2}, {'max_add': 5}],
    # v13 ablation (pinned S=96): R68 value threshold carries the gain; v219 cash, R51 fert, yarn days never fire.
    '_K_R68_A': [1.0, 1.1, 1.15, 1.35, 1.5], '_K_R68_B': [0.0, 30.0, 120.0], '_K_R68_RES': [1500, 5000], '_R51_INPUT_MAX_WORKERS': [2, 4],
}


def check_knobs(names):
    """Each knob must be read inside a function body (so a post-load override takes effect)."""
    src = open(BASE, encoding='utf-8').read()
    bad = [n for n in names if not re.search(r'^[ \t]+.*\b%s\b' % re.escape(n), src, flags=re.M)]
    assert not bad, ('knobs never read at call time', bad)


def label(k, v):
    if isinstance(v, dict):
        v = ','.join('%s' % (x if not isinstance(x, tuple) else '-'.join(map(str, x))) for x in v.values())
    return '%s=%s' % (k, v)


def variants(names):
    vs = [('base', BASE, {})]
    for k in names:
        for v in KNOBS[k]:
            vs.append((label(k, v), BASE, {k: v}))
    return vs


def summarize(path):
    rs = [json.loads(l) for l in open(path, encoding='utf-8')]
    by = collections.defaultdict(dict)
    for r in rs:
        if r['m'] is not None:
            by[r['gid']][r['label']] = r
    labs = list(dict.fromkeys(r['label'] for r in rs))
    out = []
    for lab in labs:
        g = [x for x, d in by.items() if lab in d and 'base' in d]
        if not g:
            continue
        d = [by[x][lab]['m'] - by[x]['base']['m'] for x in g]
        flips = sum((by[x][lab]['m'] > 0) - (by[x]['base']['m'] > 0) for x in g)
        wins = sum(by[x][lab]['m'] > 0 for x in g)
        se = st.pstdev(d) / len(d) ** .5
        out.append((st.mean(d), lab, len(g), wins, flips, se))
    for mean, lab, n, wins, flips, se in sorted(out, reverse=True):
        print(f"{lab:44s} n={n:3d} wins {wins:3d} dWin {flips:+3d} dMargin {mean:+7.0f} ±{se:4.0f}  z={mean / max(se, 1e-9):+5.1f}")


if __name__ == '__main__':
    if sys.argv[1] == '--sum':
        summarize(sys.argv[2]); sys.exit()
    import pinmulti
    out, S = sys.argv[1], int(sys.argv[2])
    if len(sys.argv) > 3 and sys.argv[3] == 'round2':
        KNOBS.update(KNOBS2); sys.argv[3] = ','.join(KNOBS2)
    names = list(KNOBS) if len(sys.argv) < 4 or sys.argv[3] == 'all' else sys.argv[3].split(',')
    split = sys.argv[4] if len(sys.argv) > 4 else 'all'
    check_knobs(names)
    games = pinmulti.load_games(pinmulti.GAME_FILES + ['recent_loss.json'])
    if split == 'screen':
        games = games[1::4]
    elif split != 'all':
        games = [g for j, g in enumerate(games) if (j % 3 == 0) == (split == 'test')]
    vs = variants(names)
    print('games', len(games), 'variants', len(vs), flush=True)
    pinmulti.run(games, S, vs, out, chunk=4)
    summarize(out)
