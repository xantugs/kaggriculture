# moon/ — evaluation kit and the day-15 planner experiment (22 Sep 2026)

Run everything from this folder with `..\..\.venv\Scripts\python.exe`. Uses 16 processes.

## Gates for a v12 patch

| gate | command | time | what it measures |
|---|---|---|---|
| closed loop vs v12 | `batch.py cand.py ../arena/cand/omw_v12.py 2000-2031 out.jsonl` | ~1 min / 64 games | decoupled engine, both seats; prints W-L-T, margin, per-product net deltas |
| strong teams, pinned | `pinned.py loss_0922c.json,loss_0922b.json,v10v11_top_0922.json,v12_all_0922.json,strong_new.json 360 ../arena/cand/omw_v12.py,cand.py out.jsonl` | ~5 min / 87+ games per candidate | our recorded game up to step S, then the candidate; opponent replays its recorded moves; from day S//24 the recorded shops and the opponent's recorded weeds are pinned, our weeds come from a private stream |

`pinned.py` checks that every recorded game reproduces exactly before using it (`recOK`). Set `PYTHONIOENCODING=utf-8` on Windows; team names are not ASCII.
Pick S at or before the first step the patch can change. Include wins (`v12_all_0922.json`), not only losses.

Reference, v12 continuing from day 15 on 87 strong-team games: **57-30, margin +$7,251**.

## Tools
- `batch.py`, `tune.py` (random search over MOON_P), `pinned.py`, `pin1.py` / `pinleak.py` / `pinmix.py` (single pinned game: daily farm, overflow, action mix)
- `diag.py`, `sales.py`, `ledger.py`, `leaks.py`, `hours.py`, `mix.py`, `deaths.py`, `prodtrace.py`: closed-loop single-game instruments
- `fetch.py ids.txt out.json`: downloads public replays (`/competitions/episodes/<id>/replay.json`, ~32 MB each) into the compact format

## The planner experiment (moon.py) — stopped
A from-scratch controller for every unit and the market from a chosen step (`build.py out.py '{"start": 360}'`).
Daily plan at hour 0: job values per tile, sweep routing with 2-opt, Fibonacci-aware hiring, just-in-time seeds,
capacity-aware selling and delivery. Legal full seasons, zero errors, labor more efficient than v12.

It stayed $15-18k per game behind v12's own continuation on the strong-team gate (worse in every game), after ~25
iterations. Main causes: less useful work on the same labor (v12 turns its hours into more care, watering and
planting), and weaker denial (elites earn more on strawberries, wool and wheat when it plays). Not a submission candidate.

## Rejected today
- counter-tomato: V219 gate extended to rivals growing >= 4-8 tomatoes: same 57-30, margin -$1.6k/game.
