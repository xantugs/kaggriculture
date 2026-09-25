# gold/ — takeover controller experiment (24 Sep 2026)

`ctl.py` is a full controller appended to the live chassis (`base_v15a_adapt.py` = uploaded v15a + ADAPT).
From `GC_P['start']` (hour 0 of a day) it owns every unit and the market:
- daily job valuation;
- hires chosen by marginal value against the Fibonacci wage;
- cheapest-insertion VRP routing (3 insertion orders + 2-opt);
- explicit shed-stop visits;
- dynamic feed/fertilizer reserves;
- final-day delivery;
- an optional market module (rival-aware sell timing, price floors).

Build: `python3 build.py out.py '{json overrides}'`. The current best closed-loop configuration is:

    {"start": 288, "max_hands": 15, "drop_slack": 0, "max_sell0": 0, "hire_cost_w": 0.6, "carrot_last_plant": 26,
     "final_water": false, "plant_must_last": 29, "prem_drop": false, "drip_on": false, "ovf_value": 100.0,
     "replant_done": true, "sell_timing": true, "sell_floor": {"STRAWBERRY": 30, "MILK": 25, "WOOL": 25}}

## Evaluation
- **Closed loop.** Against live v15a (`arena/cand/omw_v15a.py`), seeds 6000-6029, seat 0, decoupled engine:
  `harness/batch4.py`, then `harness/paired.py` for paired per-seed differences.
- **Pinned.** 249 recorded strong-team games, pinned at S=288:
  `harness/pinned4.py pin_all.json 288 candA,candB out.jsonl`, then `harness/pair_ana.py` (copy / divergent / opp≥2800 split).
  The baseline is `arena/cand/omw_adapt_up.py` (chassis+ADAPT), whose rows are in `pin288_v6.jsonl`.

## Progress on 24 Sep (closed loop, controller minus chassis, day-12 takeover)
| version | change | paired gain | margin vs chassis |
|---|---|---|---|
| v26z | start of the day | | -$9.4k |
| v28a | `_choose_crops`: a negative `wheat_now` made `feed_first` plant wheat on carrot/replant slots (and useless wheat on day 28) | +$503 ± 130 | -$8.9k |
| v30a | shed stops as route visits with repair (move later visits to other routes); hiring prices end-of-day overflow; re-ordering can no longer exceed a route's turn cap | +$2,407 ± 695 | -$6.5k |
| v30b | `replant_done` (dig and replant finished plants in one visit) | +$1,545 ± 458 | -$4.9k |
| v33a | hands hired at hour 1 spawn where the engine's occupancy rule puts them; pickups/drops use any access tile, water before harvest, queues re-matched at hour 2 | +$641 ± 370 | -$4.2k |
| v36b | market: sell one turn before the rival's predicted sale (inferred exactly from inventory residuals) + price floors | +$508 ± 363 | -$3.7k |

Later takeover with v33a code: day 20 -$0.2k, day 24 -$0.2k, day 26 -$0.9k.

**Pinned (249 games) against chassis+ADAPT, v33a code:**
- day 12: -$3,842 ± 315 (wins 65 vs 125);
- day 20: -$1,046 ± 200 (94 vs 125).

In pinned games the day-12 controller lets the recorded opponent earn +$2.9k more: strawberry +$1.3k, milk +$0.9k, wool +$1.6k.
The chassis sells premium goods before the rival; the controller sold them next morning, after it. That race is worth about $5.7k of margin.

## Leak diagnostics (what fixed the most)
- `leak.py`: product flow (harvested, sold, sold at $1, used, end-of-day overflow, end stock).
  Before v30a the controller lost about 36 wheat, 10 carrots and 6 strawberries per game to end-of-day shed overflow.
- `unfin` / `tiletrace` (scratch scripts): units whose queue did not finish. Late-hire spawn mismatches killed strawberries through missed must-waterings.
- `ledger.py` (full money ledger from day D0), `census2.py` (tile census), `actaudit.py` (effective actions, optional day window).

## Engine facts confirmed today
- The last processed step is 718 (day 29, hour 22). Final drops must land by then, and same-step drop+sell works.
- Plants die after 2 consecutive unwatered days. The planting day counts as unwatered, so water on the planting day.
- Finished ongoing plants decay into weeds one day after their last production.
- Town demand is 6 per shop per day (12 for single-product shops), plus 1 per day from the town centre.
  Sales at $1 do not add market supply.
- Care bonus: +1 per fed+cared day, paid at the next production (fed). Sheep reach 4 wool per 3 days with daily care.

## Late takeover and endgame (24 Sep afternoon)
- The takeover-day sweep (60 seeds, closed loop, v43 code) ran from day 20 +$1.07k to day 27 -$0.95k (7/60 wins).
  The controller's own final days were weaker than the chassis's fd4 endgame.
- Courier: from hour 12, project tonight's shed load and send loaded units to drop.
- Footprint cap: never grow more plots than the chassis ran at takeover. In herd-heavy towns the chassis leaves
  land idle on purpose; planting it overcommitted labour and the shed (seed 6008 lost 100+ goods on day 28).
- Day 29, return-aware: routes include their final delivery against the hour-22 deadline (the last processed step is 718).
  Combined with leaving age-2 carrots to grow into day 29 plus a final watering, this adds +$313 ± 78 per game (47/60 better).
- Tested and rejected:
  - planting carrots on day 27 (-$1.1k: wages);
  - keeping all growing crops for day 29 (-$0.2k);
  - SE tomato annex (-$3.1k);
  - care at any price (-$2.2k);
  - higher floors;
  - fertilizer reserve 0 / carrot fertilizer threshold.

## Submission candidates (see submit/SUBMIT_THIS.txt), 24 Sep 20:45 UTC
Adaptive takeover: the chassis's ADAPT layer already compares the two farms at steps 143/359. The controller
takes over on day 24 against a chassis copy and earlier against a divergent rival (day 16 in v61, day 20 in v62),
with the per-unit price floor and day-20 tomatoes enabled only in that case.

Pinned (249 recorded strong-team games) vs chassis+ADAPT (baseline 125 wins; 111 copy, 14 divergent, 38 vs >= 2800):
- `main_ctl_adapt.py` (v61): 172 wins (144 copy, 28 divergent, 69 vs >= 2800); flips +50/-3.
- `main_ctl_adapt_d20.py` (v62): 170 wins (144 / 26 / 66).
- Other ingredients:
  - carrot price forecast at harvest (edge 0.85), which gained 9 wins at d24;
  - day-29 return-aware routing with age-2 carrots kept for the final day.
- Tested and rejected:
  - minimal hour-0 room sales (the midnight dump of the top lot wins races);
  - lot-size caps;
  - rival-aware floors;
  - day-27 carrot plantings;
  - care at any price.

## 25 Sep: strawberry-rich towns (v74, `submit/main_ctl_rich_m7.py`)
The first four shops (known at day 12) predict the late strawberry market. With >= 3 strawberry buyers among them
(brunch, ice cream, smoothie, farmers market; 81 of 249 recorded games) the day-24 strawberry price has a median of
$155-213; with 0-2 it has crashed to $5-14. The tape always plants 33 strawberries, so in rich towns the market stays
under-supplied. Elite rivals (e.g. 摆烂小分队, +30 strawberries on days 14-16, $93k strawberry revenue) exploit it.

- `_straw_value`: n new plots planted today, straw_units at ages 10/12/14/16, sold `straw_lag` days after production
  into a book drained 6/day per strawberry shop (+1 town centre, +0.5 expected per future shop) and supplied by every
  visible strawberry plant on both farms. Calibrated on the 80 recorded rich towns (predicted vs actual quote, days
  13-29): lag 1, our weight 0.9, rival 1.0 cut the RMSE from $55 to $23.
- `rich_eval` at step 288: SE quadrant as a 16-plot strawberry annex (land + seeds + 3 fertilizer + labour). Take over
  at day 12 only if it clears `se_straw_margin`; then `se_straw` buys SE and `straw_fc` plants extra strawberries
  (on SE and on replant slots) until day 17.
- Pinned (249): 175 -> 180 wins, +$1,066 +- 265 per game, flips +7/-2. Fired in 40 games (+$6,635 each).
  Closed loop, 60 rich seeds vs live v15a: +$3,818 +- 1,004.
- A day-12 takeover without the forecast gate costs 21 of 62 wins in rich towns (-$1,562 per game): the gate matters.

Tested today and rejected (pinned):
- `room_v3` (courier and stop planning count held lots; loss-ranked room releases): -$297 +- 145 (69 games).
  End-of-day dumps are market gluts, mostly in the chassis phase.
- `race_harvest` (harvest premium goods at 1 unit): -$83 at d16, +$114 at d12 (animals are already harvested at every
  production once cared for).
- No sell timing on the divergent path: -$864 +- 220 (the rival-timing hold is worth keeping).
- Divergent-path tweaks (more tomatoes -$901, hold_max 35 / max_hands 17 no-ops, melons/floors/hire weight ~0).
- Per-day caps on forecast strawberries (16/20): no change.

Tools: `harness/pinned4.py` now takes `PIN_GIDS=file` (game subset) and `PIN_FILLS=1` (our fills, hires, h12 prices).
Full-game pinned replays (S=0) reproduce the recorded margins (corr 0.996, 81/84 same winner), so day-0 changes can be
evaluated against recorded rivals too.

## 25 Sep (evening): v81 (`submit/main_ctl_rich2_m7.py`)
- Chassis tomato block (V219) at >= 2 pizza/farmers-market shops (was 3), via `base_m7_t2.py`. Copy path +$288 +- 98
  per game (26 of 171 copy games change, no flips); closed-loop mirror 44 -> 46 wins (+$488 +- 220).
- `straw_replant=False`: the forecast's extra strawberries go only on free tiles (the SE annex), never on wheat replant
  slots: +$395 +- 317 per fired game, and it halves the two bad fired games (-3,979 -> -1,349; -6,217 -> -2,020).
- v81 vs v74 over 249 pinned games: +$194 +- 68, flips 0/0 (180 wins each).

Rejected this evening (pinned):
- cautious strawberry counts (future-shop weight 0 / 0.5): -$4,896 / -$1,434 per fired game;
- planting carrots/wheat up to day 27: copy wins 149 -> 100 (late wages and crowded-out harvests);
- copy takeover day 20/22/25/26: 126/139/131/113 copy wins vs 150 at day 24.
Close copy losses are decided on day 29 afternoon: we lead at noon, the copy rival's final harvest overtakes us.

## 25 Sep (night): v86a (`submit/main_ctl_rich3_m7.py`)
Close copy losses were decided on day 29 afternoon: we lead at noon, then the copy rival dumps carrots (h19-20) and milk
(h21) and we delivered our final harvest into those prices (h21-22).
- `final_cap=19`: every day-29 route's final delivery lands by hour 19. Copy +$209 +- 19 (hour 20: +142, 18: +129,
  17: +127), divergent +$56 +- 29.
- `final_sell0=3`: sell the top three shed lots at hour 0 of day 29 (ahead of the rival's hour-1 dump): +$31 +- 11
  (6 lots costs too many hour-0 hires: -$16).
- v86a: 182/249 pinned wins (copy 151, divergent 31, opp>=2800 75), +$192 +- 19 over v81, +$1,452 over v18.

Rejected: timing carrots/wheat/eggs like premium goods (copy -$194 +- 48); glut arbitrage (the engine only fills
BUY_PRODUCT for WHEAT and FERTILIZER, so bought wool/milk/strawberry never arrive).

Also rejected (25 Sep, night; pinned, vs v86a unless noted):
- hour-0 top-lot sales on days 26-28 (not only day 29): -$590 / -$204 (hour-0 slots are worth more as hires);
- rival-timing for carrots/wheat/eggs on the divergent path only: +$107 +- 105 (noise);
- divergent takeover day 15 / 17: -$557 (6 wins lost) / +$176 +- 255;
- wheat planting through day 26: copy -$339 +- 47;
- SANX (strawberry annex worked by hired hands while the chassis keeps playing, ADAPT signature masked): far worse than
  the day-12 takeover in the fired games (e.g. +15.5k -> -3.2k); the controller runs the annex labour much cheaper.
Endgame note: against copies the rival sells ~290 wheat on days 24-29 vs our ~175, but it also buys ~110; net wheat
revenue is within $300.
- carrots on day 27 as optional work (plant_must_last 26): copy -$2,758 (151 -> 91 wins): day-27 plantings create
  must-water visits on day 28 that cannot all be served, and the hire search buys hands at steep Fibonacci wages;
- a day-28 delivery deadline (hour 20/21, like day 29): copy -$1,074 / -$719.
v86a closed-loop mirror (60 seeds): 48-12, +$384 +- 46 over v81.

## 25-26 Sep: v100 (`submit/main_ctl_rich4_m7.py`)
- Day-18 tomato block sized by forecast (V219X, `base_m7_t3.py` + `v219x`): the chassis always planted 10 SE tomatoes
  on day 18. In tomato-rich copy towns the book reaches $250-480 on days 26-28 (hinge scarcity: 4-5 tomato shops drain
  25-31 a day) and copies with a 20-plant block beat us (112251252: -4,344; 111972195: -1,748). At step 432 the
  controller prices 10/15/20 plants (our share of every tomato arriving on days 26-29 against the town's drain, the
  rival's visible or assumed 10-plant block, seeds, fertilizer, extra hands) and picks 20 when it beats 10 by >= $3,500,
  15 when by >= $1,250. The block gets one planting hand a row and one watering hand per 8 plants (a tomato needs
  water every other day until it bears; a tile missed on a watering day dies). Calibrated on the 53 copy games where
  the block fires (forced 15: +$1,406 +- 318, forced 20: +$1,261 +- 590, the rule about +$1,800; 25 plants always
  worse than 20).
- Tick timing, divergent games only (`tick_defer` in div_over): the town buys every 4 turns right after the market
  (hours 0, 4, ..., 20), so a lot sold at hour 20 meets the book before the restock. Plain lots wait an hour; lots due
  one turn ahead of the rival's predicted sale still go (beating the rival's lot is worth more than the restock:
  without that exemption -$419). Divergent +$184 +- 67; everywhere +$100 +- 31 but two copy wins flip.
- v100: 185/249 pinned wins (copy 154, divergent 31, opp>=2800 78), +$438 +- 127 over v86a (flips +4/-1).
  Closed-loop mirror vs live v15a (60 seeds, seat 0): 51-9 +$2,805 (v86a 48-12). Official runner DONE in both seats.

Rejected (pinned, 25-26 Sep):
- carrot-rich towns (>= 3 PET_CAFE/FM demand points among the first four shops) taking over on day 12 with carrots
  first: -$3,075 / -$4,020 per game, 20-22 wins lost;
- day-29 variants: max_hands_final 18 (no effect), divergent final_cap 17 / 21 (-$171 / +$9);
- rival timing knobs on divergent games: hold_max 8 -$509, rival_days 3 -$47, timed melons 0;
- the controller's own SE tomato annex on divergent games (se_on, days 16-18): -$928 (bought in 26/78, lost money in
  nearly all, even at forecast +$32k);
- a day-10 melon front-run against copies: impossible (hands respawn at the shed; the tape's h9-h15 deliveries are the
  earliest the geometry allows).
Where the rest is: divergent losses (47) are mostly elite rivals ahead by > $5k on every product (their opening builds
tomatoes, melons, geese and earlier strawberries by day 12); copy losses (17) are within $2.5k except one.

## 26 Sep: v108 (`submit/main_ctl_rich5_m7.py`) = v100 + herd expansion
Milk and wool books spike in some towns (px12 peaks: a quarter of games >= $189; up to $268 milk / $249 wool) because
the chassis picks its herd from the first two shops only; later yarn stores and milk shops go unserved. A
perfect-foresight bound (extra animals bought on day 12, actual price paths) was > $1k in ~45 games each for milk
and wool.
- `herd_on` (controller days: divergent 16-18, strawberry-rich 12-18): price k extra sheep/cows from a book forecast
  (town drain now + expected shops, every visible animal on both farms at its cared rate - the rival's at 1.0, not 0.8:
  elite rivals care fully, which is what sank the first version -, new animals min(held, fy) units after fy days then
  1+iv every iv days, the day's lot shared with the rival), net of price, feed, labour ($60/animal-day), fertilizer and
  land (own SE or tiles beyond 6 spare only: the first version put 12 geese on the strawberry annex, -$44k).
  Buy when > $3,000, at most 6 animals a game, hour-0 BUY_ANIMAL so the day's routes place them.
- `herd_rich_margin` 4000, cows only: copy games take over on day 12 when the cow forecast is large (sheep excluded,
  wool's glut side is quadratic: the two sheep takeovers lost $7.8k / $2.4k). A div-over leak once let a sheep forecast
  fire the cow rule and buy nothing: the day-12 takeover alone cost $16.9k in that game (fixed: the check prices only
  the rule's own kinds).
- v108 vs v100: +$170 +- 63 per game (copy +$178, divergent +$152), no flips; fired in 13 games (11 better, +$0.5k to
  +$8.6k). Geese were never chosen. Mirror 51-9 +$2,867; pipe16 40-0, ahmed v47 39-1; official runner DONE.
Also rejected: carrot_edge 0.7 / 1.0 / 1.2 on copy games (-$174 / -$59 / -$415; 0.85 stays), 0.7 on divergent (-$3).
Rejected after v108 (pinned vs v108 unless noted):
- copy takeover day 23: +$44 +- 118, wins 154 -> 152 (day 24 stays);
- herd-rich margin 3000: identical (no cow forecast between 3000 and 4000); geese in the controller herd: never chosen;
- strawberry-rich path: carrot_edge 1.0 -$95, carrot forecast off -$199; rich margin 1500 / 3500: -4 wins / -$135;
- 15-plant tomato option, closed loop (200 games vs live v15a): +$64 +- 84 where chosen (neutral; pinned +$1.4k
  per eligible game), kept.
Robustness: 400 closed-loop games vs live v15a 371-29, 0 errors, max step 0.28 s; vs the newest public top agents
metav4 v13 36-4, a-smaller-market-shock 37-3, one-more-wheat / pipe16 variants 40-0 (+$349 / +$480 per game over v86a
against the two strongest). metav4 v13 is classified a chassis copy by ADAPT (day-24 takeover) and plays like live v15a.
- tomato harvest threshold 2 / 1 (sell the day-26 production at the top of the book): -$226 / -$181 on tomato and
  divergent games; day-26 sales only pull day-27 prices down, the day-29 dump (60-80 units at ~$110 in rich towns) stays.
- geese allowed in the day-12 herd takeover: never fire (identical); hire_cost_w 0.5 / 0.7: -$28 / -$15 on ~127 games
  (0.6 stays); against metav4 v13 in closed loop a day-22 copy takeover gains $272 per game but day 22 lost copy wins
  on the recorded games, day 25 is worse (33-7): day 24 stays.

## 26 Sep: pushing past v108
- Early controller takeover against rivals ADAPT flags divergent on day 5 (S=144 pinned, 38 games): day 6 -$62k,
  day 10 -$20k, day 12 -$2.5k per game. The controller cannot run an opening (it skips the chassis's planned animal,
  seed and land investments and hires half the hands); the elite rivals' edge (SW land on day 9, 15-27 wheat the same
  day, strawberries from day 2, staggered melons, 4-7 cows / 5-6 sheep on day 6) has to come from a scripted opening.
- Chassis constants tuned by the public authors on mirrors (`chassis_globals` knob): V9_HERD species rules, V9_RACE
  margin 8/16 and horizon 32/44, V9_CARROT ratio 1.5/2.2, V9_COURIER hour 8/16, V219 cash 12000 / tomato price 60:
  flat on the recorded field (few games change, net ~0).
- Divergent footprint slack 5 / 8 / off: +$132 +- 160 / +$19 / -$769; divergent wheat until day 26 / 27: -$227 / -$29;
  no strawberry-rich rule against flagged rivals: -$3,550 (margin 5000: -$254); herd margin 2000 / 9 animals /
  labour 45: +$56 / +$16 / +$40 (noise).

## 26 Sep: v130 (`submit/main_ctl_rich6_m7.py`) = v108 + big tomato block two days ahead of the copy
Copies plant their tomato block on day 18 and sell days 26-29; in rich towns both farms then dump 60-80 units on day 29
at ~$110 while the copy took the day-26 top of the book ($290-318). `base_m7_t4.py` makes the block's planting day
movable (`_V219_DAY`, falling back to day 18 when it does not qualify yet) and adds thirst-only growth crews
(`_V219_THIRST`: a crew only on days some plant needs water, sized to those plants, never doubled for a late request).
`v219x_early_n=20, v219x_early_day=16`: on day 16 price the block; when it already picks 20 plants, plant then.
- copy games: day 16 +$149 +- 76, no flips (14 blocks moved: 12 better, +$25.5k); day 17 +$89 +- 61 / +$142 (without
  thirst crews, one flip each); day 15 -$638 per block game; moving 15-plant blocks to day 17: -5 wins.
- without the thirst crews a day-17 block set off a late doubled crew on day 18 (18 hires, Fibonacci wages +$6.2k).
- v130: 185 wins, margin +$5,323 (v108 +$5,221). Closed loop neutral against live v15a / metav4 / smaller-shock.

## 27 Sep: probes past v130
- Melons on the block's free SE tiles (`base_m7_t5.py` + `v219x_melon`, forecast-sized, harvested at age 10 by the
  controller): 53 block games -$819 +- 206 (up to 10 melons) / -$434 +- 165 (extra hand-day priced $800). Melon sales
  +$2.1k per block game, but the fifth planting crew and the melon-only watering crews are the 15th-16th hires of the
  day ($610-987 each, +$1.8k wages) and tomatoes lose a little. Needed fixes on the way (kept in t5, unused): melons
  are thirsty every day of their yield window, V13V's skip days (19/21/23) count melons, the chassis never harvests an
  unripe melon, a lone thirst crew tours only the thirsty tiles.
- `visit_watered` (a mid-day re-plan of a plant watered today gains nothing from WATER, so no harvest one unit short):
  -$300 and 6 fewer wins on the block games; not used.
- 25-plant block option (margin 6000 / 9000): +$112 +- 95 / +$93 on the 53 block games (noise).
