# gold/elite — the elite dump as a testbed (25 Sep 2026)

`moon/elite/games_2026-09-20.jsonl.gz` holds 639 elite-versus-elite ladder games (DSM 166, Majkel1337 158,
THIRD FARM CLUB 152, SpaTaro 101, Otter Vibe 93, Unknown Mother-Goose 93, QQ 91, ymg_aq 89, Sida Zuo 56,
M & M & P & Q 55, Yannik Schiffner 53, ...), full action streams and seeds. Every one of the 1,278 seats reproduces
exactly on the pinned 1.32.7 engine (`rec_ok`).

## 1. Where the rating is lost (live games vs 2800+ rivals, `moon/strong2800.json`, 131 games)

Split by action similarity to our own seat over the first 144 steps:

| rival type | games | W-L | median margin |
|---|---:|---:|---:|
| same route family (mirror) | 61 | 21-40 | -$467 |
| near-copies | 15 | 5-10 | -$1,031 |
| elite private agents | 55 | 5-50 | -$8,207 (24 losses over $10k) |

Ledger replay (`ledger_strong2800.jsonl`, `timing_strong2800.jsonl`) of the 55 elite games, revenue delta us-them:
tomato -$6,001 (77 units, 21 in days 18-23 and 55 in days 24-29 at $75-85), wheat -$5,521 (120 more units sold in
days 0-11 at $29-36), egg -$2,671 (1.3 more geese), strawberry -$1,662 (they sell early at $193 and stop; we sell
44 more units later into a crashed market from 8-9 extra tiles), carrot -$1,566, wool -$1,461; melon +$2,235 (our
day-10 dump). They hire 13.5 more hands, fertilize 73 more times, CARE 77 fewer times. Against the 61 mirrors:
uncollected fertilizer $1.4k (they COLLECT 9 more times, sell 48 more units), late tomatoes $1k at $154, the day
24-29 strawberry race (they sell first at $105, we follow at about $36), 45 more idle turns on our side.

## 2. Open-loop replay of elite routes (`eval_elite_routes.py`, `elite_vs_v100.jsonl`)

Each elite seat replayed verbatim as our agent (fresh weeds, recorded shop sequence pinned) against v100:

| team | robust (>= 90% of recorded cash) | robust replays: wins vs v100 | margin |
|---|---:|---:|---:|
| Sida Zuo | 89% | 80% | +$5,021 |
| Yannik Schiffner | 89% | 70% | +$4,134 |
| Otter Vibe | 95% | 67% | +$2,979 |
| THIRD FARM CLUB | 72% | 38% | -$3,045 |
| DSM / Majkel1337 / QQ / Unknown Mother-Goose | 2-10% | collapse | |

The collapses have one cause (`diag_collapse.py`, `diag_batch.py`): the adaptive elites spend to the last dollar on
day 0 and hire at day-1 hour 0 with "HIRE x8, keep what you can afford". A rival that also buys wheat at step 0 shifts
their fill prices by $3-7, the recording had $3-7 and got 2-4 hands, the transplant gets 0-1, and the farm is dead by
day 9. THIRD FARM CLUB fails the same way on a $100 strawberry seed at day 6 (the engine's atomic PLANT rule then
blocks the whole planting step).

## 3. Repair layer (`transplant.py`, `build_elite.py`), validated by ablation (`ablate_repairs2.log`)

Replay the recording's *successful* orders (from a hooked reference replay) instead of its requests; pad/truncate
hand actions to the live hand count; trim surplus PLANT requests to the seeds on hand; drop one unit of a feed-safe
seed late on day 0 only when the recording reached its day-1 hires with less than $20 to spare and live cash is
observed below the recorded trajectory. Emergency sells before purchases were destructive and are off.

Robust routes are unchanged (0.99 of recorded, identical to plain); collapsed routes go from 0.29 to 0.98.
`eval_repaired_own.py` on the adaptive teams in their own towns vs v100 (partial, 351 seats): DSM 81% wins +$6,842,
Unknown Mother-Goose 69% +$4,291, Majkel1337 69% +$2,068, QQ 63% +$2,199, M & M & P & Q 9/9 +$12,146,
THIRD FARM CLUB 55% -$185; overall 67%, +$3,148, mean ratio 0.98.

**This is an elite-strength gate**: a candidate can now be played against DSM's recorded play in DSM's town.

## 4. The route library is dead (`eval_prefix_matched.py`, `eval_hybrid_matched.py`)

A scripted elite route dropped into a *different* town that shares its first two shops loses to v100: 68/184, -$5,736
(the same routes win 71%, +$3,641 at home). Adding the takeover controller from day 12 on top (elite opening,
controller after) is worse: 50/184, -$7,206; takeovers at day 9 or 6 lose $20-45k to the route itself. The elites'
edge is adaptation to the whole shop sequence, not a transferable opening. Do not pursue route transplants.

## 5. Controller fix (`gold/ctl.py`)

`_route_and_hire` crashed the whole day (best = None) when the farm woke up with less cash than its minimum hand count
costs; never on the chassis, every day on a route that spends to the floor. It now falls back to fewer hands and
always evaluates the zero-hand plan. v100 rebuilt with the patched controller plays seeds 6000/6011/6042 identically.

## Tools

- `eval_elite_routes.py dump cand out [teams|ALL] [max]`: plain replay vs a candidate, own town.
- `eval_repaired_own.py dump cand out [teams] [max] [slack_min]` (`RESUME=1` appends): repaired replay, own town.
- `build_elite.py dump gid seat out.py`: one seat as a self-contained agent; `gold/build.py out '{...}' base` appends the controller.
- `hybrid_smoke.py`, `diag_collapse.py`, `diag_batch.py`, `diag_repaired.py`, `ablate_repairs.py`.
- `timing_anatomy.py games.json out`, `elite_ledger.py dump out [nproc]`, `composition_table.py elite.jsonl ours.jsonl`.
Built agents live in `gold/elite/bases/` (ignored; reproducible).
