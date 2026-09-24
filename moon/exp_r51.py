"""Screen the fertilizer-crew layer's structural limits (R51/R68: active days, skipped days, hours, minimum
tour, crop windows) on omw_v13k2.py.  usage: exp_r51.py out.jsonl S [screen|rest|all] [2 = follow-up set]"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import pinmulti, tune
B = os.path.join(HERE, '..', 'arena', 'cand', 'omw_v13k2.py')
ALTS = [('_K_R51_D0', 8), ('_K_R51_D0', 10), ('_K_R51_D1', 26),
        ('_K_R51_SKIP', (12,)), ('_K_R51_SKIP', (18,)), ('_K_R51_SKIP', ()),
        ('_K_R51_QMIN', 2), ('_K_R51_QMIN', 4),
        ('_K_R51_HOURS', (1, 2)), ('_K_R51_HOURS', (0, 1, 2, 3)), ('_K_R51_HOURS', (1, 2, 3, 4, 5)),
        ('_R51_INPUT_CROPS', {'WHEAT': (2, 5, 6), 'CARROT': (2, 3, 4)}),
        ('_R51_INPUT_CROPS', {'WHEAT': (2, 4, 6), 'CARROT': (2, 4, 4)}),
        ('_R51_INPUT_CROPS', {'WHEAT': (1, 4, 6), 'CARROT': (1, 3, 4)})]
ALTS2 = [('_R51_INPUT_CROPS', {'WHEAT': (1, 4, 6), 'CARROT': (1, 3, 4)}),
         ('_R51_INPUT_CROPS', {'WHEAT': (1, 4, 6), 'CARROT': (2, 3, 4)}),
         ('_R51_INPUT_CROPS', {'WHEAT': (2, 4, 6), 'CARROT': (1, 3, 4)}),
         ('_R51_INPUT_CROPS', {'WHEAT': (2, 4, 6), 'CARROT': (2, 4, 4)}),
         ('_R51_INPUT_CROPS', {'WHEAT': (1, 4, 6), 'CARROT': (1, 4, 4)}),
         ('_R51_INPUT_CROPS', {'WHEAT': (0, 4, 6), 'CARROT': (0, 3, 4)}),
         ('_K_R51_D1', 29)]
if __name__ == '__main__':
    if len(sys.argv) > 4 and sys.argv[4] == '2':
        ALTS = ALTS2
    out, S = sys.argv[1], int(sys.argv[2])
    split = sys.argv[3] if len(sys.argv) > 3 else 'screen'
    variants = [('base', B, {})] + [('%s=%s' % (k, v), B, {k: v}) for k, v in ALTS]
    games = pinmulti.load_games(pinmulti.GAME_FILES + ['recent_loss.json'])
    if split == 'screen':
        games = games[1::4]
    elif split == 'rest':
        sc = set(games[1::4]); games = [g for g in games if g not in sc]
    print('games', len(games), 'variants', len(variants), flush=True)
    pinmulti.run(games, S, variants, out, chunk=5)
    tune.summarize(out)
