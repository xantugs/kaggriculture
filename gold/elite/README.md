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
| v137 with the divergent takeover at day 14 (e47) | +$129 +- 172 | | | +6/-8 |
| v137 with the divergent takeover at day 13 (e48) | -$57 +- 176 | | | +5/-8 |

| v137 with a 1-day rival forecast window (e49) | +$657 +- 135 | | | +6/-6 |
| v137 with a 3-day rival forecast window (e50) | +$989 +- 130 | | | +8/-2 |

The programme does not make an earlier hand-over pay: day 16 stays. The rival's pattern over the last 2 days is
the best forecast window (1 day is too noisy, 3 days too stale).

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
a day-29 watering. Both lose on the pinned 2800+ gate (200 rows, paired vs v136): e45 -$264 +- 123 (copies -$554,
flips 0/-7), e46 -$821 +- 126 (flips 0/-10). The controller's tuned endgame (carrots to day 26, harvest-all on
day 28, cheap last-day labour) beats a horizon-exact crop rule that leaves more to the expensive final day; what the
copy earns on day 29 it pays for in hands and in the day-29 carrot dump. The copy-game close losses stay open.

## Bottom line (26 Sep, evening)

v137 = v136 + the market programme on divergent games. Against elite routes it is the first change since v108 that
moves the gate beyond noise (+$1,155 +- 132, 59 -> 67 wins of 210, no seat lost); on the live 2800+ population it
adds $644 +- 270 on divergent games and nothing on copies (identical play, verified closed-loop). It does not flip
many live games yet because the divergent losses are large. Tried and rejected on the way: rival weight 0-3 (1.5),
tomatoes in the programme, holding caps 8/20, room_v3, room 80/100, an earlier divergent takeover, a horizon-exact
late planting rule. Open: `mkt_dp_every` (+3 wins on the gate at 80 extra programme runs a game), the programme on
copy games (+$108 +- 126 pinned), and a chassis-days programme, which is not worth building: before day 16 the
chassis sells only ~70 premium units a game in divergent towns (`fills_ana.py`), a tenth of what the controller
sells afterwards.

## 16. Engine mechanics mined for money (26 Sep, evening)

Read straight from kaggriculture.py 1.32.7:

- **Market settlement**: the two players' order lists are processed index by index; within an index, unit by unit
  in lockstep, both quoted at the same pre-commit inventory. A lot at a later index than the rival's same-product
  lot settles after their whole lot. Buys of wheat/fertilizer are quoted at the post-buy inventory, so a buy/sell
  round trip nets zero. The town drains after the market of steps 0 mod 4; sales at $1 add no supply.
- **Growth**: a one-time crop is planted with 1 unit and gains 1 (2 fertilized) per WATER on a day in its window,
  immediately; ongoing crops gain 1 (2 if fertilized and watered) at the end of production days regardless of
  watering. Two consecutive unwatered days kill a plant (the planting day counts as unwatered: water on day 0).
  Animals produce at the end of production days regardless of feeding (the care bonus needs feeding); two unfed
  days and they escape. The controller already feeds and waters by these rules.
- **Hands** vanish every night; the n-th hire of a day costs fib(n) dollars (1, 1, 2, 3, 5, 8, 13, 21, 34, 55,
  89, 144, 233, ...). Hands spawn at the shed at hour 1; the farmer respawns at (4, 4).
- **Thin markets** (units over 10,000 to the $1 floor): strawberry 75, milk 80, wool 60, melon 160; fertilizer
  495 (no shop buys it, linear, $0.20 a unit); eggs never crash (log, floor about $37).

**Tick-window lead** (`lead2`, ctl.py): sell every premium lot the tape plans inside the current tick window now,
ahead of a copy's own one-step lead. Inert: 2 units in 300 closed-loop steps, none in a pinned copy game; the
tape's premium lots are dropped at the step they are sold. The copy tie prize would have been $1,257 a game
(`pin_fills`, chassis days), so ties are decided by harvest logistics, not by the order list.

**Copy forecast from the tape** (`mkt_dp_copy_plan`): the copy's planned sales from our own route, its lead
applied, capped by the ripe units on its farm. Matches only 13-33% of its observed sale steps (copies run other
versions and layers), so it stays off.

**The melon race**: melons have no shop, the town centre takes one a day, and the price is 250 - 900 (x/300)^2:
the first wave (day 10, 72 units from our 12 tiles vs the elites' ~80) is a one-shot pool of about $26k shared by
lockstep. Simulated against the elites' recorded melon sales (672 seats): selling our 72 by hour 8 instead of
hours 9-15 is +$3.5k margin, but delivery physics (hands spawn at the shed at hour 1, melon tiles are 3-5 steps
away, water then harvest) already put the tape at the frontier (+$1k at best). Supply is the lever: 4 more tiles
delivered on second trips are +$4.7k margin vs elites and +$2.5k vs copies, 8 tiles +$8k / +$3.5k, and the route
has no room for them: day 0 spends the $3,000 on 2 cows, 2 sheep, 12 melons, 7 wheat and 5 hires, and NW's 24
tiles are full from day 1; displacing the animals or the early wheat nets out negative. After day 11 nobody sells
melons in copy games and the price crawls from $76 to $120 (one unit a day), but the room to the floor is only
30-40 units, so a second wave is worth $2-3k gross for 5-6 tiles: strawberries beat it.

**Programme on copy games with step-level decisions** (e52, pinned, 102 games so far): +$299 +- 184 on copies
(0/-1 flips; one strawberry-rich copy game loses $4.5k when holds hand the copy the day-27 book), +$357 +- 119 on
divergent games over v137. Step-level decisions go into the divergent build (e54/e55, elite gate running); the
copy-game programme stays off.

**Land**: the top elite teams buy SW on day 8-9 and SE on day 8-9 (DSM 77% of seats, Unknown Mother-Goose 89%,
M & M & P & Q 98%, Yannik Schiffner 70%; QQ and Sida Zuo never), with the same 10-12 hires a day as us; our route
buys SW on day 11 and SE only as a strawberry/tomato/herd annex (16% of gate seats, day 12+). The products they
beat us on (wheat, carrots, tomatoes) are the ones whose markets take volume. `se_force_day` (ctl.py) buys SE as
plain land at the first day plan on or after that day; e56 (day 16) and e57 (day 20) on the elite gate measure
whether the controller turns 25 tiles for $4,000 into money with its own crop choice. It does not: e56 -$1,168
+- 182 (67 -> 46 wins), e57 -$1,662 +- 174. With SE the controller hires fewer hands (9.7 a day against 10.9),
leaves the far tiles unserved rather than pay the 11th-13th hand ($89-$233 a day), and the land idles. The
elites' SE works because it is in their plan from day 8-9 with 20 days to pay for it and labour-light crops; a
controller that farms 100 tiles with 11 hands is a different planner, not a knob. With the planting footprint raised
too (`se_force_fp`, e58: the land is planted), the 161 seats that buy it plant 35 more plots, hire 35 more hands
(the 12th-14th of the day), earn +$5.7k of wheat and pay $6.5k of wages plus the $4,000: -$5.5k a seat, -$3,005 +-
352 over the gate, 70 -> 48 wins. e59 (max_hands 15, hire weight 0.4) is no better. The Fibonacci wage, not
labour efficiency, is the wall: elites and our controller spend unit-turns the same way (42% walking, 17%
watering, 10% harvesting, 278 vs 255 turns a day); they simply run 100 tiles on the hands we run 75 with.

**Gate fidelity**: the repaired elite replays score a median 0.99 of their recorded games; 55 of 210 seats are
below 0.95 and 24 below 0.90 (a recorded land purchase can fail on the replayed cash path: DSM 111016709 seat 1
loses its SE). We win 30% of the intact seats and 38% of the weakened ones, so the gate overstates us slightly.

**Determinism**: two builds of the same effective configuration differ on 20 of 210 seats when the programme's keys
sit in `div_over` instead of the top level: `div_over` is applied only once ADAPT flags the rival (step 143 or
359), so a rich-town day-12 takeover runs without the programme until then. v138 puts the keys at the top level
(e42's placement: +$1,200 / 70 wins vs e54's +$1,072 / 67 wins on the same seats).

## v138 (`submit/main_ctl_rich9_m7.py`, `cfg/cfg_v138.json`)

v137 with the programme on every rival and step-level decisions before a forecast rival sale of at least 3 units
(`mkt_dp_every`, `mkt_dp_every_min`), keys at the top level. Elite gate: +$1,234 +- 141 paired vs v136, 59 -> 70
wins, flips +12/-1, worst step 0.47 s, no errors. Pinned 2800+ (149 paired): +$535 +- 131 vs v136 (divergent
+$1,014 +- 248, copies +$213 +- 132, flips +4/-3, wins 95 -> 96); +$276 +- 93 vs v137.

## m3 (`submit/main_ctl_mkt3_m7.py`, `cfg/cfg_m3.json`) = their v147 + the market programme (26 Sep, merged)

Their v147 (v136 + chassis unit floor + divergent melons through day 19) is neutral on the elite gate (-$123 +- 75,
59 wins) and +$182 +- 100 pinned (95 wins). Adding the programme (m2's keys, top level): elite gate +$1,266 +- 149
vs v136, wins 59 -> 72 (+15/-2); pinned 2800+ +$791 +- 151 vs v136, wins 95 -> 102 (copies 75 -> 80, divergent
20 -> 22, flips +8/-1); +$609 +- 136 vs v147 (95 -> 102); +$256 +- 90 vs m2 (96 -> 102). Worst step 0.47 s.
The two lines add: theirs lifts copies, the programme lifts divergent games and the copies' controller days.

## 17. The tape's strawberries: a flood weapon, and towns where it misfires (26-27 Sep)

Per-tile labour is the same as the elites' (they water and harvest more per plant than we do); the crop mix differs:
in days 16-28 they run ~23 wheat, 9 tomato and 16 strawberry tiles to our 19 / 5 / 25, on the same ~72 tiles in
use. Our 25 strawberry tiles are the tape's own 33 plants (days 5-11: 4, 8, 4, 4, 13), planted whatever the town.
The strawberry price floors 75 units over and the drain is 6 a day per strawberry shop, so two farms of 30 plants
floor it within days.

**Rival classification on day 0**: a chassis copy runs the same opening and holds $1,000-1,070 at step 2 (`div2_band`);
the seven elite teams hold 12-1,571 (584-588, 647, 736, 1,085, 1,569-1,571, 12-22); one near-copy classed divergent
by ADAPT held 1,041 (missed, harmless). 50 of 60 divergent pinned games and 0 of 89 copies are flagged with the
wide band (6 copies with the narrow one, and one of them, a $1,008 opening, cost $32k when the conversion fired).

**Conversion** (`s2t_days`, `s2t_crop`, `s2t_max_shops`, `s2t_by_town`): against a flagged rival, the tape's PLANT
STRAWBERRY and strawberry seed purchases on the given days become another crop. Unconditional (e60, days 8+11 to
tomatoes): our cash +$2.4k but the elite's +$5.6k, its strawberry revenue +$7.1k: -$3.3k. Against a strawberry-heavy
elite our flood is worth more to us than the tiles are: on Majkel1337's seat 111017922 the swap raised our cash $6.8k
and the elite's strawberries from $12k to $27k. The split is the town's shops: 0 strawberry-buying shops among the
first 3 (known by day 9): +$6.7k +- 1.2k, 3 -> 10 wins of 17; 2 or more: -$5k to -$9k. m3 itself is -$7.6k with 5
wins of 36 against strawberry-light elites, which are exactly the strawberry-poor towns. The rival's own strawberry
count by day 11 does not separate the cases.

| variant (vs m3, elite gate) | margin | wins |
|---|---:|---:|
| e63 days 8+11, no strawberry shop known that day, crop by town | +$405 +- 151 | 72 -> 75 |
| e64 same, always tomatoes | **+$659 +- 169** | **72 -> 80** (+10/-2) |
| e65 one strawberry shop allowed | -$711 +- 435 | 68 |
| e66 days 6-8 + 11 (crop by town) | -$519 +- 317 | 69 |
| e67 day 11 only (crop by town) | +$377 +- 114 | 76 |

Tomatoes beat carrots and wheat as the replacement even without a tomato shop (the hinge keeps them scarce).
Pinned 2800+ from day 6 (S = 144, both farms replayed to day 6, rival tape pinned): e63 vs m3 divergent +$1,105
+- 418 (z 2.6), 22 -> 24 wins; 14 of the 73 live divergent games are 0-shop towns by day 9.

**m4** (`submit/main_ctl_mkt4_m7.py`, `cfg/cfg_m4.json`) = m3 + the e64 conversion with two safeguards: the step-2 cash
band widened to $1,000-1,070 (a $1,008 copy converted 4 plants and lost $32k: the chassis's day-16 tomato block went
untended), and `s2t_max_sim` 0.97: a copy's farm equals ours tile for tile through day 11 (1.00 in every recorded copy
game, the odd-opening ones included), the elites' sits at 0.74-0.86 on day 8. Elite gate: identical to e64 (+$1,925
+- 241 vs v136, 59 -> 80 wins, flips +25/-4; +$659 +- 169 vs m3). Pinned 2800+ from day 6: +$487 +- 169 vs m3
(z 2.9), wins 100 -> 103 (+3/-0), divergent +$1,209 +- 405, copies untouched; 23 of 60 divergent games convert.
Converting more batches loses: days 6-8 + 11 (e68) +$143, day 5 on (e70) -$861, day 11 alone (e69) +$456 / 77 wins.
**m5** = v149 (their chassis floor 8%) + the m4 additions: elite gate +$1,911 +- 242 vs v136 (80 wins); day-6 pinned
vs v149 +$952 +- 219 (z 4.3), wins 96 -> 101, divergent +$2,057 +- 471; vs m4 -$13 +- 40 (103 -> 101 wins):
the floor step from 3% to 8% is invisible on the pinned gate. m4 stays the primary; m5 is the same agent for anyone
who prefers their closed-loop judgement of copy games.

## 18. The early-game planner, tried the cheap way (27 Sep)

`start_div2` hands the farm to the controller at day 6 against a step-2-flagged rival (the tape keeps the opening:
melons, cows, sheep). With the elite land schedule (SW day 9, SE day 11, footprint +25) and optional planting the
controller loses $15-18k a seat (e71 smoke: unserved value $4.5k, ten hires a day, land bought, nothing tended in
time); the same at day 12 with SE (e75) -$6-14k; SE at day 16 with optional planting and the full wage weight (e74)
still triples the hire bill (+$7k of wheat for +$7k of wages plus the land). A bug found on the way: an ADAPT flag at
step 359 used to reset the takeover to day 16 after a day-6 hand-over, so the tape resumed on a farm it did not
recognise (fixed with a min). Verdict: this controller cannot run 100 tiles; its routing over far tiles hires the
12th-14th hands and leaves the work unserved. The elite early game needs a planner written for it, not a takeover.
**Copies too?** e78 converts against every rival: copies -$756 +- 397 (78 -> 72 wins, flips +1/-7) with two
collapses (-$14k, -$32k: our day-16 tomato block goes untended once early tomatoes sit on the farm, hires drop
from 75 to 54). The conversion stays divergent-only. Tomatoes in the market programme (e77): +$58 +- 36, 80 -> 77
wins, not adopted. Delivery timing measured (16 elite seats, days 16-28): elites drop 56% of premium units at the
night boundary, we drop 75% (27 of 36 a day); on the first day of a rival's strawberries the programme held our
8 strawberries, 8 milk and 12 wool from hour 1 to hour 23 for want of a rival pattern (DSM sold 36 that day).

**Delivery and forecast variants on m4 (elite gate)**: farm-based rival forecast (e81, the ripe units on its tiles
count as sales over the next 8 hours) -$597 +- 130 (66 wins); courier from hour 6 at room 40 (e80) -$805 +- 162
(65); both (e82) -$1,392; shed stops down to an end-of-day room of 30 (e79) -$5,363 (32 wins: labour). Selling
fresh harvests the same day is worth less than the turns it costs, and the programme's holds beat a forecast that
sells into the rival's day. The night drop stays.

## 19. The opening rebuilt by the controller, and what the elite gate says about it (27 Sep)

`GC_P["open"]` (ctl.py) lets the controller play the early game from step 0, or from a takeover day, on a schedule:
land days, cumulative animal targets, strawberry targets by the demand known (DSM's 8 plots on days 2-4, 12 in NE on
day 6, SW on day 9), cash kept for the next morning's hires and feed, an evening feed purchase, urgent sales (no market
holds) while a scheduled purchase is unfunded, mid-day purchases the moment the day's sales pay for them with incremental
re-routing (new hands when they pay), premium loads delivered the same day (`deliver_prem`: the trip is reserved in the
route cost, the stop lands right after the premium visits, which go first), melon window waters as must visits, hands the
plan gives nothing to not hired. Tools: `harness/open_trace.py` (closed-loop per-day table of both farms),
`elite/day_sched.py` (per-day schedule of a candidate and a repaired elite in its town). m4 (`open=None`) is unchanged.

| elite gate, 210 seats | margin | wins | our cash vs m4 | elite cash vs m4 |
|---|---:|---:|---:|---:|
| m4 | -$1,315 | 80 | | |
| o1: schedule from day 0, the tape's herd | -$27,306 | 3 | -$2,278 | +$23,712 |
| o2: schedule from day 0, DSM's early strawberries, cows from day 6 | -$29,258 | 3 | -$3,933 | +$24,009 |
| o4c: the tape to day 5, the schedule from day 6 | -$18,398 | 6 | -$4,792 | +$12,290 |

Our own cash is within $2-5k of the tape's (hires +60 a game, tomatoes, melons a day late before the delivery fix); the
margin is lost on the **elite's** side: it earns $12-24k more when our milk, wool and strawberries arrive later or in
smaller volume (o1: elite strawberry +$10.7k, milk +$6.6k, wool +$4.2k). The tape's early herd and its strawberry
batches floor the thin markets before the elite's recorded sales; the controller-run opening does not, and its own
gains never cover that. Verdict: the tape's days 0-11 stay.

**Early strawberries on the tape** (`es_days`, ctl.py): the tape's day 2-4 wheat replants in NW become strawberries
(7 tiles), the seeds bought on top of the wheat seeds, the day 2-3 cow purchases dropped to pay ($800); the tape keeps
watering the tiles and harvests them on its wheat cadence (4 units a plant, unfertilized, sold from day 14). e83:
-$9,958 +- 504 (72 -> 13 wins, flips +1/-60): our cash unchanged (+$67: strawberry -$156, fertilizer -$2.0k, eggs
-$0.7k, wheat +$1.6k), the elite +$10.0k, of it **milk +$9.9k**: two cows fewer on days 2-3 lift the elite's milk price for
the whole game. e84 (the day-7 cows dropped too) -$11,350. Two early cows are worth $10k of denial; seven early
strawberry plots earn nothing extra for us. Denial-weighted herd purchases on controller days (`herd_denial_w` 1.0,
e88/e89): +$0 / +$13 (the late herd rarely fires). Elite revenue by product in the m4 gate: strawberry $32.4k, wool
$20.4k, milk $19.0k, melon $12.5k, fertilizer $11.5k, wheat $10.6k, carrot $6.2k, tomato $5.3k, egg $4.8k; ours:
strawberry $29.3k, milk $20.4k, wool $20.4k, melon $17.6k, fertilizer $13.0k, wheat $7.5k.

**Cows bought back** (`es_cow_days`: the skipped cows re-bought on days 7-10 when the cash is there, carried by the tape's
own cow pickups and placed on its empty pastures by no-op visits): e90 -$16,535 (elite milk +$11.9k; only one cow comes
back, the cash is not there before day 8-10); one cow skipped on day 3 and four early strawberries (e91): -$6,530
(elite milk +$6.3k). The day 2-3 cows are what floors the milk market for the game; nothing bought later replaces them.

**Same-day premium delivery on controller days** (`deliver_prem`, the opening's delivery rule applied from the takeover):
800 (e92) -$1,766 +- 179 (hires -$2.0k), 1500 with weight 0.2 (e93) -$196 +- 128 (strawberry +$170 for us, -$278
for the elite, hires -$560). The night drop stays. **Footprint**: slack 8 (e94) -$72 +- 129 (wheat +$706, hires -$676);
off (e95) -$1,099 +- 215 (wheat +$1.2k, hires -$1.7k). More plots after the takeover buy wheat at the 12th-14th hand's wage.

**Where m4 loses** (m4 gate): 78 of the 130 losses are by more than $5k, only 14 within $2k. In the big losses the elite
out-earns us on strawberry +$6.0k, wheat +$4.2k, carrot +$2.6k, wool +$2.2k, tomato +$1.0k (melon -$5.4k, fertilizer
-$1.5k); the elite's strawberry revenue is $32k in every group (it sells first, at $190), ours is $26k in the big losses
and $33k in the wins. Wheat is a log market: the elite's +$3-4k there is volume we never grow (its SW day 9), not denial.

