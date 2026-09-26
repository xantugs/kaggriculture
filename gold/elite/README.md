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
| e11 | `hire_cost_w` 0.3 (cheaper hiring in controller days) | -$104 +- 71 | +3/-5 |
| e12 | e11 + 18 hands | -$239 +- 90 | +3/-6 |
| e16 | strawberry annex check at 2 shops (`rich_min` 2, forecast-gated) | never fires differently (0 games changed) | |
| e17 | herd margins 2000 / 3000 | +$19 +- 35 (5 games changed) | +1/-1 |
| e18 | e9 + e16 + e17 | +$493 +- 154 | +7/-5 |
| e19 | divergent takeover day 18 | +$152 +- 145 | +6/-6 |
| e20 | divergent takeover day 22 | +$39 +- 169 | +3/-7 |

e9 on the pinned 2800+ gate: divergent games +$24 +- 385 (flips +1/-3), copies unchanged by construction. The
takeover-day curve against elites (16: 0, 18: +152, 20: +474, 22: +39, 24: -14) is a marginal effect at best.

## 11. Rejected: strawberry planting cap (`straw_cap`), and what it taught

Chassis days: from day 6, PLANT STRAWBERRY beyond a demand-keyed cap (18 at demand 0, 22 at demand 6) becomes PASS
and further strawberry seed orders are dropped; positions are untouched. Mirror seeds: our cash +$0.7-1.8k where it
fires, but the copy rival gains $1-10k because it keeps flooding the market we just vacated. Elite gate (128 seats
before the run died of memory pressure, 57 fired): paired -$1,633 +- 787 in fired games, wins 3 vs 12; we gain
$1,386, the elite gains $3,019 (DSM -$1.8k, Majkel1337 -$3.2k, UMG -$5.0k; only Sida Zuo/Yannik positive).

The 33-tile strawberry flood is denial, not waste: the strawberry book is the shallowest in the game (100 units move
the price by 160% of base), so whoever floods it destroys the rival's strawberry revenue. Elite winners hold 15-20
tiles in poor towns because their rivals are elites who do not flood; against a flooding rival the best response is
to flood back and sell first. The same logic protects our wool and milk positions. Do not cut supply in shallow
markets.

## 12. Rejected: SE tomato block at day 15 against ADAPT-divergent rivals only (`v219e` + `div_only`, e23)

Elite gate, paired vs v108: -$161 +- 106 overall; in the 25 games where it fired -$1,352 +- 851 (us -$2,440, the
elite -$1,089). Per product in those games: our tomatoes +$1,064, and the controller later grew wheat +$2,217 and
carrots +$2,261 on the SE tiles; the elite's tomatoes -$880 (denial works); but wages -$3,921, seeds -$855 and the
$4,000 quadrant outweigh it. Hands hired on top of the tape's roster cost fib(11..14) = $89-377 a day each.

## 13. Where v108 loses against elite routes in their own towns (210 seats, ledger delta us - elite)

wheat -$3,582, strawberry -$2,915, tomato -$1,840, carrot -$1,514, wool -$381, egg -$376;
melon +$4,855, fertilizer +$1,498, milk +$1,243, hires +$1,099 (we spend less).

## Bottom line (26 Sep)

Fifteen candidates against v108 on the elite gate, paired on identical seats: none beats it beyond noise. The
controller matches the tape from day 16 but is far weaker before; every earlier hand-over loses. Extra labour on top
of the tape's roster is priced out by the Fibonacci wage. Cutting supply in a shallow market hands revenue to the
rival. What remains is the tape's fixed days 0-16 (the elites' early wheat, tomatoes on existing tiles, geese), which
cannot be tuned from outside the route. v108 is at the frontier of the chassis-plus-controller design against elites.

## 14. The market as the optimization target (26 Sep)

**Oracle** (`market_oracle.py`): replay pinned 2800+ games with v108, record our arrivals, the rival's sales and
the inventory path, and solve the optimal sell schedule per product by dynamic programming on the exact price curve
(12 games, from day 12). Perfect foresight, 10 units held per product: +$5,086 a game (strawberry +$1.7k, milk
+$2.3k, wool +$2.6k; wheat/fertilizer 0). A plan from the rival's previous-day pattern, evaluated on the true path,
still gains $4.8k on those three goods. Our realized prices trail an optimal schedule by that much.

**Policy** (`mkt_dp` in `ctl.py`): in controller days, for strawberry/milk/wool, after every town drain tick a
dynamic programme over the next 6 post-tick turns chooses how many units to sell now: exogenous inventory = now -
town draws (exact schedule) + the rival's forecast sales (its hourly pattern over the last 2 days); tonight's carried
units arrive at the day boundary; at most `mkt_dp_cap` (12) units held; the rival's forecast sales in each period are
charged at the book our decision leaves, weighted `mkt_dp_rival_w`. 3 s a game, worst step 0.4 s.

Elite gate (210 seats, paired vs v136, controller from day 16):

| variant | paired margin | our cash | elite cash | flips |
|---|---:|---:|---:|---|
| w = 0 (revenue only) | -$530 +- 150 | +$1,689 | +$2,219 | +4/-11 |
| w = 0.5 | +$12 +- 145 | +$1,793 | +$1,782 | +9/-7 |
| w = 1 (e24) | **+$433 +- 139** | +$1,706 | +$1,273 | +9/-7 |
| w = 1, 12 periods (e27) | +$425 +- 139 | | | +9/-7 |
| w = 1.5 (e29) | +$562 +- 128 | +$1,512 | +$950 | +10/-2 |
| w = 2 (e30) | +$587 +- 130 | +$1,328 | +$741 | +12/-6 |
| w = 3 (e31) | +$572 +- 129 | +$1,079 | +$507 | +10/-8 |
| w = 1 + tomatoes (e32) | +$406 +- 139 | | | +9/-7 |
| w = 1, cap 20 (e33) | +$110 +- 159 | | | +7/-7 |
| **w = 1.5, night room cap 90 (e35)** | **+$1,155 +- 132** | +$1,954 | +$799 | **+8/-0** |
| e35 + room_v3 (e36) | +$902 +- 139 | +$1,652 | +$750 | +7/-3 |
| room_v3 alone (e34) | +$496 +- 161 (142 seats) | | | +6/-4 |
| w = 1.5, cap 8 (e37) | +$524 +- 127 | | | +8/-6 |
| w = 1.5, cap 8, room 90 (e38) | +$839 +- 132 | | | +8/-7 |
| w = 1.5, room 80 (e40) | +$1,114 +- 137 | +$1,954 | +$840 | +8/-1 |
| w = 1.5, room 100 (e41) | +$813 +- 126 | +$1,652 | +$839 | +8/-1 |
| e35 + decisions before a forecast rival sale (e42, `mkt_dp_every`) | +$1,200 +- 141 | +$1,868 | +$669 | +12/-1 |
| w = 2, room 90 (e43) | +$1,032 +- 136 | +$1,703 | +$671 | +7/-1 |
| w = 2.5, room 90 (e44) | +$999 +- 136 | +$1,537 | +$538 | +10/-1 |

`mkt_dp_every` (sell ahead of the rival's forecast hour, not only after a tick) wins 70 seats to e35's 67 at the
same margin, at 80 extra programme runs a game (worst step 0.48 s here against 0.27 s; the engine's actTimeout is
1 s with a 60 s overage bank), so v137 stays with post-tick decisions; e42 is the next step if the budget allows.

Holding lifts the rival's prices too (the denial cost); charging the rival's sales at the book we leave is what
turns revenue into margin. The weight plateaus from 1.5. Tomatoes add nothing; a larger holding cap loses most of
the gain. Mirror seeds (copy rival, controller only from day 24): our cash +$400-460 but margin -$435, so the
policy is for divergent games (`e28`: mkt_dp in `div_over` only).

**The night** (`mkt_dp_room`): the day plan carries up to `eod_room` (88) units into the night on purpose, so the
shed is full every evening and lots the programme held across the boundary were dumped by the hour-20 room
release (`gc_held_released`) or crowded out wheat and fertilizer (`gc_room_sells`); on big elite farms it also
raised the planned overflow. The programme now caps the units it may hold across the day boundary at
`mkt_dp_room` (90) minus tonight's load (reserves kept, goods each unit still carries after its last queued drop);
within the day the cap stays `mkt_dp_cap`. That doubles the gain (e35, +$1,155, no seat flips down); reserving
night room in the plan instead (`room_v3`, more shed stops) is worse (e36, e34).

Pinned 2800+ live games (149 paired, S = 288, `pair_ana.py`): without the night cap, mkt_dp on all rivals (e27)
costs $226 +- 126 on copies and gains $156 +- 295 on divergent rivals; the divergent-only build (e28) is
+$221 +- 283 on divergent games. With the night cap (`pinned2800_mktdp_room.jsonl`): e35 on all rivals is
+$660 +- 278 on divergent games (z 2.4) and +$108 +- 126 on copies (flips +2/-2); the divergent-only build e39
(= **v137**, `submit/main_ctl_rich8_m7.py`, `cfg/cfg_v137.json`) is +$644 +- 270 on divergent games, copies
identical, 95 -> 95 wins overall (+1/-1). The margin moves; the wins barely do, because 36 of the 50 divergent
losses are by more than $5k (`fills_ana.py`, `pin_fills_v136.jsonl`) and only 5 are within $2k. Copy losses are
the opposite: 14 of 16 within $2k.

## 15. The copy games' last two days (26 Sep, `fills_ana.py` on `pin_fills_v136.jsonl`)

Pinned 2800+ population, v136, per game and day, our sales minus the rival's. Copy games (106, 90 wins, +$5,085):
days 22-27 are ours (+$1,140, +$902, +$234, +$1,707, +$743, +$4,395), days 28-29 are the copy's (-$330, -$1,119).
On day 29 the copy sells 83.5 carrots and 60.5 wheat a game to our 49.7 and 32.2, at the same prices. The 16 copy
losses are close (14 within $2k); the divergent losses are not (36 of 50 beyond $5k). The wheat units gap over days
16-29 (335 vs 735 sold) is a round trip: the copy buys 461 wheat a game for feed and sells its harvest, we keep
harvested wheat as the feed reserve; net wheat revenue is equal.

Engine facts for the endgame (kaggriculture.py): a one-time crop is planted with 1 yield unit; each WATER on a day
in its window (ages (max_yield_day+1)//2 .. max_yield_day) adds 2 units fertilized, 1 not, capped at max_yield,
immediately; HARVEST needs age >= first_yield_day and units > 0. So a carrot planted on day 27 gives 3 units
(fertilized) on day 29 and wheat planted on day 26 gives 5; the controller's `carrot_last_plant` 26 and
`wheat_last_plant` 25 leave 28-44 tiles empty on days 28-29 (`farm_trace.py`, game 111749735).
`late_plan` (ctl.py, off by default): from day 24 plant wheat or carrots by their exact remaining growth to day 29,
whichever nets more after seed and fertilizer; `late_keep`: on day 28 keep any one-time crop that still gains from
a day-29 watering. Pinned 2800+ gate (e45/e46): see below.
