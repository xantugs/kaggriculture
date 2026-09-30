# Controller loop with ChatGPT (owner's request, 29 Sep ~18:50 UTC): ~50 iterations overnight, keep pushing

Goal: a controller-side answer to the new-meta lineage (960 band: step-1 rival money 940-980, no hands; the top teams
UMG/DSM/DECEM/Vadim + the ladder players who beat v33 c2tr). NO Kaggle submission without the owner's explicit yes
(live: v33 c2tr + v32 PFcfc; CGt frozen in gold/final, not submitted).

## How a round works
1. Build variants: `v33loss/build_nmp.py OUT '<json overrides of the p1e open profile>'` (student: the 960 band goes to the
   p1e controller with the overridden profile; every other rival exactly as c2tr). Always end patches with a new
   `_xxx_submission_agent = agent` if `agent` is re-bound (last-callable trap).
2. `nohup bash nmloop/eval.sh CAND TAG` -> rows nmloop/lg_TAG (ladder mini-gate), bl_TAG_* (blind 4x20), f960_TAG (420
   seats); "TAG done" lands in nmloop/eval.log (~10 min; one eval at a time, ~16 processes).
3. `python nmloop/summary.py TAG ...` -> compact line per candidate vs the tape.
4. Send the lines + trace notes to ChatGPT (thread "Claude Workflow Chat", tab seed), ask for 1-3 variants in the JSON
   format {"variants": [{"name", "overrides", "why"}]}; read the reply (scroll containers to the bottom first).
5. Log each round below and in gold/top10/CONTEXT.md.

Bar (ChatGPT): >= 2 ladder loss->win flips with 0 wins lost, >= 65/80 blind, fresh960 net positive.

## Baselines
- tape (c2tr/CGt): ladder -15.7 / -9.9 / -23.2 / -10.7 / -7.8 / +9.4k (Y&G, RS Turley, Siyuan, pangzi, Tremble, azamat);
  blind 59/80; fresh960 12 wins of 410 stable.
- c0tp (p1e vs everyone, c2tr profile): ladder -10.9 / -7.4 / -23.6 / -9.8 / - / +4.9k; blind 57/80; fresh28 81 vs 132.
- NM1 teacher (literal replay): -27.3 / -13.4 / -33.4 / -49.1 / -44.3 / -24.9k. Dead (desync).
- NMp1: -10.9 / -4.0 / -20.2 / -5.1 / -13.0 / +1.0k; blind 60/80; fresh960 13 vs 12 (+6/-5), margin -814.
- NMp2: -13.5 / -1.2 / -17.8 / -8.6 / -8.2 / -5.4k.

## Rounds
- L1 (19:05 UTC): sent results + teacher medians + knobs; NMp3 (teacher-median flat targets) evaluating.
- L1 reply (19:07): NMp4 (land NE 7 / SW 9), NMp5 (mid_melon), NMp6 (both + anim_day_max 6), all on NMp3's teacher targets.
- Results: NMp3 ladder -15.5/-10.6/-21.8/-37.6/-14.8/-11.4k, blind 49/80, fresh960 7 vs 11 (-$8.5k). NMp4 blind 52, NMp5 56
  (RS Turley -0.3k), NMp6 50; pangzi -32..-38k for all. Teacher targets make the p1e executor worse; NMp1 stays best (60/80).
- diag.py milestones: with teacher targets our cows reach 5 on d7-9 (rival d5), geese 5 on d12-16 (rival d7-9) at the same
  $0-40 cash floor; NMp1 d0-10 spend ~= rival's (wages/seeds/animals within $1k) but sales $16.6k vs $36.5k in pangzi.
- LIVE LOSSES by phase (tape, 4 games avg): days 0-15 sales us $43.3k vs rival $55.0k; days 16-29 us $49.5k vs $66.1k, the
  late gap mostly EGG $4.9k vs $13.3k (-8.4k), strawberry -3.6k, carrot -2.8k, melon -1.7k, tomato -1.1k; wool/milk +1k each.
  The controller's divergent-rival herd window (div_over: days 16-18) buys only SHEEP/COW, margin $3k, max 6 -> LG1 (+GOOSE,
  herd_max 8, total 10) and LG2 (+ margin 1500) on c2tr (all divergent rivals, both routes); evaluating 19:15.
- L2 reply (19:20): LG3 (geese-only herd window, margin 1500), LG4 (+ EGG in mkt_dp_prods), LG5 (GOOSE/COW/SHEEP, margin 1200 +
  EGG DP). Results: LG1 == tape on all panels; LG2 fresh960 11 vs 12 (sheep/cows bought in 22 seats, geese never); LG3/4/5
  quick == tape (EGG DP -> RS Turley -9.6k vs -9.9k). Cause: _herd_value charges days x (wheat_px + herd_labor 60) per animal
  -> a day-16 goose costs ~$1.6k for ~18 eggs (~$720-900); even by hand the late goose is ~break-even (feed ~$455 + $300).
  The rival's egg economy pays only because its geese start by day 7-9. Late-herd lever: dead.
- buys.py (per-day purchases, NMp3 vs the repaired rival in pangzi's game): the rival buys 2 cows + 3 sheep on d0, 1 cow/day
  on d2-4, 6 GEESE on d6 (the NE land day), 2 geese + 19 wheat seeds on d8 (the SW land day), hires only 3 on d1, and dumps
  ~420 WHEAT + 48 MELON units on d10-11 ($34k in two days; wheat base $25, log glut curve: 400 units move it only 20%).
  NMp3 bought geese on d9-11, wheat 26 on d9, sold $7.9k on d11.
- L3 reply (19:33): NMp7 (NMp1 + due cows/geese bought before strawberries / wheat / non-due land; COW,GOOSE,SHEEP order;
  anim_day_max 4) -> built as anim_before_straw + abs_last 15; NMp8 (NMp7 + SHEEP flat 3, anim_day_max 5); LD1 (late wheat
  denial seller rule, code-level, later). Mine: NMp9 (NMp8 + the rival's timing: COW {0:2, 2:3, 3:4, 4:5, 7:7}, GOOSE {6:6, 8:8},
  anim_day_max 6, mid_wheat_max 20). Quick screens 19:33.
- L4 results: NMp7 blind 51, pangzi -18.2k, azamat -1.5k; NMp8 blind 49; NMp9 blind 49 (animals-first starves the crops).
- L4 reply (19:38): cash cycle instead of herd, on NMp1: NMp10 (mid_wheat_from 7, mid_wheat_max 20, wheat_cap 22), NMp11 (+ melon0 6,
  melon_last 7, mid_melon), NMp12 (+ day-10/11 liquidation; built as melon_sell_now 1 + melon_day {min_units 12, slack 4}).
  GPT wants cash at days 9-11 and wheat/melon revenue on those days. Quick screens 19:39.
- L5 results (19:48): NMp10 blind 54 (azamat lost); NMp11 blind 59 (RS Turley -3.7k, azamat lost); NMp12 blind 62/80 and
  FRESH960 16 vs tape 11 of 405 stable (+7/-2; DSM 6/3, DECEM 6/3), margin -$4,390 (more wins, lower mean), ladder 0 flips,
  azamat lost. FIRST positive win delta on the big panels. Day-11 cash matches/beats the rival (pangzi 7.9k/8.3k, RS 8.6k/5.8k,
  azamat 9.6k/7.5k; day-10 melon dump 36 units like the rival) but no wheat dump (9 vs 423 units in pangzi).
  BEST SO FAR: NMp12 = NMp1 + wheat pulse + melon cycle + melon_sell_now/melon_day (cands/full_NMp12.py).
- L5 reply (19:50): NMp13 (NMp1 + melon cycle + day-10/11 liquidation, no wheat pulse), NMp14 (NMp12 + day-6 dairy guard:
  >= 1 milk shop among the first two -> revert to NMp1 values; build_nmp_guard.py; GPT suggested 2 but azamat's first two are
  PET_CAFE + PIZZA), NMp15 (NMp12 + until 20). Priority 13, 15, 14. Full evals 19:50 sequential.
- NMp12 - tape final revenue on fresh960 (405 stable): EGG +5.7k, FERT +1.1k, WOOL +0.8k, MILK +0.7k, WHEAT -3.0k, CARROT -0.7k,
  MELON -0.6k; hire -1.8k, anim -1.0k; our cash +$907 but the ELITE's cash +$5,297 (our lower wheat sales lift its prices).
- NMp13 (19:57): ladder -10.5/-5.2/-21.4/-10.0/-6.1/-0.8k (better than the tape on all 5 losses, azamat lost by $0.8k),
  BLIND 66/80 (passes 65), FRESH960 16 vs 12 (+7/-3), margin -$1,808, cash +$2,619. BEST SO FAR (cands/full_NMp13.py):
  NMp1 + melon0 6, melon_last 7, mid_melon + melon_sell_now 1, melon_day {min_units 12, slack 4}. Sent to GPT 19:58 (L6 partial).
- NMp14 (NMp12 + dairy guard): blind 63, fresh960 14 vs 12, margin -2.1k, azamat -0.7k. L7 reply (20:03): NMp16 (NMp13 + day-6
  dairy guard reverting only the melon cycle), NMp17 (NMp13, melon_day min_units 18), NMp18 (NMp13 + hire guard, built as
  over.max_hands 10 + hire_cost_w 1.3). Queued after NMp15 (full evals).
- NMp15 (NMp12 + until 20): blind 59, fresh960 13 vs 11, margin -6.1k, every ladder game worse -> the day-16 hand-over helps.
- Robustness: blind2 panel (same 4 replays, seeds 9510-9519) for TAPE (CGt) and NMp13 -> nmloop/b2_<TAG>_*.jsonl.
- BLIND2 CORRECTION (20:18): seeds 9510-9519: TAPE 72/80, NMp13 60/80 -> 160-game totals TAPE 131, NMp13 126. eval.sh/quick.sh
  now run blind on 9500-9519 (160 games); summary.py baseline = bl_TAPE160_*. NMp16 (NMp13 + dairy guard): blind 66/80 (panel 1),
  fresh960 14 vs 12, margin -938, azamat -0.7k. NMp17 (melon_day 18) == NMp13 (fresh960 16 vs 12, margin -1,621).
- L7 sent 20:25 (correction + results; asked for a bigger structural lever). NMp18 (over.max_hands 10, hire_cost_w 1.3) running.
- NMp18 (over.max_hands 10 + hire_cost_w 1.3): COLLAPSE (ladder -56..-126k, blind 43/160, fresh960 1 vs 6 on 95 stable). Hiring
  weights are extremely sensitive: never touch `over` hiring knobs.
- L8 reply (20:32): late controller (days 16-29) instead: LC1 late crop value replant, LD1 wheat denial, LC2 carrots; park NMp13.
  Bar: blind160 net positive, fresh960 >= +5, broad gates (381 + 851) >= -2, ladder flips. Existing knobs cover most of it:
  c2tr late settings: straw_last_plant 12, straw_fc False, late_plan False (from 24, min 15), carrot_edge 0.85 (min demand 1,
  first 14, last 26, carrot_fc True), feed_reserve_tiles False, melon_on True / melon_last 19 / tomato_last 20 via div_over.
  Built via div_over: LC1a (late_plan True from 16, min 10), LC1b (straw_fc + straw_replant + straw_last_plant 16), LC2
  (carrot_edge 0.7 + CARROT in mkt_dp_prods). Full evals from 20:36.
- L8 results (20:50): LC1a blind 131/160, fresh960 13 vs 12 (+1/-0), margin -537; LC1b == tape; LC2 blind 129, fresh960 11 vs 12.
  Late-controller knobs: neutral. Sent L8 at 20:55. Probe: public master engines (../pubnb/v930/x_the-2965-master-hybrid-engine.py
  PUBmh, x_kaggriculture-harvest-ledger.py PUBhl, x_the-shepherds-ledger-herd-safe-sovereign.py PUBsl) quick screens.
- Public engines (PUBmh/PUBhl identical, PUBsl): blind 84-85/160, ladder worse everywhere; route-tape agents -> ME1-3 off.
- L9 sent 21:05 (plan: NMp13 + LC1a = NMLC, fresh29 held-out validation after ~00:10 UTC). L10 reply: NMp19 (= NMLC, running),
  NMp20 (capital gate: keep NMp13's melon cycle only when the day-10/11 payout is underfunded; built as build_nmp_cap.py: at step
  144 our MELON plants >= 10 -> revert to NMp1 values), NMp21 (NMp13 without mid_melon). GPT: run the FROZEN NMp13 vs tape on
  the 29 Sep dataset first; if negative there, demote the opening branch.
- NMLC / NMp19 (NMp13 + late_plan): blind 127/160, fresh960 15 vs 12 (+6/-3), margin -2.4k: not additive. L10 partial sent 21:13.
- fresh29.sh running (polls Kaggle every 10 min for the 2026-09-29 dataset; then fetch, gate build, TAPE then frozen NMp13;
  progress in nmloop/fresh29.log; rows nmloop/f29_TAPE.jsonl, f29_NMp13.jsonl).
- NMp20 (21:20): ladder -11.6/-1.9/-19.9/-6.6/-12.5/-0.7k, BLIND 138/160 (tape 131: +7), fresh960 14 vs 12 (+6/-4), margin -310,
  cash +2,367. BEST BALANCED SO FAR (cands/full_NMp20.py = NMp13 with the day-6 capital gate: >= 10 melons -> NMp1 path).
- L11 reply (21:20, written before NMp20's result): NMp22 (NMp13, melon 10), NMp23 (liquidity gate: money + 900 x melons >= 7000
  at step 144 -> NMp1 path; build_nmp_liq.py), NMp24 (start on NMp1; at step 144 ENABLE NMp13's melon catch-up if melons < 10;
  build_nmp_late.py). Queued after NMp21. GPT: if frozen NMp13 is neutral/negative on fresh29, stop tuning and analyse the
  fresh960 flip states instead.
- NMp21 (21:28): blind 133/160, fresh960 12 vs 12, azamat +2.0k kept. L11 partial sent 21:29.
- NMp22 (melon 10): blind 125, fresh960 13 vs 12, azamat -8.7k. L12 reply (21:37): NMp25 (gate >= 8), NMp26 (gate >= 12), NMp27 (gate 10 + dairy: mid_melon off when a milk shop is among the first two; build_nmp_capd.py). Queued after NMp24.
- NMp23 == NMp20 (same selection); NMp24 (late enable) blind 113/160, fresh960 10 vs 12: day-0 melon changes are what matter. L12 partial sent 21:51.
- NMp25 (gate 8) == NMp20 (bimodal melon counts). NMp26 (gate 12, 22:05): ladder = NMp20, BLIND 139/160 (+8), FRESH960 16 vs 12
  (+8/-4), margin -672, cash +2,629. NEW BEST (cands/full_NMp26.py). L13 sent 22:06.
- NMp27 (gate 10 + dairy) == NMp20. L14 reply (22:13): NMp31 (gate 11), NMp32 (gate 12 + dairy mid_melon off), NMp33 (mid_melon
  cutoff day 8: a no-op with melon_last 7, skipped); broad-gate check of frozen NMp26 first (broad.sh: goldg + top10g -> og_*).
- NMp26 broad (old 381 vs c2tr): 324 identical, wins 132 vs 133 (+1/-2), margin -162 -> broad total +3 (fresh960 +4, old -1). L14 partial sent 22:20.
- NMp31 (gate 11) ~= NMp26 (blind 138, fresh960 16 vs 12). NMp26 FROZEN as gold/final/NMp26_final.py (sha256 55e45d1b...) +
  backup; not submitted. L15 reply (22:27): NMp34 (gate 13), NMp35 (old-style vs new-meta rival guard), NMp36 (bucket audit).
  Old vs new top-team day-3 farms: new = wheat 9, straw 2, cows 3 (258-263/265); old = 62% "wheat 4-5, melons 10, cows 2, straw 4"
  + 34% new-like. NMp35 (build_nmp35.py): NMp26 + at step 72 rival wheat <= 6 or melons >= 10 -> revert to NMp1 melon values.
  Queue: NMp32 (running) -> NMp34 -> NMp35 (+ broad).
- NMp32 (gate 12 + dairy): blind 136, fresh960 14 vs 12 -> dairy clause retired.
- NMp34 (gate 13) == NMp13 (counts never exceed 12). Gate curve: none 126/16, 8=10 138/14, 11 138/16, 12 139/16. L15 sent 22:43.
- NMp35 build had failed silently (unescaped %d in the template + build chained into a backgrounded list); rebuilt 22:55, eval + broad launched separately. LESSON: build in the foreground, then launch nohup on its own line.
- L16 reply (22:55): NMp37 (NMp13; at step 144 with exactly 12 melons turn off ONLY the liquidation), NMp38 (liquidation for 12-melon farms only if day-10/11 cash < 6k), NMp39 (earlier predictor). NMp37 built, queued after NMp35.
- L16 sent 23:08 (NMp35 == NMp26 everywhere incl. old 381). fresh29 will also run frozen NMp26 after NMp13 (f29_NMp26.jsonl).
- NMp37 (NMp13 + at step 144 with 12 melons only the liquidation off) == NMp26 (blind 138, fresh960 16 vs 12, margin -661): the
  gate's whole effect is ONE seller rule (force the melon dump only when the cohort is short of 12). L17 sent 23:15.
- L18 reply (23:17): AZRS_trace first, then NMp38 (short cohorts: dump only while cash < 6k), NMp43 (< 4k).
- AZRS_trace (azrs.py / azrs2.py, tape CGt = A vs NMp37 = B):
  azamat: A +9.4k, B -0.7k. First |gap| > 1k on day 8 (-1.1k: B has 5 geese, cash $188 vs $1,238), day 10 -6.0k (melons sold
  60 vs 36), but B leads days 14-21 (up to +4.4k); the loss is days 22-29 (gap -2.2k -> -10.1k). Days 14-29 by product (B-A):
  our STRAWBERRY -10.5k, rival STRAWBERRY +5.9k, rival milk +3.4k; ours melon +5.0k, egg +3.0k, carrot +2.9k, milk +2.6k, tomato +2.2k.
  Root: day-11 reinvestment. A buys 9 strawberry seeds on day 11 (25 tiles d12-22); B re-plants melons + wheat (15 strawberry
  tiles, none after day 25; 34 wheat tiles that earned +0.2k).
  RS Turley: A -9.9k, B -1.9k (+8.0k). First |gap| > 1k on day 10 (-9.1k, melons 60 vs 30), B ahead from day 18. B's gains:
  wheat +6.7k, melon +5.0k, egg +2.7k; strawberries equal (+0.4k) with 23 tiles vs A's 33 (A bought 13 strawberry seeds day 11).
  Both towns have 1 strawberry buyer by day 11 and 2 by day 12; azamat gets a third (SMOOTHIE) on day 15, RS not until day 24.
- Queued (queue18.sh, 23:21): NMp38 (cash 6k), NMp39s (NMp37 + straw_hf late [5, 4, 11]: day-11 strawberry top-up, cap 26),
  NMp43 (cash 4k). build_nmp_cash.py.
- fresh960 buckets (NMp37 - tape by strawberry buyers known by day 11 / day 15): (1,3) n=36 margin -5.95k (our straw -4.0k, elite
  straw +7.4k), (2,3) n=86 -2.1k, (3,3) -5.3k; gains at (0,0) +6.8k, (1,1) +3.4k, (2,2) +1.1k. Elite straw +2.85k on average.
- L18a sent 23:27 (trace). Reply: NMp44 (once 3 strawberry buyers are visible, top up strawberries to 26 on free/replant tiles),
  NMp45 (cap 22), NMp46 (diagnostic: rival straw plots day 12 as an early signal). Built with build_nmp_d15.py (trigger window
  days 12-15, straw_last 15, target = cap). azamat: NMp37 -0.7k -> NMp44 +4.5k (our straw +9.0k from 9 day-15 plots; rival -1.1k).
- NMp38 == NMp37 on the ladder (the cash rule never binds there: 12-melon cohorts are reverted anyway).
- queue18 stopped after NMp38; queue18b.sh (23:40): NMp44 -> NMp39s -> NMp45 -> NMp43.
- NMp38 (23:29): ladder == NMp37, blind 138, fresh960 16 vs 12, margin -495 (NMp37 -661): +166, no win change.
- NMp46 diagnostic (recorded PLANT STRAWBERRY actions of the elite by day 12, 408 fresh960 seats): weak predictor of >= 3 buyers by
  day 15 (precision 0.53-0.65 vs base 0.53) -> dropped; the shop trigger splits fresh960 cleanly (fires on 215 seats where
  NMp37 - tape = -2.5k; silent on 193 where it is +1.4k).
- Siyuan/Y&G traces (NMp37): strawberry gap -12.7k/-12.1k. Engine: every shop instance takes 1 unit per 4 steps (2 if it buys
  one product), the town center 1/day; strawberry price falls $1.92 per unit above I0 -> 1 buyer = ~7 units/day. A plant
  yields 4 units (8 fertilized) on days +10/+12/+14/+16, then dies. Siyuan (1 buyer to day 18): the rival sells days 14-18 at
  $150-192 (hours 0-1), we sell days 19-23 into the glut at $72 -> $4; the price recovers to $93-145 on days 27-29 when we have none.
- fresh29 will also run NMp44 after NMp26 (f29_NMp44.jsonl).
- queue18c.sh (after NMp43): NMp48 (top-up trigger >= 2 buyers), NMp49 (>= 0: always from day 12). build_nmp_d15.py arg 7 = MINB.
- NMp44 (23:38): ladder -11.6/-1.9/-19.9/-6.6/-12.8/+4.5k (azamat win kept: flips +0/-0), blind 138/160 (+19.2k; 27 games
  changed vs NMp37, +1,377 each, no flips), fresh960 16 vs 12 (+8/-4), margin -457 (NMp37 -661), cash +3,024 (77 seats changed,
  +1,140 each, no flips). NEW BEST. NMp38 vs NMp37: 137 seats changed +490 each, no flips.
- NMp50 = NMp38 + NMp44 (build_nmp_combo.py OUT OVER REV 12 6000 26 12 3). queue19.sh (23:41, after NMp39s): NMp50, NMp45,
  NMp48, NMp49, NMp43 (queue18b/18c stopped).
- L18b sent 23:44. Reply: NMp51 (1 strawberry buyer by days 3-6: move 7 NE plots into days 4-5, total unchanged), NMp52 (4),
  NMp53 (days 14-18 with <= 1 buyer: sell the shed's strawberries at once while the marginal quote >= $130). build_nmp_early.py
  (args: ... MINB EK SELL_THR). Siyuan: NMp51 -20.5k, NMp52 -20.1k (no-ops: days 4-8 cash is $40-650, the early targets can't
  be funded), NMp53 -18.8k (+1.1k vs NMp44). queue20.sh (after NMp39s): NMp50, NMp53, NMp45, NMp48, NMp49, NMp51, NMp43.
- broad check of NMp44 queued after NMp43 (og_NMp44_*).
- NMp39s (23:46; day-11 top-up late [5,4,11]): ladder -9.9/-5.1/-20.9/-5.4/-12.8/+8.7k, blind 128/160 (vs NMp44: 108 changed,
  -1,447 each, -10 wins), fresh960 16 vs 12, margin -594 (vs NMp44: +1 win, +80 per changed seat). Retired: the day-11 bet costs
  blind games; the days-12-15 shop trigger (NMp44) is the clean version.
- Seller timing check (Siyuan, NMp37): same-day price gaps vs the rival are small for every product (strawberry -757 over 11
  days, milk +949); the loss is the season timing (the rival's strawberries ripen days 14-18, ours 19+) and volume.
- Preflight of NMp44 started (official self-play 6042/8500 -> preflight_NMp44.log); imports identical to c2tr_final.
- fresh960 buckets (NMp44): the top-up acts only in (2 buyers d12, 3 by d15): +947/seat vs NMp37; with 3+ buyers already on day 12
  NMp44 == NMp37 (target already at the cap). There NMp44 - tape = -2.2k with hire -7.8k (!): our revenue is higher on
  strawberry +1.7k, egg +5.3k, wheat +1.3k, wool +1.1k, but wages eat it. Wages (traces): tape d0-15 $1.0k, d16-29 $2.0-3.2k;
  NMp37 $2.0k / $3.2-5.7k; rivals steady 11-12 hands (ours swing 8-15; Fibonacci cost: 15 hands = $1,596/day).
- build_nmp_hire.py (... MINB HIRE_W MAX_HANDS): edits the opening's saved GC_P (restored at the day-16 handover). Ladder
  (Siyuan/RS/azamat/Y&G vs NMp44): NMp56 (w 1.0, 15) +0.5/0/0/-; NMp57 (0.8, 13) +0.5/0/+0.2/-; NMp58 (1.0, 12) +1.0/+1.1/-0.3/-0.8
  (RS -0.85k); NMp59 (1.0, 11) +1.8/+1.0/0/-1.7.
- NMp50 (23:54) vs NMp44: blind 16 changed -489 each, fresh960 137 changed +401 each, no flips; margin -321. Neutral.
- queue21 (after NMp53): NMp58, NMp45, NMp48, NMp49, NMp56.
- L19a sent 23:57 (crew leak). Reply: NMp60 (post-16 cap 12, must-visits override), NMp61 (crew +1/day max, must floor),
  NMp62 (min feasible + 1; ~= NMp56's true-cost search, skipped). build_nmp_crew.py (... HIRE_W MAX_HANDS MODE K; wraps
  GoldCtl._route_and_hire; rerun with the normal ceiling if a must-visit is left unserved). Ladder vs NMp44 (Siyuan/RS/azamat/Y&G):
  NMp60 +0.4/+1.1/-0.3/-0.8 (== NMp58 except Siyuan), NMp61 -0.5/+0.5/-0.1/-1.2 (smoothing worse).
- queue22.sh (after NMp53): NMp58, NMp60, NMp45, NMp48, NMp49.
- broad NMp44 waiter re-keyed to 'queue22 done' (the NMp43 one was killed).
- NMp53 (00:05; sell strawberries early in 1-buyer towns, quote >= $130): ladder Siyuan -18.8k (+1.1k), blind 138 (17 changed,
  -513 each), fresh960 16 vs 12, margin -521 (63 changed, -434 each), no flips. Retired.
- fresh960 NMp44 margin distribution: 332/420 seats lost by > $10k, only 11 within -$3k -> +$1-2k tweaks can flip few seats.
- NMp58 (00:10; post-16 hire_cost_w 1.0 + max_hands 12): ladder -12.4/-0.8/-19.0/-4.8/-12.8/+4.2k, blind 137/160 (93 changed,
  -842 each, flips +1/-2), fresh960 16 vs 12, margin -193 (303 changed, +303 each, no flips), cash +4,030. Wash on wins.
- Crew instrumentation (NMp44 d16-29): 53-69 visits/day, 28-61 must (mostly WATER), up to 29 FERTILIZE; 13-14 hands at 63-69 visits.
- fresh29 dataset landed 00:07 (584 ids); fresh29.sh fetching -> gate -> tape, NMp13, NMp26 (waiter), NMp44 (waiter).
- L19b sent 00:12 (NMp53/NMp58 + "freeze NMp44 or one more structural idea?").
- L19b reply (00:15): NMp63/64 feed outsourcing (buy feed, convert surplus wheat plots), brutal stop: >= 2 extra fresh960 flips
  or $5k+ on Siyuan/Y&G/Tremble, else freeze NMp44. Post-16 controller already outsources (feed_reserve_tiles False, buys wheat
  when short); opening wheat_cap: NMp64a (20) Siyuan -1.5k, RS -6.2k, azamat -9.3k (win lost), Y&G -4.0k, Tremble -5.1k;
  NMp64b (16) worse. Opening wheat funds the day-8-11 economy. Killed -> NMp44 frozen pending fresh29.
- queue22 stopped after NMp60 (NMp45/48/49 dropped; CPU to fresh29); broad NMp44 starts after NMp60.
- fresh29 reorder (00:23): NMp44 runs as soon as the gate is built and NMp60 is done (parallel to the tape); broad NMp44 after it.
- NMp60 (cap 12 + must fallback) vs NMp58: blind 102 changed -688 each (flips +2/-4, 135/160), fresh960 162 changed -1,149 each
  (flips +1/-2). Worse. Crew-cap family retired (NMp58 wash, NMp60/61 worse). NMp44 stays the reference.
- fresh29 gate: 656 seats (Boey/DSM/Vadim/Victor/DECEM 80 each, UMG 72, Majkel 45, Yizhou 37, Anton 32, akmr 30, ...).
- NMp44 timing on fresh960 (loaded machine): per-game max step p50 0.369 s, p99 0.862 s, max 1.079 s; 0 errors (NMp37: 0.327/0.679/0.865).
- NMp60 changed 419/420 fresh960 and 160/160 blind seats vs NMp44: the double _route_and_hire call has side effects; retired.
- State reset: not needed; fresh-load replays reproduce live v33 exactly -> Kaggle loads per episode (c2tr itself mutates GC_P per game).
- fresh29 partial (00:37, ~75%): 960-band = 432 of 656 seats. NMp44 vs tape on 266 stable band seats: wins 5 vs 5 (L>W 1, W>L 1),
  median delta -218, mean -1,061, our cash +2,827 (the elite earns +3.9k more vs us), wages -4,873, strawberry +753. Per team:
  DSM -1.4k, Vadim -0.9k, Victor -1.9k, UMG -0.1k. All seats: 21 vs tape 23 (outside band 15 vs 18: tape W -> NMp44 L 5, all Boey
  = c2tr's herd-first controller). Margins: P25 -20.4k, median -15.8k, P75 -11.9k; |m| <= 3k: 8 seats.
- fresh29 ledgers (band, n=301, NMp44 - tape): ours egg +6.0k, fert +0.9k, wool +0.8k, straw +0.8k, wheat +0.7k, carrot +0.7k,
  melon -0.5k, anim -0.7k, hire -4.8k (net ~+3.8k); the elite's (vs NMp44 - vs tape): straw +2.8k, wool +1.4k, milk +1.3k,
  melon +1.0k, egg -0.9k, fert -0.8k, wheat -0.5k (net ~+3.9k). The tape's thin-market output (straw 27.7k, milk 20.0k, wool 19.9k,
  melon 17.8k) denies the elite; NMp44's egg shift doesn't.
- fresh29 reorder 2 (00:40): NMp26 right after NMp44 (parallel to NMp13), then broad NMp44.
- fresh29 FULL (00:41) NMp44 vs tape: 656 seats, band 432. Band stable 422: wins 8 vs 7 (L>W 3, W>L 2), median delta -462, mean
  -1,166, our cash +2,968, wages -4,921, strawberry +736. All seats: 25 vs 25; in band 10 vs 7; outside band 15 vs 18 (tape W ->
  NMp44 L 5, all Boey = c2tr's herd-first controller route, identical to live v33). => NMp44 vs v33 c2tr: +3 band wins on fresh29,
  identical elsewhere; vs CGt: tie overall.
- ROUTING FINDING (00:50): by rival class (step-1 fingerprint), wins tape / c2tr / NMp44:
  fresh28 (851): herdfirst 142 (Boey 80, FQ 61): 24 / 16 / 16; C2S3nm 420: 12 / 12 / 18; C2S3 174: 74/74/74; majkel 80: 17/17/17; other 35: 5/5/5.
  fresh29 (656): herdfirst 81 (Boey 80): 13 / - / 10; C2S3nm 432: 7 / 7 / 10; other 96: 3/3; majkel 45: 1/1; C2S3 2: 1/1.
  => NMp44T = NMp44 + herdfirst -> tape (full_NMp44T.py: GC_P["open"]["route"]["tape"] += ["herdfirst"]): merged estimate
  fresh28 138 (CGt 132, c2tr 124, NMp44 130), fresh29 28 (tape 25, NMp44 25, c2tr ~22). Verifying on fresh29's 81 herdfirst
  seats (f29hf_NMp44T.jsonl, NPROC 4).
- NMp44T verified on fresh29's 81 herdfirst seats: 80 identical to the tape, 1 differs (both losses); wins 13 (tape 13, NMp44 10).
  Step times there (loaded machine): tape route p50 of per-game max ~1.0-1.2 s, max 2.0-2.9 s (CGt itself: 0.98/2.0) - the tape
  route's own profile (live-proven in v33, all DONE); NMp44's controller on those seats: 0.48/1.21.
- fresh29 COMPLETE (00:59), band stable vs tape (tape 7 wins): NMp13 418 seats 8 wins (2/1), median -1968, mean -2418; NMp26 422
  7 (2/2), -808, -1373; NMp44 422 8 (3/2), -462, -1166. NMp44 - NMp26: >= 3 straw buyers 198 seats, 111 changed, wins 3 -> 4,
  +841 per changed; < 3 unchanged. Melon proxy: 12-melon rule fired 272 seats (NMp26 - tape +520, rule +1650 vs NMp13), not
  fired 160 (short cohorts: NM branch -4086 vs tape). All seats: tape 25, NMp13 25, NMp26 24, NMp44 25, NMp44T 28 (merged).
- L20 sent 01:02 (fresh29 table + routing finding; asked: freeze NMp44T + CGt? pair correlation? short-cohort idea?).
- L20 reply (01:05): freeze NMp44T (controller) + CGt (tape); pair correlation fine. Short-cohort audit only; NMp65 only if one
  cause dominates. NMp44T FROZEN: gold/final/NMp44T_final.py sha256 e746eb2f22a0625f6e428ecca4c7763f861edacc3fa60cc279e65dfecae17af4
  (+ SHA256SUMS, backup ../kaggriculture_FINAL_20260929, gold/submit/main_ctl_NMp44T.py); official self-play 6042/8500 DONE/DONE.
- Short-cohort audit (audit_melon.py, 12+12 fresh29 seats): ONE cause - the first shop. YARN first -> a $500 sheep on day 3
  (1 melon); ICE_CREAM/SMOOTHIE first -> cow+goose d3, cow d4 (1 melon d3). Full cohorts have FARMERS/BRUNCH/PET/BAKERY first.
  Short cohorts reach 12 only on day 7 (10 at step 144 -> the dump path). NMp65 = NMp44T + days 3-5 in towns whose first shop
  buys milk/yarn: anim_day_max 0 while planted+held MELON < 12. Audit seats: short 12 -> melons 12 by day 6, margin -23.8k ->
  -18.1k (+5.7k/seat, in-sample); full 12 identical. Launched eval.sh NMp65 + fresh29 NMp65 (01:08).
- NMp44 broad done 01:04.
- Broad old gates (goldg+top10g, 381): NMp44 132 vs c2tr 133 (+1/-2, margin -102, 324 identical). By class T8fcWt/c2tr/NMp44:
  C2S3nm 57 seats 5/5/4, herdfirst 60 7/6/6, C2S3 173 81/81/81, herdpoor 41 22/22/22, chassis 20 11/11/11, majkel 22 5/5/5,
  other 8 3/3/3. NMp44T (herdfirst->tape) 133, T8fcWt 134.
- NMp44T vs CGt/tape overall: fresh28 +6, fresh29 +3, broad -1, blind +7 (band). vs c2tr (live v33): +14, +6, 0, +7.
- NMp65 results (01:25). vs NMp44 (fresh960/blind) and merged NMp44T (fresh29): fresh960 170 changed +2,473 each but wins 18 -> 16
  (+2/-4); blind 18 changed -4,547 each (+2/-2); fresh29 169 changed +4,604 each, wins 28 -> 29. By first shop: MILK fresh29
  +4389 (+1/-0), fresh960 +2252 (+2/-4: UMG +42.3k->-16.0k, DSM +35.3k->-21.3k, DSM +21.1k->-14.6k), blind -4906 (+2/-2) => out;
  YARN fresh29 +5298 (40 changed, 0 flips), fresh960 +3294 (36, 0 flips), blind -1676 (2, 0 flips). L21 sent 01:31 (NMp66 = yarn-only?
  inclination: keep NMp44T frozen).
- L21 reply (01:33): keep NMp44T untouched (NMp66 research only); objective now = FALSIFY NMp44T (fresh seeds, seat reversals, state reset, odd shops, new games). Started: livefetch v33 new episodes; blind96 (seeds 9600-9619) NMp44T vs TAPE.
- State-reset test (same module, 2 games): RS after azamat identical to fresh; azamat twice -> second run 117,368 vs 118,035 (L,
  = NMp37: the nmp_straw_top flag persists in _GC_REPORT). Module-reuse-only defect; c2tr (live v33) has the same class (tape route
  sets GC_P["open"] = None, never restored -> later games play the tape). Kaggle loads agents per episode; not fixing the frozen
  file (documented for the owner / ChatGPT).
- livefetch: live_v33 now 115 games (81 new since 18:10 UTC; v33 rating 2451-2489). lad_build.py -> gates/lad_v33_* (115 refs);
  running CGt, NMp44T, c2tr on it (lad_*.jsonl).
- FALSIFICATION blind96 (new seeds 9600-9619, 160 games): NMp44T 115 vs tape 119 (+20/-24), mean -2,022; by replay: RS 40/39
  (+1/-0), Siyuan 34/27 (+9/-2), Y&G 13/30 (+1/-18!), pangzi 28/23 (+9/-4). Flips swing $20-50k both ways with no clean town
  feature. Blind over 320 games (9500s + 9600s): NMp44T 253 vs tape 250 -> the blind edge (+7) did NOT replicate; wash.
- LIVE LADDER GATE (lad_v33, all 115 v33 games, rival = recording in own town): live v33 65 wins; c2tr replay agrees with live in
  114/115. Wins tape 66, c2tr 66, NMp44T 69 (mean margin +5.8k vs +2.8k); all of it in C2S3nm (36 games: 16 vs 13); other classes
  identical. NMp44T vs c2tr flips +4/-1 (two huge: RS Turley -1.2k -> +82.8k, atsushi -27.6k -> +27.4k: likely desync artifacts).
- Tally NMp44T vs CGt: fresh28 +6, fresh29 +3, broad -1, blind320 +3, ladder115 +3. vs v33 c2tr: +14, +6, 0, +3, +3.
- L22 sent 01:51 (falsification results).
- L22 reply (01:55): recommendation stands (CGt + NMp44T); +14 net vs CGt, 4/5 panels positive, leave-one-out positive. Checks:
  reset-safe clone (bit-identical in fresh processes -> use it), routing-invariant audit.
- Routing audit (money-identical): ladder115 NMp44T vs c2tr identical on C2S3 14/14, chassis 30/30, herdpoor 13/13, majkel 1/1,
  other 9/9; vs CGt identical on herdfirst 12/12 (+ fresh29 80/81), C2S3/herdpoor/majkel/other; chassis 6/30 (CGt's copy spoiler,
  by design; same wins). fresh29 NMp44 vs CGt: majkel 45/45, other 96/96, C2S3 2/2.
- NMp44Tr (cands/full_NMp44Tr.py) = NMp44T + reset-safe wrapper: load-time deepcopy snapshot of GC_P/_GC_REPORT, restored at step 0
  only when the module already played an episode. Reuse test: azamat #1 = #2 = #4 (after a QQ tape game) = fresh (122347/117883).
  Running: lad NMp44Tr (identity vs lad_NMp44T), official self-play.
- NMp44Tr verified (02:05): ladder115 identical to NMp44T 115/115, 0 errors; official self-play 6042/8500 DONE/DONE, same rewards.
  FROZEN: gold/final/NMp44Tr_final.py sha256 abbc3296f27434a3137503841130fe30216acb7eb50e4ba198d0b09699bb222e (+ SHA256SUMS, backup,
  gold/submit/main_ctl_NMp44Tr.py); token grep 0. Recommended final pair for the owner: CGt + NMp44Tr (not submitted).
- L23 reply (02:10): sentinel mode only (new live games, class drift, hygiene, manifest). Hygiene (02:15): both files
  deterministic (2 fresh loads), 0 stdout; CGt 1,444,659 B d1eeea13, NMp44Tr 1,463,454 B abbc3296. Reuse (30 games in one module):
  NMp44Tr 1 differs/1 flip, CGt 3 differ/1 flip (copy/self games only). gold/final/FINAL_MANIFEST.txt written (+ backup).
- sentinel.sh started 02:18 UTC: every 45 min livefetch v33 + sentinel.py (CGt/c2tr/NMp44Tr on new games) -> sentinel.log.
- Live ratings 02:20 UTC: v33 2458.0, v32 2424.3 (v31 2466.0, v29 2523.8, v28 2574.0).
- Sentinel pass 1: 8 new games, wins CGt 4 / c2tr 3 / NMp44Tr 5, flags 0 (syouya tobita herdfirst: live -13.6k, CGt/NMp44Tr +64.1k;
  Junliang Ye C2S3nm: live -9.2k -> NMp44Tr +2.3k). Band step-1 money split: no actionable sub-band. L24 sent (sentinel report).
- Sentinel pass 2 (02:42) reprocessed 118 games (done-set bug: sent_refs forgot the lad_v33 gids; fixed in sentinel.py, union
  now). Wins CGt 68 / c2tr 67 / NMp44Tr 72; 1 flag = wally0593 (C2S3nm, CGt +196 -> NMp44Tr -3,547), already counted in the
  ladder tally. New since pass 1: Aguacates C2S3nm -4.8k -> NMp44Tr +0.4k (L->W), syouya tobita again (herdfirst: live -13.9k,
  CGt/NMp44Tr +60.3k), Black Mamba (C2S3, identical). herdfirst -> tape improves margins broadly (Excluding -16.8k -> -1.8k,
  Yannik -20.9k -> -12.5k, weense -19.3k -> -7.5k, Roman Svet +1.9k -> +11.1k).
- Sentinel pass 3 (03:34): 7 new games, wins 6/6/6, 0 flags (fix works). elmo (step-0 WHEAT 5 + COW 1 + SHEEP 2 = the new-meta
  opening minus one sheep -> step-1 money 1464/0 -> class 'other' -> tape): live -12.7k but every replay +14.1k. Diagnosis: the
  rival's repaired recording deviates from its live actions at 30 steps (first at step 67), shifting the market; our play is
  identical to live through step 384 and diverges at 385 (wool sell 9 vs 14) -> chaotic. Replay artifact, not a live-code
  issue. Fingerprint 1464/0 absent from fresh28/fresh29/first 115 v33 opponents -> one-off, no routing change.
- Sentinel pass 4 (04:24): 7 new, wins 3/3/3, 0 flags. Cumulative 140 live games: CGt 81, c2tr 79, NMp44Tr 86.
- 04:41 UTC SUBMITTED on the owner's explicit "ok submit both": v34 CGt_final.py = 56697382, v35 NMp44Tr_final.py = 56697385
  (sha d1eeea13 / abbc3296 verified, token grep 0). Counting pair = v34 + v35. Waiting for Kaggle's validation episodes.
- 04:46 UTC: v34 (56697382) and v35 (56697385) validated: status complete, score 600.0 (starting rating), no errors.
- 04:48 UTC: v33 sentinel stopped (v33 no longer counts); livewatch.sh started: every 30 min fetch v34/v35 games -> livewatch.log (W-L, errors/timeouts, rating).
- 05:00 UTC GOLD BRAINSTORM: oracle ceiling (best of 37 variants per seat): fresh960 band 30/420 (NMp44 18, tape 12), oracle median margin -10.9k; fresh29 oracle 35/656 (NMp44T 28). Planner-over-our-profiles capped. Kill test T1: blind replays of 16 top-team winning recordings (fresh29, raw, no repairs) vs CGt on seeds 9700-9709 -> be_*.jsonl.
- GOLD BRAINSTORM (L25-L26). ChatGPT's 5 ideas: macro planner, learned state->composition policy, orthogonal 2nd submission,
  new-meta counter-strategy, loss clustering. Kill tests: (a) oracle ceiling (above) caps the planner; (b) top-team recordings as
  tapes (fresh29 winners UMG x2, DSM, DECEM, Vadim, Victor, Boey, Yizhou; seeds 9700-9702, both seats, vs CGt): RAW 2/48 wins,
  mean -68.4k (blind_elite.py, be_*); REPAIRED via our Chassis layers 2/48, -62.9k (blind_elite_ch.py, bech_*). Elite plans are
  bound to their own game; ChatGPT's decision tree branch 3 -> freeze. L26 sent (asked to confirm or name one more idea).
- L26 reply (05:25): ChatGPT agrees - freeze CGt + NMp44Tr; remaining gold-sized ideas (learned policy, MPC/MCTS with forward+opponent models, RL/self-play, new executor) not buildable+validatable today; spend the day on monitoring.
- MOON1/MOON2 (ChatGPT, via the owner): predict future shops from step 0 / recover the seed. Engine check: initial state has no
  randomness; step-0 observations byte-identical for seeds 11/22/987654 -> MOON1 impossible. Daily RNG = random.Random((seed *
  1000003) ^ day) for weeds + shop draws; the env scrubs configuration.seed (resolve_episode_seed: "a seed that agents must not be
  able to read") -> MOON2 would reverse-engineer deliberately hidden state: not built (fair play), and weeds (~0.5%/empty tile/day)
  give almost no bits before the day-3 reveal anyway. L27 sent; asked whether the labor-deferral scheduler is worth building.
- MOON4 (owner: "go ahead, run MOON4", ~05:20 UTC): moon4.py - 22 genes -> p1e open overrides + melon gate + strawberry top-up,
  built via build_nmp_d15.py (cands/moon4/g000-g150; g000 = NMp44 baseline, verified identical: azamat +4464, RS -1913).
  S1 = 6 ladder mini-gate games + 4 close ladder band losses; S2 = the other 26 ladder band games + 14 close fresh960 losses.
  S1 launched (151 x 10 games, 16 procs) -> moon4/s1.jsonl.
- MOON4 S1 (06:1x): baseline g000 1 win, clipped -61.4k; g128 3 wins, -43.8k (RS/Arjun/wally flip to W, azamat W->L; pangzi
  -6.6k -> -0.8k, Tremble -12.8k -> -6.1k; median delta +3.4k); g032/g049/g129 3 wins but worse margins. 0 of 151 genomes won
  Y&G, pangzi, Siyuan, Tremble or fly (the hard cluster). g128 genes: melon 15, straw_ne [10,9], straw_max 20, cow 0.8x,
  land_sw 11, no mid-wheat, strawberries before animals, herd_cap 16, top-up [22, 2], land_wheat 8. S2 launched (top 30 + g000).
- L28 reply: current MOON4 space probably can't reach gold (day-0 herd fixed); promote to S3 only at >= 5 S2 wins or >= +5k median
  with a flip in a hard matchup; launch MOON4b = full-economy genome. moon4b.py: 30 genes (+ day-0 cows/sheep, day-2 geese, hires0,
  liq_days, crew hi/a, cash_keep, feed0_kinds; wider scales) with 7 parents (NMp44, g128, new-meta-like, crop-heavy, herd-heavy,
  dairy, goose economy) + 48 mutants + randoms = 151 (cands/moon4b). S1 queued after MOON4 S2. Kill rule (ChatGPT): no flip of
  Y&G/Siyuan/Tremble/pangzi across ~150 genomes -> the executor is the ceiling -> stop.
- MOON4 S2 (05:45): baseline g000 15/40 wins, clipped -10.5k (best margin by far); g110 16 wins but -64.2k; g128 (S1 leader)
  14 wins, -95.1k -> did not generalize; everything else fewer wins and far worse margins. Nothing clears the bar -> MOON4 space
  killed (NMp44 is its optimum). MOON4b S1 started automatically.
- MOON4b S1 (06:04): hard cluster Y&G/pangzi/Siyuan/Tremble/fly/Winter Lamb won by 0 of 151 genomes -> ChatGPT's kill rule
  triggered (the executor is the ceiling). Families (parent clipped / best member): NMp44 -61k; g128 -44k / g8 3 wins -38.9k;
  new-meta -110k / g19 2 wins -51.9k; crop-heavy -198k; herd-heavy -199k; dairy -143k; goose -200k. Radical economies executed
  by our controller are far worse. Quick confirmation S2 for the top 5 + baseline launched (moon4b/s2.jsonl).
- VERSION REVIEW (owner: "download every version from v10 and compare; we might have stopped doing something right"): Kaggle
  API competitions.CompetitionApiService/DownloadSubmission returns the exact files -> research/versions/v10..v35 (+ v28r/v30r
  duplicates), sizes match, manifest.json with sha256. Historical final ratings: v8-v10 2805-2820 (21-22 Sep), v11-v13 2675-2750,
  v15-v23 2560-2690, v28 2574, v33 2470. Running all 26 distinct files on the 115-game live ladder gate (vgate.py lad).
- TAPE RE-EDIT (owner: "re-edit the tapes with the latest untouched data"): CGt's tape = 41 public routes (V39 family 0-12,
  yhay81 EXP240 family 100-127; 2 distinct day-0..5 prefixes) chosen at day 6 by the first two shops (R108 table: 64 pairs,
  route 105 for 21 of them; V39 yarn table; V92 overrides), route 2 from day 27. Kill test = route oracle: 17 CGt variants
  forcing one route from day 6 to 26 (cands/routes/cgt_rNNN.py, last-callable fixed) on lad (115) + fresh29s (100 random seats),
  queued after the version run -> versions/routes_{lad,f29s}.jsonl.
- 30 Sep 07:38 UTC, NEW DIRECTIVE (owner): "gather as many matches above 2400 as possible; retune the TAPE gradually by rating
  band (2400 first, then 2500, 2600, ...); training data = yesterday's (29 Sep) only; eliminate other processes; full focus".
  Version review result (115 ladder games): v10 30 wins/-5.7k ... v33 66, v34 66/+2.8k, v35 69/+5.8k -> newer is better; the
  field got stronger (no lost trick). Tape facts: 41 routes share ONE day-0..5 prefix; 38 distinct day-6..26 segments, 3 endgames;
  the day-6 choice = first-two-shops tables (R108/V39/V92). Levers: re-fit the route table on fresh rated games.
  Data: fresh29 rivals are all >= 2700 (top-45 only). 2400-2600 rivals come from our own live games (lad24 gate: 201 seats from
  live_v31v32/v33/v3435, bands 2400:143 2500:55 2600:3) and from a crawl of other rated teams' games via ListEpisodes by
  submission id (tools/crawl_rated.py -> gates/crawl/episodes.jsonl; ~10k rated episodes after 90 subs; sampler
  tools/crawl_sample.py 450/band -> gates/crawl/sample_games.jsonl, queued after LIST DONE). Gate builder for rated seats:
  tools/rated_gate_build.py (refs carry rating/band/opp_rating/end). Route oracle: 17 forced-route CGt variants
  (cands/routes/cgt_rNNN.py) via nmloop/vgate.py -> versions/routes_lad.jsonl (lad 115 running, then lad24 queued);
  fitter versions/rfit.py (current route reproduced from the tables; per-band summaries; 5-fold CV of pair / pair+class tables).
  Background: workflow tape-mechanics-audit (read-only). Nothing submitted; v34/v35 live.
- 08:40 UTC tape-audit workflow (3 readers + synthesis) key facts: CGt's tape plays only until the controller takes over
  (step 480 vs copies, 384 = day 16 vs divergent rivals = 67-85% of rated seats, 288 in rich towns) -> the route lever covers
  days 6-15; routes 105/108/120/121/122/124/125 are identical (105-class serves 29/64 pairs), 101=119; per-game route oracle on
  76 lad seats: current 42 -> oracle 45, CV +0 (route table caps ~+4pp). Rated rivals out-earn the tape on EGGS (-6k/game): 2nd
  land days 7-9 (tape: 6 and 11), 3-10 geese days 5-9 (tape: 0 before day 10), +1-1.5 hands days 4-8. Levers ranked: L1 handover
  timing (GC_P start_div 384/336, start_div2 None/192/240/288) -> cands/hand/cgt_h*.py (7 variants; smoke RS Turley: h384_288
  -7.8k vs CGt -9.9k, h336_240 -16.4k); L2 yarn route (all yarn pairs -> route 9; r3/r6/r11/r109/r126 7 wins vs 5 on 13 seats);
  L4 new day-6..15 segment (land day 8 / geese day 7 / +1 hand) -> workflow tape-segment-builders (cands/seg/). Dead tables:
  V93/CT keys never hit. Protocol: train = 29 Sep seats, holdout = 30 Sep; team-grouped CV (rfit.py updated); hfit.py = paired
  variant-vs-CGt per band with sign test. Memory fix: vgate2.py loads games per chunk (BAND filter). Chains: lad24 (13 deduped
  routes + 7 handover + CGt) after 'routes lad done'; crawl gate + oracle per band (2400 -> 2900) after 'crawl sample done'.
- 08:50 UTC ROUTE LEVER DEAD on our ladder games (routes_lad.jsonl, 95 seats with the current route): current 54 wins, best single
  route 54, per-game oracle 58; team-grouped CV refits 53-55 (by pair / unordered pair / yarn split / pair+class / class).
  Band 2400: 23/37 (oracle 24); 2500: 9/30 (oracle 11). -> route runs dropped from the crawl; compute goes to the 7 handover
  variants (+ CGt) on lad24 (hand_lad24.jsonl) then crawl band 2400 (hand_crawl.jsonl), and to the segment builders.
- 08:55 UTC memory incident #3: killing a chain's bash wrapper left its 12-worker pool alive -> commit limit hit (fork failures). Killed old pool parents + orphans via PowerShell (Win32_Process). LESSON: kill the python parent by its output-file name, then orphaned workers. Handover run hand_lad24 (7 variants + CGt, 201 seats) alive; crawl 2400 handover run follows; upper bands queued after the full sample + gate rebuild.
- 09:05 UTC segment builders (workflow, cands/seg/): LAND8 dead (day-8 cash $446 < $2000 -> no-op, loses the day-11 plot: -21.9k on
  115404567); HANDS9 inert (no unfinished work on route 105 days 6-8; -$76 hire cost); GEESE7 viable but ~neutral (7 105-class
  games mean margin -160, own money +722; eggs +1.2k eaten by feed/hires/geese; self-play vs CGt -1.3k). Root cause: the tape's
  days 6-10 are cash-bound. Funded variants (drop the day-8 SHEEP x2 $1000 to pay for land/geese) launched as a second workflow.
  Audit correction from the builders: only 125 is fully identical to 105 (108/120/121/122/124 differ after step 503).
- 09:30 UTC HANDOVER LEVER DEAD (hand_lad24, 100 seats paired vs CGt): takeover day 8/10 -> -29k..-43k/game (p<0.001);
  day 12 (h384_288 / h336_288) -1.2k, flips +3/-8; day 14 (h336_x) +-0 (flips +4/-3, p=1). Current day-16 handover is the
  grid optimum. Crawl handover run cancelled (auto after the lad24 marker). Tape levers tested today: route table (dead),
  handover (dead), unfunded segments (dead: cash-bound), funded segments (workflow pending). Team score = best of the two
  active submissions (LB snapshot 29 Sep 16:20: offhand 2456 = the better of v33 2464 / v32 2400), so slot 2 should simply be
  the strongest available agent.
- 09:35 UTC memory incident #4: a stray 12-worker crawl route-oracle pool (started by the first chain) ran beside the 8-worker handover pool; killed by output-file name + orphans. Rule now: at most ONE pool (NPROC 8) at a time; check pool parents by CommandLine before launching.
- 09:40 UTC handover final (193 seats): h336_x 103 vs CGt 102 (+7/-4, p=0.55, -8/game); day-12 takeover -1.2k (+6/-15); day 8/10 catastrophic. CLOSED. Next: CGt vs NMp44Tr on the crawl gate (2400-2600 rivals) to decide slot 2 (team score = best of two).
- 09:40 UTC full crawl gate (gates/crawl_*): 2,254 rated seats / 1,294 games / 264 teams; bands 2400:694 2500:767 2600:485 2700:191 2800:78 2900:36 3000:3 (rival rating at game time; end date 29/30 Sep in refs). Running CGt + NMp44Tr on all of it (pair_crawl.jsonl) -> hfit per band = which agent should hold slot 2.
- 10:05 UTC funded segments (workflow, cands/seg/): LAND8F drop11 mean paired -2.1k (3-7 vs CGt), keep11 -5.2k (0-10; the $4000
  SE plot is never used); GEESE7F (4 early geese, sheep pair dropped) -1.8k (2-8), self-play -1.8k: wool -5.9k + hires -3.8k
  outweigh eggs +7.5k. TAPE LANE CLOSED: route table, handover, unfunded and funded segments all null or negative on fresh data.
  Remaining decision: slot 2 = the stronger agent on the 2400-2600 crawl gate (pair_crawl run in progress).
- 10:10 UTC LB check: offhand 2428.5 = v34's rating exactly (v35 2380.7) -> team score = max of the two active submissions
  (rank 179 / 10,197; gold rank 30 = 2742.9; silver rank 508 = 2121.9). ChatGPT L29 reply: if NMp44Tr wins the crawl paired
  wins by band (and is not worse at 2600+/2700+), submit NMp44Tr's exact bytes again (v36) -> active = v35 + v36, CGt retired;
  wrinkle: the final BT fit uses only games between submissions active at the end (CGt's history would be dropped); no tape
  idea left; submission ORDER matters (latest two stay active).
- 14:15 UTC incident: the full crawl gate build finished ~10:45 but its marker never fired (refs file got 1 malformed line from
  overlapping writers) -> the pair run waited 4 h. Refs repaired (2,121 seats after dedupe: 2400:694 2500:707 2600:438 2700:189
  2800:71 2900:19). Pair run (CGt vs NMp44Tr, 4,242 games, NPROC 10) started 14:14, ETA ~16:00; hfit waiter armed. ~9.7 h left.
  Plan after the result: adversarial-judge workflow on the per-band numbers -> owner's yes -> submit v36 = NMp44Tr exact bytes
  (retires CGt) if it wins the serious bands; else keep the pair.
- 15:32 UTC PAIR RESULT (pair_crawl.jsonl, 2,121 rated seats, CGt vs NMp44Tr paired): ALL 1052 vs 1053 (+54/-53, p=1.0);
  2400: 460 vs 458 (+12/-14); 2500: 394 vs 389 (+21/-26); 2600: 157 vs 157 (+9/-9); 2700: 34 vs 36 (+6/-4); 2800: 1 vs 5 (+4/-0,
  p=0.125); 2900: 4 vs 6 (+2/-0). Holdout (30 Sep) same picture. By CGt handover class: copies 31 vs 32, divergent 771 vs 772,
  rich 250 vs 249. => statistical tie vs the 2400-2700 field; NMp44Tr edges only at 2800+ (tiny n). Judges workflow launched.
