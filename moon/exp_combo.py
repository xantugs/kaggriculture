"""Confirm the knob-screen leaders on the games the screen did not see (all but games[1::4]).
usage: exp_combo.py out.jsonl S"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import pinmulti, tune
LEAD = {'_CS_FROM': 168, '_CA_MARGIN': 0.0, '_GLUTH_H': 8, '_HD2_CARE': 0.6, '_SR_MARGIN': 14}
if __name__ == '__main__':
    out, S = sys.argv[1], int(sys.argv[2])
    B = tune.BASE
    variants = [('base', B, {})] + [(tune.label(k, v), B, {k: v}) for k, v in LEAD.items()] + \
               [('combo5', B, dict(LEAD)), ('combo4', B, {k: v for k, v in LEAD.items() if k != '_CA_MARGIN'})]
    games = pinmulti.load_games(pinmulti.GAME_FILES + ['recent_loss.json'])
    screen = set(games[1::4])
    games = [g for g in games if g not in screen]
    print('games', len(games), 'variants', len(variants), flush=True)
    pinmulti.run(games, S, variants, out, chunk=4)
    tune.summarize(out)
