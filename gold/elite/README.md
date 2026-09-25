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
`eval_repaired_own.py` on the adaptive teams in their own towns vs v100 (786 seats, `repaired_own_vs_v100.jsonl`):

| team | seats | robust | ratio | wins vs v100 | margin |
|---|---:|---:|---:|---:|---:|
| DSM | 166 | 84% | 0.98 | 86% | +$7,536 |
| M & M & P & Q | 55 | 82% | 0.97 | 76% | +$4,956 |
| Unknown Mother-Goose | 93 | 80% | 0.97 | 73% | +$4,714 |
| Majkel1337 | 158 | 92% | 1.01 | 66% | +$2,071 |
| Vadim Vasilenko | 23 | 78% | 0.94 | 61% | +$580 |
| QQ | 91 | 92% | 1.01 | 59% | +$1,618 |
| THIRD FARM CLUB | 152 | 86% | 0.98 | 49% | -$952 |
| Orbital Terraformer | 48 | 85% | 0.98 | 44% | -$949 |
| all | 786 | | 0.99 | 66% | +$2,875 |

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

## 6. What the elite winners grow, by demand known at the time (`composition_table.txt`)

Demand = daily units the shops known at day D drain for the product (6 per multi-product shop, 12 per single-product
shop; day 12 knows 4 shops, day 18 six, day 24 eight). Elite winners (639 seats) / our live seats (131):

| product, day | demand 0 | 6 | 12 | 18 | 24 |
|---|---:|---:|---:|---:|---:|
| tomato tiles, day 18 | 2.9 / 0.0 | 5.5 / 0.0 | 7.2 / 0.0 | 11.3 / 5.3 | 18.8 / 6.0 |
| strawberry tiles, day 12 | 15.2 / 33 | 20.2 / 33 | 26.1 / 33 | 31.8 / 33 | 38.2 / 33 |
| carrot tiles, day 24 | 2.0 / 0.0 | 2.4 / 0.0 | 8.0 / 3.3 | 9.6 / 4.6 | 17.1 / 9.6 |
| cows, day 12 | 5.0 / 6.0 | 7.1 / 6.6 | 9.5 / 7.5 | 12.0 / 9.4 | 14.6 / 12.0 |
| sheep, day 12 (demand 0/12/24) | 3.2 / 5.7 | | 8.5 / 9.4 | | 15.6 / 16.6 |

Elite cash rises with tomato demand known at day 12 ($110.7k at 0, $115.9k at 18). The tape plants 33 strawberries
in every town; 26% of towns have strawberry demand 0-6 at day 12, where the winners hold 15-20. Day 6: winners
already have 9.2 strawberries (ours 4.3). Winners hold 25 locked tiles at day 24 (three quadrants); we buy the
fourth in a fifth of games.

## 7. Rejected: idle fertilizer collection on chassis days (`fert_idle`, off)

A unit whose scripted action is PASS while standing on an animal tile with fertilizer available collects it (no
move, so the route stays in lockstep). Fires 29-50 times a game and changes final cash by exactly $0 on seeds
6003/6011/6042: `fertilizer_available` resets daily and the route already collects those animals later, so the
scripted collect becomes the no-op. The 48 extra units the 2800+ copies sell come from animals the tape never
visits, which a position-safe layer cannot reach.

## 8. Gates for the 2800+ population

- `gold/harness/pinned4.py moon/strong2800.json,moon/strong_new.json 288 cand1,cand2 out.jsonl offhand`: the 179
  recorded games vs 2800+ rivals (61 copies, 55 elites, 15 near in the first file), our prefix to step 288.
- `gold/elite/elite_gate.py build|run`: a candidate vs repaired elite recordings in their own towns (7 teams x 30
  seats cached in `elite_gate_refs.jsonl`).
- `gold/harness/batch4.py cand arena/cand/omw_v15a.py 6000-6059 out.jsonl 0`: closed-loop mirror.

## 9. Rejected: earlier controller takeovers against elites (elite gate, 210 seats, paired vs v108)

v108 on the elite gate: 60-150 (29%), -$3,204 (DSM -$6.2k, Yannik -$5.2k, M & M & P & Q -$3.8k, UMG -$3.7k).

| candidate | change | paired delta | flips |
|---|---|---:|---|
| e1 | takeover at day 12 everywhere | -$1,694 +- 190 | 0/-13 |
| e2 | e1 + tomato allowance 20/day to day 20 | identical to e1 | |
| e5 | day-12 takeover when tomato demand >= 12 among the first four shops (`rich_tom_dem`) | -$660 +- 154 | 0/-6 |
| e6 | the same at demand >= 6 | -$1,624 +- 185 | 0/-12 |

The controller's execution from day 12 costs more than any production package it plants, even in tomato towns
against elites. The production-mix gap in section 1 cannot be closed by handing the farm to the controller earlier.

## 10. Takeover timing against elites, and an earlier SE tomato block (elite gate, paired vs v108)

| candidate | change | paired delta | flips |
|---|---|---:|---|
| e9 | divergent takeover at day 20 (`start_div` 480) instead of 16 | +$474 +- 153 | +6/-5 |
| e10 | divergent takeover at day 24 | -$14 +- 185 | +6/-8 |

`base_m7_t4.py` makes the chassis's SE tomato block (V219) planting day, shop minimum, cash floor and price floor
variables; `v219e` in the controller sets them at day 12 by tomato demand. Mirror seeds (vs omw_v15a):
- day-13 block, 20 plants (seed 6042, tomato demand 18): sold 247 tomatoes at $97-220 vs v108's day-18 block's 133
  at $238-429; cash $10k lower by day 18 (land, seeds, and 3-4 extra hires a day at Fibonacci wages on top of the
  tape's roster); our own ADAPT then misread the copy rival as divergent (the block lands before the day-15 check).
  -$11.2k; day-15 block -$11.6k (seed 6042), -$11.0k (6046). The late block's hinge prices are the whole value of
  V219 in copy games; an earlier block trades them for volume and wages. Not pursued.
