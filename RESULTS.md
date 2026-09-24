# V8 review and evaluation — 20 September 2026

The selected `main.py` includes the final-day harvest/delivery fix and retains
V7's crop-forecast behavior. The full forecasting correction is implemented and
tested in `versions/main_v8_full_buffer.py`, but it was not promoted because it
performed worse in the fresh-seed comparison. No submission was made to Kaggle.

## Fresh comparison against original V7

Seeds 20000–20003, both seats, default 720-step games. Cash margin is candidate
cash minus opponent cash. W/L/T means wins/losses/ties.

| Candidate | W/L/T (8 games) | Mean cash margin |
|---|---:|---:|
| Selected V8: endgame only | 4/4/0 | $+706 |
| Experimental V8: endgame + forecast | 3/5/0 | $-2,244 |

The selected candidate has a small positive cash margin but **no demonstrated
win-rate improvement**: it split the eight matches. Four paired seed scenarios
are not enough to establish a leaderboard advantage.

| Seed | Selected V8, average over both seats | Full forecast version, average over both seats |
|---|---:|---:|
| 20000 | $+2,195 | $+2,194 |
| 20001 | $+161 | $+161 |
| 20002 | $+464 | $-7,614 |
| 20003 | $+4 | $-3,718 |

## Matched stress tests

Seeds 10000–10001, both seats. Each opponent is a parameter variant of original V7,
so these are strategy stress tests rather than independent competitors. The V7
control also ran seeds 10002–10003; the table uses only the matching two seeds.

| Opponent | V7 W/L/T | V7 mean margin | Selected V8 W/L/T | Selected V8 mean margin | Change in mean margin |
|---|---:|---:|---:|---:|---:|
| melon_rush | 4/0/0 | $+42,576 | 4/0/0 | $+43,062 | $+486 |
| crop_heavy | 4/0/0 | $+112,903 | 4/0/0 | $+113,316 | $+413 |
| livestock_heavy | 2/2/0 | $-2,918 | 2/2/0 | $-3,056 | $-139 |

The revised bot retains the same win/loss pattern as V7 in these stress tests.
Removing opening melons in the opponent (`livestock_heavy`) wins decisively on
seed 10000 but loses on seed 10001. This is a useful opening-strategy lead, not
proof that a livestock opening is generally superior. The melon and crop variants
are weak opponents here; beating them does not demonstrate broad robustness.

## Fixes and checks

- Final-day jobs account for travel, harvest, return and delivery before accepting
  a harvest. Immediate harvest can replace watering when that saves existing yield.
- The selected change preserves V7's early return buffer for the shared shed.
- The experimental forecast version books fertilized tomato/strawberry supply
  consistently with its valuation. Correcting this arithmetic changes investment
  choices; the current policy did not benefit on the measured seeds.
- **26 regression tests passed**: 13 selected-agent endgame checks, 5 checks of the
  separate forecast experiment, and 8 evaluation-harness checks.
- The harness rejects parameter typos, failed matches and invalid rewards.
- 72 completed simulation games were recorded, all reaching `DONE` for both
  agents. This includes earlier superseded candidates and V7 controls, not just
  the selected agent's 20 games.

## Earlier candidate and reproducibility

The initial full candidate lost 6/8 games against V7 on seeds 10000–10003
(mean margin -$1,419.25). Code review then restored the early delivery buffer that
an initial patch had unnecessarily removed. Its wider stress run and the initial
endgame-only run were stopped; every completed game remains in the JSONL logs,
with `.run_status.json` files explaining the interruption. Their version snapshots
are retained. Primary comparisons above use the revised candidates and separate
seeds 20000–20003.

The simulator was the unmodified Kaggle Environments **1.32.7** package, running
on Python 3.12 with `DEBUG=True` in independent agent module instances. Exact
runtime packages are pinned in `requirements-eval.txt`. The source hash and
parameters, environment configuration, seed, seat and scores are recorded for
every game. Concurrency and machine speed can affect an agent that uses a wall
clock planning budget, so these small samples should be treated as pilot results.

Selected `main.py` SHA-256: `b3ce1808da9f2846c794260f5764b36546eee99ae8636c41c9dad2e549ace20b`.

Raw evidence is in `logs/`; reproduction commands are in [README.md](README.md).
Next useful work: validate the endgame change across more unseen seed pairs and
independent opponents, then study the no-melon opening and the forecast model's
assumptions about realized fertilizer use before retuning investment parameters.
