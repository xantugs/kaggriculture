"""Pilot: choose a whole elite day-15 continuation by the town seen so far.

This tests a coordinated retrieval policy, not per-action prediction.  Games in
the test fold never donate their own continuation.
"""
from pathlib import Path
import copy
import json
import math
import statistics
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT.parents[0] / '.venv' / 'Lib' / 'site-packages'))
sys.path.insert(0, str(ROOT / 'arena'))
sys.path.insert(0, str(ROOT / 'moon'))
import lean
import pinned

SOURCES = [ROOT / 'moon' / 'elite' / f'games_2026-09-{day}.jsonl' for day in (20, 21, 22)]
BASE = str(ROOT / 'arena' / 'cand' / 'omw_v13f.py')
TEAMS = {'mtmr_s1', '吃白饭的大肥鱼'}
S = 360
MAX_GAMES = 190
META_PATH = HERE / 'conditioned_tape_meta_all.json'
RESULT_PATH = HERE / 'conditioned_tape_results_all.json'


def tape_action(acts, p, step):
    a = acts[step + 1][p] if step + 1 < len(acts) else None
    if isinstance(a, dict):
        return a
    return {'farmer': ['PASS'], 'hands': [], 'market': []}


def tile_key(tiles):
    out = []
    for row in tiles:
        for t in row:
            if t is None:
                out.append('.')
            elif t == 'LOCKED':
                out.append('#')
            elif isinstance(t, dict) and t.get('kind') == 'PLANT':
                out.append(str(t.get('crop'))[:2] + str(t.get('planted_day')))
            elif isinstance(t, dict) and t.get('animal'):
                out.append(str(t.get('animal'))[:2])
            elif isinstance(t, dict):
                out.append(str(t.get('kind', '?'))[:2])
            else:
                out.append('?')
    return '|'.join(out)


def load_games():
    games = []
    seen = set()
    for source in SOURCES:
        with source.open(encoding='utf-8') as fh:
            for line in fh:
                d = json.loads(line)
                seats = [p for p, name in enumerate(d['info']['TeamNames']) if name in TEAMS]
                if seats and d['id'] not in seen:
                    seen.add(d['id'])
                    d['_teacher_seat'] = seats[0]
                    games.append(d)
                if len(games) >= MAX_GAMES:
                    return games
    return games


def snapshot(d):
    p = d['_teacher_seat']
    snap = {}

    def spy(obs, cfg=None):
        if int(obs['step']) == S:
            farm = obs['farms'][p]
            private = obs['private']
            snap.update(
                key=tile_key(farm['tiles']),
                hands=len(farm.get('hands') or []),
                shops=list(obs['town'].get('unlocked_shops') or []),
                money=float(farm.get('money', 0)),
                shed=dict(private.get('shed') or {}),
                seeds=dict(private.get('seeds') or {}),
            )
        return tape_action(d['acts'], p, int(obs['step']))

    agents = [pinned._tape(d['acts'], 0), pinned._tape(d['acts'], 1)]
    agents[p] = spy
    r = lean.play(None, None, d['info']['seed'], agent_objs=agents, max_steps=S + 1)
    if r['err'] != [None, None] or not snap:
        raise RuntimeError((d['id'], r))
    snap.update(id=d['id'], team=d['info']['TeamNames'][p], seat=p,
                reward=float(d['rewards'][p]), margin=float(d['rewards'][p] - d['rewards'][1-p]))
    return snap


def shop_counts(shops):
    return {s: shops.count(s) for s in set(shops)}


def donor_distance(a, b):
    # Farm layout and hand count must align.  Then favor the same demand mix,
    # cash, and feed/fertilizer stocks at the splice point.
    if a['hands'] != b['hands'] or a['key'] != b['key']:
        return math.inf
    ca, cb = shop_counts(a['shops']), shop_counts(b['shops'])
    shop = sum(abs(ca.get(k, 0) - cb.get(k, 0)) for k in set(ca) | set(cb))
    order = sum(x != y for x, y in zip(a['shops'], b['shops']))
    stock = sum(abs(a['shed'].get(k, 0) - b['shed'].get(k, 0)) for k in set(a['shed']) | set(b['shed']))
    seeds = sum(abs(a['seeds'].get(k, 0) - b['seeds'].get(k, 0)) for k in set(a['seeds']) | set(b['seeds']))
    return (5000 * shop + 500 * order + abs(a['money'] - b['money']) / 20
            + 10 * stock + 3 * seeds)


def run_target(target, donor, spawns, shops, base_metrics=None):
    p = target['_teacher_seat']; o = 1 - p
    pd = donor['_teacher_seat']

    def retrieved(obs, cfg=None):
        t = int(obs['step'])
        src = target if t < S else donor
        seat = p if t < S else pd
        a = copy.deepcopy(tape_action(src['acts'], seat, t))
        if t >= S:
            n = len(obs['farms'][p].get('hands') or [])
            hs = list(a.get('hands') or [])
            a['hands'] = (hs + [['PASS']] * n)[:n]
        return a

    base = lean.load(BASE)

    def incumbent(obs, cfg=None):
        t = int(obs['step'])
        return tape_action(target['acts'], p, t) if t < S else base(obs, cfg)

    def play(ours):
        orig = pinned.install_pinned(S // 24, o, spawns, shops)
        try:
            agents = [None, None]
            agents[p] = ours
            agents[o] = pinned._tape(target['acts'], o)
            return lean.play(None, None, target['info']['seed'], agent_objs=agents)
        finally:
            from kaggle_environments.envs.kaggriculture import kaggriculture as K
            K._end_of_day = orig

    rb = play(incumbent) if base_metrics is None else None
    rr = play(retrieved)
    base_us = rb['r'][p] if rb is not None else base_metrics['base_us']
    base_them = rb['r'][o] if rb is not None else base_metrics['base_them']
    base_margin = base_us - base_them
    return {
        'gid': target['id'], 'donor': donor['id'], 'team': target['info']['TeamNames'][p],
        'shops_seen': shops[:len(next(m for m in METAS if m['id'] == target['id'])['shops'])],
        'distance': donor_distance(next(m for m in METAS if m['id'] == target['id']),
                                   next(m for m in METAS if m['id'] == donor['id'])),
        'tile_mismatch': sum(x != y for x, y in zip(
            next(m for m in METAS if m['id'] == target['id'])['key'].split('|'),
            next(m for m in METAS if m['id'] == donor['id'])['key'].split('|'))),
        'base_us': base_us, 'base_them': base_them, 'base_margin': base_margin,
        'retrieved_us': rr['r'][p], 'retrieved_them': rr['r'][o], 'retrieved_margin': rr['r'][p] - rr['r'][o],
        'cash_delta': rr['r'][p] - base_us,
        'margin_delta': (rr['r'][p] - rr['r'][o]) - base_margin,
        'base_err': rb['err'] if rb is not None else base_metrics.get('base_err'),
        'retrieved_err': rr['err'],
    }


if __name__ == '__main__':
    games = load_games()
    by_id = {d['id']: d for d in games}
    if META_PATH.exists():
        METAS = json.loads(META_PATH.read_text(encoding='utf-8'))
    else:
        METAS = []
        for i, d in enumerate(games):
            METAS.append(snapshot(d))
            if (i + 1) % 5 == 0:
                print('metadata', i + 1, '/', len(games), flush=True)
        META_PATH.write_text(json.dumps(METAS, ensure_ascii=False), encoding='utf-8')

    # Fixed game-level split: every fifth game is untouched by donor selection.
    tests = [m for i, m in enumerate(METAS) if i % 7 == 0][:24]
    test_ids = {m['id'] for m in tests}
    library = [m for m in METAS if m['id'] not in test_ids]
    rows = []
    for i, tm in enumerate(tests):
        choices = [(donor_distance(tm, dm), -dm['reward'], dm) for dm in library]
        choices = [x for x in choices if math.isfinite(x[0])]
        if not choices:
            rows.append({'gid': tm['id'], 'skip': 'no aligned donor'})
            continue
        dm = min(choices, key=lambda x: (x[0], x[1], x[2]['id']))[2]
        target, donor = by_id[tm['id']], by_id[dm['id']]
        spawns, shops, rref = pinned.reference(target)
        row = run_target(target, donor, spawns, shops)
        row['recorded_reproduced'] = [int(x) for x in rref] == [int(x) for x in target['rewards']]
        rows.append(row)
        print('eval', i + 1, '/', len(tests), 'delta', row['margin_delta'], 'donor', donor['id'], flush=True)

    RESULT_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    ok = [r for r in rows if 'margin_delta' in r]
    summary = {
        'games': len(ok), 'skipped': len(rows) - len(ok),
        'mean_margin_delta': statistics.mean(r['margin_delta'] for r in ok) if ok else None,
        'median_margin_delta': statistics.median(r['margin_delta'] for r in ok) if ok else None,
        'mean_cash_delta': statistics.mean(r['cash_delta'] for r in ok) if ok else None,
        'better': sum(r['margin_delta'] > 0 for r in ok),
        'win_flips_up': sum(r['base_margin'] <= 0 < r['retrieved_margin'] for r in ok),
        'win_flips_down': sum(r['base_margin'] > 0 >= r['retrieved_margin'] for r in ok),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
