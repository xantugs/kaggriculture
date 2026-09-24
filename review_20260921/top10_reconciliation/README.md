# Top-10 reconciliation data (for the external review)

- `econ_top1.jsonl`: one line per recorded game (51 games of top-40 agents vs 2500–2780 opponents), produced by
  `econ.py`, which replays `../../replays/kgdigest_top1.json.gz` exactly with kaggle-environments 1.32.7
  (`ok: true` = local final rewards equal Kaggle's). Filled sales per product (units, revenue), purchases per
  item, hire and land spend, and end-of-day farm composition snapshots, for both seats.
- `reconcile_top10.py`: per-game reconciliation for the 30 games involving a current top-10 team. Every line is
  (top − opponent), costs negative, and each game's lines sum exactly to its final-cash margin (asserted). Means are
  reported (additive); medians only for the margin. 5 opponents with >$30k wheat round-trips are excluded.
- The game IDs and seeds are in the digests; any game can be re-simulated from `info.seed` + recorded actions
  (action at index i is the decision on observation i−1).
