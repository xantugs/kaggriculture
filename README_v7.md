# Kaggriculture agent: project state

`main.py` is the submission file (currently **v7**). Single file, standard library only,
`agent` is the last callable. Submit with:

    kaggle competitions submit kaggriculture -f main.py -m "v7"

## Versions (`versions/`)

| file | what changed | evidence |
|---|---|---|
| v2 | first valuation engine | ~$89k vs `starter` |
| v3 | labor shadow price, reserves-first spending, dawn crew planning | ~$113k vs `starter` |
| v4 | animal ring around shed, overflow-only deliveries, hire_margin 2.5 | ~$142k vs `starter` |
| v5 | honest projections: planned animals + opponent herd growth, marginal fertilizer value | beat v4 **8/8** |
| v6 | no blind re-buying of escaped animals, final-day return home, eve-of-production feeding | beat v5 5/8, +$4.9k |
| v7 | `exp_shop_w` 0.5 -> 2.0 (weight on demand from shops not yet unlocked) | 1.0-3.0 all beat v6 8/8 in 8-game sweeps; v7 file itself only sanity-checked (2/2) |

If v7 misbehaves on the ladder, `versions/main_v6.py` is the last fully duel-tested file.

## Setup and tools (`tools/`)

    pip install -U kaggle-environments
    # put main.py and the versions/*.py you want to compare next to the tools, then:
    python duel.py '{}' '{}' -n 4 --patha main.py --pathb main_v6.py   # head-to-head, both seats
    python sweep.py main_v6.py '{"name": {"param": value}}' -n 4       # param variants of main.py vs a champion
    python h2h_view.py main.py main_v6.py 303                          # side-by-side trajectory of one game
    python trace.py main.py starter --seed 100                         # daily digest of one game
    python undone.py 100                                               # work left undone at each day's end
    python escapes.py '{}'                                             # income + animal escapes vs starter

One game takes ~6-9 s on one core. Keep single commands under ~5 min in sandboxes.
`harness.py` loads each agent as an independent module instance (so self-play is honest)
and sets `DEBUG=True` so exceptions surface instead of hitting the safety fallback.

## Key findings

- Market depth drives everything: eggs/wheat are bottomless; melon (~$26k) and fertilizer
  (~$25k) are one-shot pots shared with the opponent; milk/wool/strawberry crash after
  ~60-75 units but town shops create large, observable demand.
- Mid/late game is **labor-bound**, not land- or cash-bound. Hands cost fib(n) per day.
- Day-0 animals are essential (removing them: 0/6, about -$31k). Other opening variations
  tested were within noise.
- Geese are a poor mid-game asset in contested games (eggs ~$40 vs feed wheat ~$50).
- Evaluate head-to-head against the previous champion. Income vs the passive `starter`
  bot was misleading: a change that cut escapes from ~22 to 6.5/game lost to the champion.
- Results are noisy (sd ~$10-30k over 6 seeds). A +$10k edge over 6 games vanished on
  fresh seeds. Trust only large, monotone, replicated effects.

## Known gaps

- All sparring partners are variants of this code; risk of overfitting to its own style.
- Melon race on day 10 is unvalidated against a dedicated melon rusher.
- ~6 animal escapes per game remain.
- One-day lag between harvest and sale in the early game (small cost).
