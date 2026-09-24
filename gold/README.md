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

## Submission candidates (see submit/SUBMIT_THIS.txt)
Pinned (249 games) vs chassis+ADAPT (baseline 125-124):
- `main_ctl_d24.py` (v40f) wins 145; against opponents rated >= 2800 it wins 56 vs 38.
- `main_ctl_d20.py` wins 133.
