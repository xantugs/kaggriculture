# Kaggriculture agent: V8 candidate

`main.py` contains the endgame-only V8 candidate, a single-file, standard-library agent. The original
submission is retained at `versions/main_v7.py`. See [RESULTS.md](RESULTS.md) for
the measured results and limitations; this candidate is not automatically a new
champion. No Kaggle submission was made.

## Changes

- Final-day harvest assignments must leave time to return to the shed and sell.
  Existing produce is harvested without an extra watering action when needed to
  meet that deadline. V7's early delivery buffer is preserved.
- The full forecasting correction is implemented and regression-tested in
  `versions/main_v8_full_buffer.py`: fertilized crop investments reserve the same
  harvest schedule used to value them. It is **not promoted to main.py** because
  it lost 5/8 fresh-seed games against V7, with a mean margin of -$2,244.50.
  Main retains V7's forecast behavior pending further policy work.
- The local harness rejects unknown parameter names, failed games and invalid
  rewards. Agent files resolve from the project root, tools, or versions folder.
- `tools/benchmark.py` records each game's scores, seed, seats, configuration,
  agent source hashes, effective parameters and simulator version as JSONL.

## Reproduce locally

Tested on Python 3.12 with the unmodified Kaggle Environments 1.32.7 package.
The pinned dependencies below support Kaggriculture; other games in that package
may require additional dependencies.

From this directory on Windows:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --no-deps -r requirements-eval.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe tools\benchmark.py --opponents v7 -n 4 --seed0 30000
```

The review workspace already has an environment one directory above this project;
use `..\.venv\Scripts\python.exe` there. Each benchmark refuses to overwrite a
previous log. A failed game is recorded and stops the run instead of contributing
to its win rate.

For the stress tests:

```powershell
.\.venv\Scripts\python.exe tools\benchmark.py --opponents melon_rush crop_heavy livestock_heavy -n 4 --seed0 30000
```

These are deliberate parameter variants of original V7, not independently built
competitors. `melon_rush` changes the opening to 20 melons and no animals;
`crop_heavy` removes opening animals and disables later investments;
`livestock_heavy` removes opening melons. The last variant remains free to choose
crops later; none of these names guarantees a specialized competitive strategy.

## Snapshots and evidence

- `versions/main_v7.py`: untouched original.
- `versions/main_v8.py`: selected endgame-only candidate, matching `main.py`.
- `versions/main_v8_endgame_buffer.py`: identical source used in the final benchmark.
- `versions/main_v8_full_buffer.py`: experimental version with both fixes; not selected.
- `versions/main_v8_full.py` and `versions/main_v8_endgame.py`: superseded initial
  candidates retained to match the source hashes in their logs.
- `logs/*.jsonl`: raw games; completed runs also have `.summary.json` files.
  Intentionally interrupted runs have `.run_status.json` explaining their status.
- `tests/`: current-agent endgame and harness checks, plus tests of the separate
  forecast experiment. Passing its unit tests did not establish strategic strength.
- [README_v7.md](README_v7.md): original project notes and earlier experiments.

Results within each seed are paired by swapping seats. Eight games across four
seeds are four scenario pairs, not eight independent scenarios. Fresh seed ranges
must be reserved for validation when tuning parameters.
