# gold/top10 — working context (27 Sep 2026)

Goal: gold medal (top 30 of 10,063; cutoff ~2782 now) or top 10 (~2897). Team **offhand**, #97 at 2640 on 27 Sep 06:30 UTC.
Final submission deadline **30 Sep 23:59 UTC**, 5 submissions a day. Only the **latest 2 submissions** are tracked and used
for the final leaderboard (a Bradley-Terry tournament on games played ~1-15 Oct). Rating counts wins only, not margins.

Submitted: v23 = m3, v24 = m5 (`gold/submit/main_ctl_mkt5_m7.py`), **v25 = sf8** (`gold/submit/main_ctl_sf8_lean.py`, sha256
8b899b2f..., submission 56600788, 27 Sep ~07:20 UTC). Active pair now v24 + v25.

## Environment (Windows, Git Bash)
- Worktree: `C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg` (branch `gold/top10`). Run from here.
- Python: `../.venv/Scripts/python.exe` (3.12, kaggle-environments 1.32.7). Prefix commands with `PYTHONIOENCODING=utf-8`.
- The harness hardcodes `/home/user/kaggriculture/...`; a directory junction `C:\home\user\kaggriculture` -> this worktree
  makes those paths resolve. Do not rewrite those paths.
- git core.autocrlf=true: working files are CRLF. Hash files with `tr -d '\r' < f | sha256sum`.
- 16 logical CPUs shared by everyone. Worker count per run = env `NPROC` (pinned4.py, elite_gate.py, batch4.py).
  Unless told otherwise use `NPROC=3`. Never start more than one heavy run at a time per agent.
- Bash calls time out at 10 minutes. Long runs: `nohup ... > log 2>&1 &`, then poll with short commands
  (`wc -l out.jsonl`, `tail -n 3 log`), e.g. `timeout 500 bash -c 'until [ $(wc -l < out.jsonl) -ge N ]; do sleep 20; done'`.

## Builds
- **Lean sf8** (the submission): `gold/top10/lean_sf8.py` (CRLF copy) = `gold/submit/main_ctl_sf8_lean.py` (LF). Most switches
  are folded into constants; `GC_P` still exists (dict literal near line 6584 + `GC_P.update({...})` next line), and new
  code can read `GC_P.get('knob', default)`. Changes to the lean file are made by small patch scripts
  (pattern: `gold/patches/lean_patch_wf.py`, `lean_patch_cg.py`: read file, `str.replace` an anchor, assert it matched,
  write out). Copy takeover day is the literal `start = 576` in `agent()` (+ `day == 576 // 24` in `_route_and_hire`).
- **Full sf8** (knob exploration): `gold/top10/full/` holds `ctl.py` (merged controller + `m5_sells_first.patch`),
  `base_m7_t4.py`, `cfg_m5.json`, `bm5.py`. Build: `cd gold/top10/full && ../../../../.venv/Scripts/python.exe bm5.py out.py '<json>' ctl.py`
  with the sf8 knob set
  `{"sells_first": true, "sells_first_chassis": true, "sells_first_slots": true, "sells_first_sort": true, "cash_guard_min": 5,
    "v233_wool_first": true, "div_over": {"mkt_dp_d29": true, "final_sell0": 0, "final_cap": 21, "mkt_dp_cap": 30}}`
  plus overrides (`div_over`/`rich_over` merge key by key). New controller features go into `gold/top10/full/ctl.py`
  behind a knob that defaults off (so sf8 plays unchanged), then into the lean file by a patch script.
- Controller structure, engine facts and every rejected idea: `gold/README.md` (this session's line) and
  `gold/elite/README.md` (the other session's), `gold/submit/SUBMIT_THIS.txt`. Read the relevant sections before
  proposing a knob: most obvious ideas were already measured and rejected.

## Gates (paired: same games, candidate vs baseline)
| gate | command | size / cost at NPROC=14 |
|---|---|---|
| live191 | `gold/harness/pinned4.py gold/top10/gates/live191.json 288 candA,candB out.jsonl offhand [max]` | 191 live v23/v24 games (26 Sep), from day 12; ~8 min/cand |
| pin249 | `gold/harness/pinned4.py gold/top10/gates/pin249.json 288 ...` | 249 older recorded strong-team games; ~10 min/cand |
| 2800+ | `gold/harness/pinned4.py moon/strong2800.json,moon/strong_new.json 144 ...` | 179 games vs 2800+ rivals, from day 6 |
| elite | `gold/elite/elite_gate.py run moon/elite/games_2026-09-20.jsonl.gz gold/elite/elite_gate_refs.jsonl cand out.jsonl` | 210 repaired elite seats (7 teams x 30) in their towns; ~12 min/cand |
| closed loop | `gold/harness/batch4.py cand opp 6100-6299 out.jsonl 01` for opp in `arena/cand/omw_v15a.py`, `arena/cand/pub_metav4v13.py`, `arena/cand/pub_smallershock.py` | 1,200 games; slow (~1.5 h/cand); `paired.py base new` |

| **top10g** (new) | `gold/elite/elite_gate.py run gold/top10/gates/top10g_games.jsonl.gz gold/top10/gates/top10g_refs.jsonl cand out.jsonl` | 270 repaired seats of the current top 10 (30 each: DSM, Boey, Vadim Vasilenko, M&M&P&Q, Majkel1337, DECEM, Mother-Goose, Fourth Quadrant, Azat; no KawattaTaido in the data), 25-26 Sep games |
| **goldg** (new) | same with `gold/top10/gates/goldg_games.jsonl.gz goldg_refs.jsonl` | 111 seats of gold-zone teams (ranks 12-25: 吃白饭的大肥鱼, THIRD FARM CLUB, mtmr_s1, Kaggledew Valley, TheEggman, Yizhou), 25-26 Sep |

- MEMORY: 15.6 GB RAM, 12 cores / 16 threads, shared. Workers must not load whole corpora: pinned4.py now splits each
  corpus into `<corpus>.d/<i>.json` one-game files in the main process (first run of a corpus writes them).
- `PIN_GIDS=file_with_ids` restricts pinned4.py to those game ids (subset runs). Rows carry `gid, m (margin us-them), led_us, led_them, tel`.
- Live split by opponent group: `SP=gold/top10/gates ../.venv/Scripts/python.exe gold/harness/live/livecmp.py base.jsonl new.jsonl`
  (reads `gold/top10/gates/live0926/games.csv`: groups copy / annex / own, rating <2600 / 2600+).
- live191 baseline rows for lean sf8: `gold/top10/gates/live_sf8_copyday.jsonl`, cand `gold/top10/lean_sf8.py`.
- Live-game tools: `gold/harness/live/` (lost_report, crop_trace, prem_timing, day_fills, pin_probe, early_scan);
  ledgers/traces: `gold/harness/ledger_replay.py`, `farm_trace.py`, `plant_trace.py`, `gold/leak.py`.
- Replays of the 191 live games: `replays/live_0926/` (gz raw Kaggle replays, `analysis/LOSSES.md`, `analysis/games.csv`).

## Daily top-tier games (Kaggle's own daily datasets)
`kaggle/kaggriculture-episodes-YYYY-MM-DD` (~600 games/day among the ~50 best teams). Compact copies via
`moon/elite_fetch.py list|fetch DATE`: 20-22 Sep in `moon/elite/games_*.jsonl.gz`; 23-26 Sep being fetched into
`../kaggriculture/moon/elite/games_2026-09-2[3-6].jsonl` (27 Sep appears after ~00:10 UTC 28 Sep).
Current top 10 (27 Sep): DSM 3102, Boey 3029, Vadim Vasilenko 2994, M & M & P & Q 2985, Majkel1337 2969, DECEM 2949,
KawattaTaido 2922, Unknown Mother-Goose 2921, Fourth Quadrant 2906, Azat Akhtyamov 2897. Full LB: scratchpad lb.csv.

## Results log (27 Sep)
- v26 = sf8 + copy takeover day 22 (`gold/submit/main_ctl_sf8c22_lean.py`, submission 56603319). Day 22 vs sf8: live191
  +$412 +- 96 (154 -> 157), 2800+ +$263 +- 91, pin249 +$299 +- 85 (195 -> 198); closed loop +$477 / +$132 but -9 net close
  wins in 400 games vs old public agents. Day 23: live +7 wins, 2800+ -2, pin249 0, closed loop 0.
- sf8 on the new gates: goldg 37% (-$2,271 a seat), top10g 23% (-$7,327). Gap per seat vs gold zone: tomato -$5.1k, egg
  -$4.7k, wheat -$2.3k; vs top 10: wheat -$7.4k, egg -$4.8k, carrot -$2.1k. Melons +$5.6-6.3k for us.
- Ablations on goldg (Kaggle, rows in gates/kout/): market programme off -$1,867, s2t off -$1,129, melons off -$523, herd off
  -$386, takeover d15 -$341, d18 +$212 (wins flat), care floor 8 / rival weight 2 / tick defer: 0. Everything we have pays.
- Round 2 (goldg/top10g): s2t on days 6/7 or by town or one-buyer towns: -$131 to -$569; eggs / tomatoes in the market
  programme: +$57 / -$146 (goldg), -$26 / +$66 (top10g); herd margin 1500: +$128 goldg, +$7 top10g, -$7 eg0920.
  Knob tuning is saturated.
- Egg gap is structural (elites ~5.5 geese by day 12, bought days 2-11; controller-day geese lose on wages and $40 wheat).
- Leak scan of sf8 (191 live games, S=0): night-drop discards ~$988/game, missed water bonus $380, capped animal product $289,
  care bonus lost $348, thirst/rot ~$200. Fix `drop_refill` (mid-route shed drops no longer empty the wheat a hand still
  needs for later FEEDs): live191 +$273 +- 103 (154 -> 158), pin249 -$11 +- 85; `gold/top10/cands/lean_sf8_escapes.py`.
- Kaggle compute: `gold/top10/kaggle/` (pack_gates, mkkernel, kqueue + kinbox.txt). Kaggle rows are bit-identical to local.
  Max 5 concurrent batch CPU sessions (4 cores each); the TPU queue did not start in 2+ hours.

## 27 Sep evening
- v27 = T5 submitted (gold/submit/main_ctl_T5.py): vs v26 live191 +$1,625 (157 -> 169), pin249 +$1,608 (198 -> 209),
  2800+ +$1,722 (106 -> 118), closed loop +$1.25-1.46k all three opponents; vs sf8 goldg 37% -> 46% wins.
- T6 = T5 + s2t_ext (day-11 partial strawberry->tomato, 1-strawberry-shop towns with a tomato buyer): +$79 to +$586 on every gate.
- Copy takeover day on T5: earlier is better now (live191 d19 +$311, d20 +$317, d21 +$154 vs d22; d24 -$429); live0927 d20 +$406.
- Controller audit (5 areas): the same pickup-reserve bug found 5 times (market sells the WHEAT/FERTILIZER today's queued PICKUPs
  need; day 28 reserve 0): market_fix1 +$163 +- 40 live; market_fix2 +$19; d28feed_fix +$178 +- 25 (169 -> 171); mtrim_fix +$185;
  plant23_fix +$82 (fired); handover_fix1+3 small +. All merged into gold/top10/full/ctl_top3.py (verified line by line; T6c == T6).
- T7 = T6 + copy day 20 + market_fix1/2 + d28feed + mtrim + plant23 + handover_fix1/3: gates running (Kaggle r12*).
- Research (gold/top10/research/): under T5 the post-day-16 gap vs the gold zone is closed; what is left is pre-day-16 against
  "opening winners" (Boey, Fourth Quadrant, 吃白饭的大肥鱼, Yizhou, THIRD FARM CLUB: early SW land, geese, dense wheat) and eggs.
  Round-3 agents: no-yarn herd swap, premium-first tape delivery (copy ties), labour packing.
- Pitfall: a merge resolver that writes CRLF on Windows made git merge-file duplicate the whole file; write LF (newline='').

## Leads open on 27 Sep (from the other session's last hours, code lost with its container)
- Copy takeover day 22 instead of 24: +$760 +- 163 a game on the 105 live copy games (93 -> 96 wins), measured on sf6.
  Being re-measured on sf8 (days 21/22/23) by the main session.
- 11 divergent live games lose sheep right after the day-16 takeover (escapes), e.g. vs XJHya233.
- Night-drop shed overflow: ~$880 a game of goods discarded (29 of 106 games > $1k), days 23 and 26 mostly; one game
  (Ryui68925, day 26) harvested 218 units against a 98-unit night room with every hand booked to hour 23. A forced
  courier and an hour-23 room sale both failed to pay; cheaper idea: skip harvests/pickups that would only be discarded.
- Early wool sale variants (ces15/ces25) rejected.

## 28 Sep: live loss analysis of v27 (T5) and v28 (T8)
- Data: `gates/live0928_T5T8.jsonl` (all live games of v25-v28), `gates/t5t8_all.json` (175 T5/T8 games),
  `gates/t5t8_anatomy.jsonl` (replays: farm snapshots + revenue by product/window; 175/175 reproduce exactly, no timeouts),
  `gates/t5t8_shops.jsonl` (shop unlock days, `tools/live_shops.py`).
- New live gate: `gates/lv0928hi.json` = 253 live games vs 2500+ (v25-v28 seats), Kaggle dataset `kagg-live-0928`
  (gates.bin, pinned gates lv0..lv4, S=0). Kernels must attach it instead of kagg-gates-0927 (both hold gates.bin); kqueue
  inbox lines now take a 4th field with the dataset list.
- From step 0 on those 253 games: T8 vs T5 +$1,827 a game, wins 128 -> 143 (+16/-1); v23 m3 vs T5 -$3,000 (104 wins).
  Live fits (k=100): T8 2602 +- 40 (31 games vs 2000+), T5 2566 +- 20. Refitting against the opponents' current LB scores gives the same
  numbers, so climbers are not what drags our rating.
- Losses vs 2500+ (T5 49, T8 12): own-plan rivals 31-54 (36%), rivals with the same herd at day 16 14-7.
  - Rivals with SW land by day 9 10-20, 5+ geese at day 12 15-22, 20+ animals at day 16 10-24. On exactly these games T8 = T5
    in the counterfactual (10-20, 15-22, 11-23): the late-game controller does not reach them.
  - Our herd is frozen at 17 from day 12 (tape); the big-plan rivals keep buying (19 -> 21 in T8's losses).
  - Eggs -$2.5-3.9k in every group; strawberries -$3-5k in days 12-19; T8's losses also milk -$5.6k (cow-heavy rivals).
  - Tomato buyer (pizza shop / farmers market) first opening on days 12-19: 8-14, margin -$4.1k, tomatoes -$3.5k. The rivals plant
    ~8 tomato tiles by day 20, we plant 0.6. w2t never fired: those rivals are step-2 copies (div2 off). `full/ctl_top5.py` =
    ctl_top4 + `w2t_all`; candidates TWa (w2t days 12-15), TWb (days 12-19, 4/day, 16 total) are on test (kernels kagg-tw-a/b).
- v23's own 191 live games (live191, 26 Sep) from step 0 on Kaggle: m3 reproduces its 152 recorded wins exactly. T5 would win
  171 (+$2,750 a game), T8 176 (+$4,355). The replay gate ranks T8 > T5 > m3 on both live sets; v23's higher live fit (2634) comes
  from 26 Sep games. Live fits by time third: v23 flat 2632-2639 on 26 Sep; T5 2601/2559/2551 and v26 2638/2573/2608 on 27 Sep
  (overlapping windows, equal within noise). Most likely the 2600 band got stronger between 26 and 28 Sep (not provable).
- Tomato test on the 253-game live gate (lv0-4, from step 0, vs T8s = T8 rebuilt on ctl_top5, identical sha): TWa -$470 +- 339,
  wins 143 -> 146; TWb -$399 +- 176, wins 143 -> 145. Money negative, the win change is within noise: rejected. Our tomatoes
  share the book with the rival's and lower both prices, so copying their tomato plan does not win those towns back.

## 28 Sep 08:30 UTC: opening-controller line, corrected baselines (session "opening")
- WARNING for anyone pairing candidates against the live rows in `gates/kout/kagg-lv0928-*/rows_lv*.jsonl`: those files
  hold T5, T8 and m3 rows for every game (`cand` field). Pairing by gid without `cand == 'T8'` mixes the baselines; the
  hf line's "+$15k a game on live" was that artifact plus ~8% collapsed rival tapes (`them < 75%` of base).
- Against the true T8 rows, hf s2 on 147 non-collapse live games: +$371 +- 733, wins 90 -> 89. By rival lineage (step-0
  orders, `research/opening/rivalclass.py`): chassis copies 48 -> 46, C2S3 copies 13 -> 19, herd-first 23 -> 19.
- Rival lineages are identifiable at step 1 from public money/hands: the C2S3 lineage (9 of the top 10) holds $2,460 or
  $960 with 0 hands; chassis copies >= $2,985 with 0 hands; herd-first (Boey/FQ/TFC/CBF) 3-5 hands and <= $1,600.
  `full/ctl_op.py` routes at step 1 (`open["route"] = {"tape": ["C2S3"]}`): exact T8 against listed lineages, the
  opening (started at hour 1) otherwise. Verified byte-identical to T8 on all C2S3 seats (Kaggle rs2 rows).
- Routed s2 (`cands/full_OP_rs2.py`) on Kaggle: live 253 -$733, wins 143 -> 132; goldg 58 -> 42 (CBF 8 -> 4, TFC 12 -> 5,
  Kaggledew 11 -> 6); top10g 73 -> 68 (Majkel 7 -> 3, FQ 2 -> 1). The opening branch loses on melons (7 day-0 melons and
  a late day-10 dump: 27 of 42 units sold on day 10 vs the tape's 60 of 72 by hour 14), wages (+$3-4k) and strawberries.
- Tools: `research/opening/` (mk.py builds `cands/full_OP_<name>.py` from `full/ctl_op.py`; diag.py; live.sh + lpair.py on
  `gids_live51.txt`; c2s3.sh = 24 C2S3 elite seats through elite_gate.py; kloop.sh runs a separate Kaggle queue).
- Opening-clone workflow (wf_356cdc71-afc) finished: both clones ABANDONED (details in research/openmine/hf and sf).
  - Herd-first s2 matches Boey/FQ/TFC's land days, herd and crews, but loses to T8: elite gates -$7.5k (wins 131 -> 46);
    live 2500+ from step 0 about even (+$371 +- 733 without rival-tape collapses).
  - Strawberry-first c7 (CBF): goldg -$7.7k, top10g -$12.7k, live -$2.9k (wins 92 -> 59).
  - Both lose on DENIAL. T8's early cows (days 2-3), day 8-9 sheep and 12 day-0 melons sell first and depress the rival's
    milk/wool/melon prices; with the clones the rival earns $3-12k more. CBF itself wins only 32% vs the top 50.
- care_eve_fix (found by the clone work): on an animal's production eve, CARE was skipped when the banked bonus was full. The
  engine consumes the bonus at night and then adds today's CARE for the next batch (_daily_refresh_animals), so the CARE pays.
  Ported as `full/ctl_top6.py` (ctl_top5 + care_eve_fix knob). T9 = T8 knobs + care_eve_fix (cands/full_T9.py; differs from
  T8x = T8 on ctl_top6 only in the GC_P.update line). Clone-agent numbers for the same fix: elite +$196 +- 46 (131 -> 134),
  live +$221 +- 57, rich towns +$1.0k. Full gates for T9 on Kaggle: kagg-t9-a..e.
- Opening-branch variants on the 24 herd-first elite seats (paired vs T8 -5,839; hf s2 -10,150): e (rs2 + straw ne [8,7]
  sw [9,6,-0.25] + 11-hand cap) -10,361 (5 wins = T8's 5); e12 (12 day-0 melons, 2C2S) -12,076; f (mid-day melon top-up +
  SW tomatoes) -11,930; g (force_first every day) -24,866 (50k unserved visits); w1 (crew below 1) -11,283; m1/m2/m4
  (melon-day pass: melon harvests first, forced drop, sell at once, one tile per hand) -10,694/-10,694/-11,483: the day-10
  melon lots still land at hours 10-19 (2-3 tiles from the shed, water + harvest, walk back), so the 7-melon dump cannot
  win the race the tape wins with 12 melons and 60 units sold by hour 14. e on Kaggle: goldg 58 -> 47, top10g 73 -> 66,
  live 253 trimmed -$761 (143 -> 141). Nothing in this line beats T8 on the corrected baselines.
- Final tally of the opening-branch knobs on the 24 herd-first seats (delta vs e = rs2 + straw + 11 hands): s1 (more
  strawberries) -1,478 and live 29 -> 25; w1 (crew below 1) -922; w2 (10-hand cap) -785 (milk/wool chores slip); m4 (melon
  spread) -1,123. e stays the best opening variant: live 253 -$761 trimmed (143 -> 141), goldg 58 -> 47, top10g 73 -> 66.
  The line is parked; the step-1 router in full/ctl_op.py stays usable for any lineage-specific opening or tape.
- Melon flood (28 Sep 10:00-12:30 UTC, session "opening"): the melon book is quadratic above the base stock and only the
  town centre absorbs melons, so a first seller with 84-120 units strips the rival's melon income. Measured on the 24
  herd-first seats vs e: 20 day-0 melons (2C1S) melons +$5.2k for us / -$6.7k for the rival, but the 20 tiles fill NW, no
  animal can be placed until day 12 and the rival's uncontested milk/wool books give it +$16k (mf1/mf3: -$11k to -$22k
  vs e). 14 melons with 2C2S (mf4-mf9): melons +$2.3-2.7k / rival -$3.4-3.8k, but the 8 day-0 wheat tiles are gone, feed is
  bought for cash and the day-3 denial cow slips to day 4-6 (rival milk +$1-7k), geese starve under a strict cow-first
  order (eggs -$4k): best mf9 -$6.9k vs T8 (4 wins), live 21 -> 14 of 38. Execution fixes that work and stay in
  `full/ctl_op.py` (`open["melon_day"]`): harvest every ripe melon on day 10, one melon trip per hand before any second
  trip and before the wheat pickup, per-trip shed drops, sell at once, crew forced to 11 with cash kept on day 9
  (`keep_eve`): 66 of 84 units sold by hour 13 (the tape: 60 of 72 by hour 14).
- mf10 (melon trips outrank the route cap, one per hand first): the dump is now complete on day 10 (78 of 84 units, $16.9k
  vs the elite's $7.6k) and still -$8.3k vs T8 on the 24 seats; live 51: chassis copies 16 -> 3 wins (the copy runs our
  tape and its milk/wool/strawberry books go uncontested, +$11k for it). The flood cannot be combined with the tape's
  denial herd from $3,000 of day-0 cash; the opening line is closed unless the tape itself gains melons.
- The C2S3 lineage's own plan (66 rival-side day logs in `research/openmine/hf/out_T8oth.jsonl`, session "opening"):
  strawberry-first: 2C3S + 10 wheat + 5 melons day 0, +3.6 melons day 1, 8.4 NW strawberries by day 4, no animals days 1-5,
  day-6 wave from 18 wool (NE + 3.4 cows + 1.6 geese + 1.3 sheep + 7 strawberries), SW day 9 (79%), SE day 10 (53%),
  tomatoes 2.5 -> 11.5 over days 10-16, herd ~20 by day 12, cash $36k at day 16 and $108k at day 29 (ledger: straw 27.9k,
  milk 23.8k, wool 22.6k, fert 12.5k, wheat 12.0k, melon 11.2k, egg 9.0k, tomato 7.9k, carrot 6.6k). Public notebooks: none
  of the 48 pulled so far carries this opening (all strong ones are later versions of our own chassis lineage); a sweep
  of all 442 competition notebooks is running (`research/opening/pubsweep.py`, `../pubnb/_sweep.jsonl`).
- "Copy the top players" (28 Sep 13:00-16:00 UTC, session "opening"): (1) all 442 public competition notebooks pulled,
  214 agents extracted and fingerprinted (`research/opening/pubpull.py`, `pubextract.py`, `pubsweep.py`, sources in
  `../pubnb/`): none carries the C2S3 opening; the strong public agents are later versions of our own chassis lineage and
  lose to T8 on our gates (2945 Farm median -$8k on the 24 herd-first seats, 1 of 22 live copy games; v41 -$17.6k;
  2965 Master Engine -$14k; Shepherds Ledger -$14k; the two other lineages -$35k to -$39k). No top-10 member publishes.
  (2) the lineage's day plan imitated on the opening controller (`full_OP_cs1.py`, `cs2.py` = strawberry-first schedule,
  SE dropped, wheat cap 28, harvest-first passes for melon/wool/milk days): cs2 -$14.1k vs T8 on the 24 herd-first seats
  (0 wins), -$6.5k on 24 C2S3 seats (T8 12 wins -> 5), live 51 -$6.5k (29 -> 11 wins; chassis copies 16 -> 4). The
  execution lags the plan by 1-2 days at every stage (seeds, the day-6 wave, SW) and the rival's books go uncontested.
  Elite README section 4 already showed recorded routes do not transplant. The opening line is closed.

### 28 Sep, evening: the mirror oracle (copy the rival's opening), `research/opening/mirror_test.py`
Question: if our seat played the rival's own recorded opening (days 0-15) and T8's controller took over at day 16, would we
beat T8? Same town, rival pinned to its recording; our seat replays the rival's unit actions per unit with cursors, market
orders from the recorded successful outcomes; PLANT/BUILD on a weed tile digs first; no emergency sells (they dump the feed
wheat and the cows escape: the collapse seen in every earlier run). Modes: MSHIFT=0 same-step copy (an ideal predictor,
not playable), MSHIFT=1 one step behind (what a live mirror could do at best).
- Same-step copy: day-16 cash identical to the rival's on 27 of 28 seats. Then T8 from day 16:
  vs 吃白饭的大肥鱼 (6 seats): -$318, 2 wins (T8 itself: +$85, 3 wins). From an identical farm our late game only ties theirs:
  T8's late-game edge is largely complementarity (we sell what they do not); copying their farm removes it.
  vs Boey + Fourth Quadrant (16 seats): +$5,268, 7 wins (T8: -$11,172, 0 wins); +$16.4k delta. The herd-first top-10 farms
  are worth ~$16k more than the tape's by day 16 in their towns and T8's late game holds from there.
- One step behind (the honest live mirror): total collapse (day-16 cash $0-3k). Units reset to the spawn at the day
  boundary, so a unit's hour-23 action is lost every day; in the elite openings those are PLACE/PLANT actions that the plan
  never repeats (day 0 ends with one cow unplaced, one melon and three wheat unplanted), and the deficit compounds.
  A live mirror would have to be a state mirror (make our tiles match theirs with our own routing), i.e. the opening
  controller with the rival's farm as the target: its execution lag is the thing that lost every controller opening.
- The tape-plus line (other session, `research/openmine/tp/`): TP_A3g/TP_A31g live159 +$0.7-0.8k (95 -> 103 wins), elite
  gates about neutral; the B variants lose. T5 vs T8 on the 253 live games: T5 -$1,827, wins 128 vs 143 (T5 is the weaker slot).
- TP_A31g (tape-plus: nw4=3, ne6+extra, fert_keeper; `cands/full_TP_A31g.py`) gated from step 0 against T8 (28 Sep late):
  live 253 +$825 +- 195 (median +$283, wins 143 -> 154, flips +14/-3; every lineage positive: chassis +$375, C2S3 +$652,
  herd-first +$1,650); 2800+ (S=144) +$96 +- 49 (128 -> 130 of 149); goldg 111 -$45 +- 136 (58 -> 55); top10g +$131 +- 101
  (53 -> 54 of 236); pin249 identical (blind, starts day 12); gc_errors 0. Candidate to replace the T5 slot (T5 is -$1,827 vs T8).
- v29 = TP_A31g submitted (submission 56638568, `gold/submit/main_ctl_TPA31g.py`, user-approved). Final top10g: 270 seats
  +$55 +- 94 (73 -> 74). The counting pair is now v28 = T8 and v29 = TP_A31g; T5 (v27) no longer counts.

### 28 Sep, night: Codex audit of the opening (kaggriculture_early_game_audit_20260928.zip, copied to cands/full_CX_ewave.py)
Mechanism found: on days 6, 8, 9 the opening controller bundles HARVEST with FEED/CARE; the wool/milk reaches the shed only
at the night drop, so the day-6 wool ($3.9k) funds NE and its planting a day late. Their patch (`_liq_vrp`/`_liq_compile`
on OP_e + T8 continuation) sends short harvest-and-deliver trips first and sells before the input pickups. Their numbers vs
T8: live 253 143 -> 161 (+$3,125; screened 141 -> 155, +$1,081), goldg 58 -> 47 (-$1,555), top10g 73 -> 78 (+$412),
reacting T8 self-play on 6 new towns 4W/8L, T5 10-2. Engine facts they corrected: eggs are shop products (BAKERY, BRUNCH_SPOT);
the town centre consumes every product except fertilizer (our notes had it backwards). Being re-measured on our harness.
- Verification on our harness (28 Sep night): goldg 111 seats reproduce Codex's rows exactly (-$1,555 +- 1,019, 58 -> 47;
  吃白饭的大肥鱼 -$6,942 8 -> 3, Kaggledew Valley -$2,830 11 -> 6, C2S3 seats identical because the router keeps T8's tape), so
  their live/top10g numbers can be taken as measured. The mechanism does not apply to the tape: T8 drops the day-6 wool at
  hour 5, sells at hour 6 and buys NE the same afternoon (htrace on 113065970 seat 1). Reduced closed loop vs omw_v15a
  (60 seeds x 2 seats, partial): -$46 +- 617, 42 -> 41. Not a slot candidate; T8 + TP_A31g stay.
- Codex candidate, full verification: live 253 reproduces their rows exactly (+$3,125, 143 -> 161; screened +$1,081, 141 -> 155;
  chassis copies 68 -> 79 with our cash +$953, C2S3 22 -> 22, herd-first 36 -> 37 screened). vs TP_A31g on the same games
  +$2,300 +- 973 (154 -> 161). BUT the reduced closed loop (reacting public chassis agents, 60 seeds x 2 seats) says the copy
  gain is a recorded-opponent artifact: vs omw_v15a -$1,242 +- 468 (T8 120 wins -> 112), vs pub_metav4v13 -$2,132 +- 474
  (120 -> 110). With goldg 58 -> 47 and Codex's own 4W/8L vs a reacting T8, e_wave is rejected as a slot candidate, and a
  "chassis -> e_wave, else TP_A31g" router with it is dead for the same reason. The same closed loop is being run for v29.
- v29 (TP_A31g) on the same reduced closed loop vs T8: omw_v15a +$135 +- 141 (120 -> 120 wins), pub_metav4v13 -$12 +- 140
  (120 -> 120): neutral against reacting copies, no regression. Pair stays v28 = T8, v29 = TP_A31g.

### 28 Sep 13:00-15:00 UTC: building toward a controller opening (user's call: no more recordings at the core)
Tooling: `research/opening/lagdiag.py CAND GID SEAT [D1]` prints a per-day table (cash, hands, idle unit-hours, first sale /
land / plant hours, seeds unplanted, unsold shed, unfed animals, both farms' tile census). Codex's delivery-first patch is now a
knob in `full/ctl_op.py` (`open["liq_days"] = [6, 8, 9]`); `open["melon_sell_now"]` sells shed melons at once (no effect: the
melons reach the shed late, hour 13, the hold was not the cause). Build: `mk.py NAME cfg_X.json '{overrides}' '{"care_eve_fix": true}'`.
Panel = 24 herd-first elite seats (Boey 8, FQ 8, TFC 8), paired vs T8 rows, rival-collapse screened:
| cand | config | delta | median | wins T8 -> c | our cash vs T8 | elite cash vs T8 |
| e | cfg_e (controller, no patch) | -$4,522 | -6,064 | 5 -> 5 | -4,686 | -164 |
| eliq | e + liq_days (= Codex e_wave, identical results) | +$2,329 | +655 | 5 -> 9 | -1,524 | -3,853 |
| f7 | eliq + abs_last 8 (animals before strawberries through day 8) | +$2,145 | -587 | 5 -> 9 | -946 | -3,090 |
| f6 | eliq + elite day 0 (2 cows 3 sheep 7 melons 8 wheat) | +$386 | -2,506 | 5 -> 5 | +973 | +588 |
| f2 | eliq + melon_day dump | +$643 | -3,516 | 5 -> 9 | -909 | -1,552 |
| f4 | f2 + late strawberry tranche (max 42) | -$3,362 | | 5 -> 4 | | |
| f1/f5 | tape day 0 (2C2S 12 melons) on the controller | -$8.1k / -$8.7k | | 5 -> 3 | | +6-7k for the elite |
Reading: the controller's own cash is now within $1k of the tape on these seats; its wins come from denial of the herd-first
elites' books. The controller cannot run the tape's melon portfolio (herd stalls). Running: f10 = f6 + abs_last 8, f11 = f7 + 3 sheep.
- Step-1 fingerprints (rival money/hands after step 0, from the elite refs): Boey 2339/5 (29 of 30); Fourth Quadrant 393-1596/3-4;
  THIRD FARM CLUB 19/5; 吃白饭的大肥鱼 12-17/4; Majkel1337 1806-1835/5 or 1545/0; Kaggledew Valley 3000/0; C2S3 lineage 2464/0,
  964/0, 2467/0. Live 253 rivals under the fine router: chassis 89 (fingerprints 2853-2864/0: BELOW the old 2985 cutoff; T8 74%),
  C2S3 69 (30%), herdpoor 45 (55/5, 57/4: T8 47%), herdfirst 27 (410/4, 1365/3, 2338/5: T8 85%), other 23 (2600-2630/0, 608/6: 52%).
  New router knob `route["fine"]` (ctl_op.py `_opr_class`): herdpoor = h>=4 & m<300 (tape), herdfirst = Boey 2200-2500/5 or
  300-1700/3-5 (opening), majkel = 1700-2200/5 (tape), chassis_min lowered (2800 in D2, 2550 in D3). f11 (3 sheep) rejected: its
  +$6.4k own cash comes from four rival collapses the 75% screen misses (our cash +$28-65k in those seats).
- D2 (f7 + fine router, tape vs C2S3/chassis/herdpoor/majkel): panel +$3,338 +- 2,119, wins 5 -> 9, our cash -$67, TFC seats
  byte-identical to T8 (8/8). D3 = D2 with chassis_min 2550 (the live copies sit at $2,853-2,864 and $2,600-2,630 with 0 hands).
  Full gates of D3 running (live 253 S=0, goldg, top10g, closed loop 20 seeds).
- Melon race, corrected: on the Boey seat the controller's 42 melon units sold at hour 0 of day 11 (after Boey's 30) earn about
  the same as at hour 7 of day 10 (melon_day f13/f14: +$7k on day 10, gone by day 11): 72 combined units are only 21% down the
  melon curve, so the order costs ~$1k. T8's day-10 $13.6k comes from VOLUME (12 melons, 72 units, fertilized to ripen by day 10),
  not from the hour. The controller carries 7 melons (its day-2 top-up never happens: cash). f15 (9 melons day 0) on test.
- Ledger, Boey seat 113065954 (whole game): controller f7 vs T8: carrots +$4.4k, tomatoes -$3.6k, hires -$5.0k (13 hands late).
  Boey vs T8: wheat +$14.5k (Boey grows 17-18 wheat plots all game and never buys feed; T8 nets -$5.7k on wheat buying $28-40
  feed), eggs +$5k (7 geese), fertilizer +$2.4k; T8 wins tomatoes +$21.8k, melons +$4.3k. Home-grown feed is a real lever
  (~$5k/game) but it is a labour trade against the tomato block, not free money.
- D3 full gates: goldg 111/111 seats identical to T8 (all routed to the tape); closed loop identical to T8 (40/40 both agents);
  top10g +$1,029 +- 467 vs T8 (73 -> 79: Boey 3 -> 8, FQ 2 -> 4), +$974 vs v29 (74 -> 79); live 253 vs T8 +$268 +- 265 but
  wins 142 -> 140: identical on 208 games, herdfirst (27 live games, weak FQ-lineage copies 410/4, 1365/3) 23 -> 19 wins,
  other (15) 7 -> 9. vs v29 live -$543 (153 -> 140: v29's tape-plus beats the T8 tape on every tape class). Framing: a
  deployable controller build replaces the T8 slot, so it must beat T8, not v29; D3 is neutral on live and +6 on top10g.
- f15 = f7 + 9 melons on day 0 (3 cows 2 sheep 4 wheat): panel +$14,054 +- 5,581 (median +$4,982), wins 5 -> 13 of 21, our cash
  +$8,203, elite -$5,851 (Boey 0 -> 4, FQ 0 -> 4, TFC 5 -> 5). The melon VOLUME is what the controller lacked (7 melons vs the
  tape's 12); with 9 it wins the day-10 book against Boey/FQ's 30 units. Checking per seat for replay collapses; D4 = f15 + the
  fine router is on the live-253 and top10g gates.
- f15 per seat: the wins over Boey/FQ coincide with the recorded elite's final cash falling 14-42% (FQ 113124487 -42%, 113237685
  -34%, 113276019 -24%, 113180379 -20%; Boey 113065954 -20%, 113153433 -19%, 113179000 -18%), i.e. its recording breaks when our
  farm dumps 54 melon units and sells wool/milk earlier; the 75% screen misses these. On the seats where the elite's cash moves
  less than 6%, f15 vs T8 is about even. The same caveat applies to eliq/f7's Boey/FQ gains and to Codex's elite split. A
  divergent opening can only be judged against reacting opponents: self-play f7/f15 vs T8 on fresh towns (6200-6219, both
  seats) is running. Reliable so far: the controller's OWN cash on herd-first towns is within ~$1k of the tape (f7 -$946,
  f15 +$0.3k on the unaffected seats), up from -$4.7k for cfg_e; it loses 23 -> 19 against the weak herd-first copies live.
- D4 (f15 + router): live vs T8 +$713 +- 502, wins 143 -> 141 (herdfirst 23 -> 19, other 7 -> 9); top10g +$4,718, 73 -> 97
  (Boey 3 -> 15, FQ 2 -> 14) with the recorded elite's cash down >15% in 17 of those 60 seats: artifacts.
- REACTING self-play vs T8, fresh towns 6200-6219, both seats (the honest judge for a divergent opening): f7 wins 18/40 (45%),
  mean -$923, median -$294; f15 wins 6/40 (15%), -$3,471 (its 54 melon units sell after T8's 72). So the controller opening is
  near parity with the tape but not ahead; the elite-gate gains were mostly recorded-rival collapses. No submission change:
  the pair stays v28 T8 + v29 TP_A31g. The self-play loop (40 games, ~5 min) is now the development metric; f13/f14 (melon
  harvest first, sold at hour 7, i.e. before T8's hour 9) and eliq are on it.
- Head-to-head ledger, eliq vs REACTING T8 (40 self-play games): melons -$7.3k (7 plants vs 12: volume, not the hour), wool -$3.0k,
  wages -$2.8k, strawberries +$5.8k, fertilizer +$1.7k, eggs +$1.1k, wheat +$1.0k; net -$1.3k, 20/40 wins. Counters tried in
  self-play: melon harvest-first (f14 45%, f13 28%), fertilized melons (f18 19%, f20 40%: keeping fertilizer starves the
  cash-flow days), same-step sell on drop (f21 30%: the drop already sells the same hour, the trip itself is the hour late).
  Next: `research/opening/search_open.py` = local search over ~20 opening knobs scored by reacting self-play (40 games each vs
  T8, omw_v15a, pub_metav4v13; both seats), champion kept in cfg_best.json / cands/full_OP_best.py, log search_log.jsonl.
- Rival-aware knobs added to ctl_op.py: `rival_straw` (strawberry target cut by w per rival strawberry plot) and `rival_anim`
  (cow/sheep targets cut by w per rival animal of the kind); census `_rival_counts` at every plan. Probes r1/r2/r3 in self-play.
  Late-game knob never measured before: `feed_reserve_tiles` (grow feed wheat instead of buying at $28-40): FR1 (0.75 tiles per
  animal) and FR2 (0.5) on pin249 vs T8. Search: first acceptance s004 (abs_last 5) score +3,647, T8 margin -$584 at 20/40.
- Probes vs REACTING T8 (40 games): r1 rival-aware strawberry cut 12/40 (-$3.4k: ceding the book to T8's flood loses our early
  strawberry edge), r2 (+ tomato ramp) 16/40, r3 rival-aware herd cut 11/40 (-$5.8k: wool -$6.9k, milk -$4.2k), c0 no crew
  floor 18/40 (-$2.2k; wages unchanged), h0 farmer moves at hour 0 2/12 (-$5.5k: the spawn model breaks), a1 (+ access tiles
  free) abandoned. Lesson: against a fixed-volume script the winning move is to take the thin books EARLIER, not to cede them;
  hour-level route surgery backfires through the routing model. Search: 10 candidates, one acceptance (abs_last 5, T8 -$584).
  Traces: the tape harvests a cow ON the spawn tile at hour 1 and drops at hour 2; ours are one tile out (hour 3).
- "Take the books earlier" probes vs reacting T8 (40 games): e1 early strawberries 2/4/6/8 by day 5 + NE tranche 10 -> 16/40
  (-$2.8k), e2 = e1 + 3 sheep 14/40, f6 elite day 0 (2C 3S) 14/40 (-$1.9k), f11 f7 + 3 sheep 10/40 (-$3.6k). Both directions
  from eliq lose: ceding the books loses the early edge, taking them earlier starves the herd (cows unplaced in the shed on
  days 3-5). Structure probes: tp0 = the TAPE's plan (2C 2S 12 melons, tape herd table, NE 6 / SW 11) executed by the
  controller: 0/40, -$15k (wool -$7k, melons -$4.8k, milk -$2.8k): the recorded routes' value is the execution of that tight
  sequence, the controller cannot run it. Handovers hb6 (tape days 0-5, controller from 6) 12/40 (-$2.0k), hb10 (tape to day 9)
  10/40 (-$4.2k): the controller continues the tape's farm worse than it runs its own plan from day 0 (eliq 20/40). Search
  restarted from the champion (abs_last 5 + over.prem_drop False: 23/40 vs T8, -$817; omw 38/40 +$6.6k; pub 39/40) with no-op
  proposals skipped (search_open2.log). Feed-farm pin249 at 435/747.
- tp1/tp2 (the tape's plan on the controller + melon harvest-first / + fertilized melons): 0 wins of 17 each vs reacting T8,
  stopped. The controller cannot run the 12-melon plan whatever the melon timing. Placement fix p1 = champion + access_free +
  anim_place_order [SHEEP, COW, GOOSE]: a sheep on the spawn tile (4,4) is harvested at hour 1 of day 6 and its wool dropped
  and sold at hour 2 (T8's lot at hour 5); the other access tiles stay unused by the placement for a reason not yet found.
  Search2 acceptance s022: straw_hf ne [6, 5], sw [6, 5, -0.25] -> T8 24/40 (-$452), omw 40/40, pub 39/40, score +4,011.
- Feed farm (late-game knob `feed_reserve_tiles`, never measured before) on pin249 vs T8: FR1 (0.75 wheat tiles per animal)
  -$466 +- 126 (219 -> 214), FR2 (0.5) -$244 +- 88 (219 -> 216). Wheat +$1.5-2.1k but carrots -$1.2-1.5k and tomatoes
  -$0.2-0.6k, rival +$300-400: the feed plots displace the carrot/tomato blocks. Rejected. FK1 (fert_cost_w 0.5, fert_keep 10) next.
- FK1 (fert_cost_w 0.5, fert_keep 10) on pin249 vs T8: -$11 +- 25, 219 -> 219 wins: the late game's fertilizer use is already
  at the gain rule's optimum. Neutral, rejected. Search3 (from the s022 champion, placement knobs added): s032 land_wheat 8 ->
  T8 25/40 (-$103), omw 40/40, pub 40/40, composite +$4,165; 24 candidates since the restart, one acceptance.
  Plan: when the search stops (~23:00 UTC) validate the champion on fresh seeds (6300-6339) vs T8/omw/pub, then the routed
  deployable on live-253 (S=0), goldg/top10g, before any submission decision on 29 Sep.
- Champion s032 on FRESH seeds 6300-6339 vs T8: 41/80 (51%), -$589 +- 718, median +$764 (training seeds: 25/40, -$103). The
  search's 40-game T8 blocks (SE ~$800) accepted noise. Search restarted (search_open4/5) with a 120-game T8 block (seeds
  6200-6259), acceptance = T8 margin +$400 with no public-agent regression. Honest state: the controller opening is at parity
  with the tape against a reacting T8; every structural lever tested today (melon volume, book timing, placement, rival-aware
  targets, handovers, feed farm, fertilizer input) is neutral or negative.
- Wide block (120 games, seeds 6200-6259 both seats) vs reacting T8: the champion s032 is 46/120 (38%), -$2,560: the 40-game
  block (25/40) was a lucky draw. NOTE: both seats of one seed are near-identical games (38 of 60 pairs identical margins):
  panels should spread SEEDS, not seats; effective samples are ~60% of the game count.
- Town split of the champion's losses (first 4 shops): yarn stores >= 2: 0/12 wins, -$11k (WOOL us $70k vs T8 $90k, tomato
  -$4.7k); strawberry buyers 0: 1/16, -$8.1k (TOMATO us $0.9k vs T8 $8.7k: T8's s2t conversion plants tomatoes in
  one-strawberry-buyer towns, the controller opening has no tomatoes); milk buyers 0: 8/28, -$5.3k; tomato buyers 0: 13/48,
  -$4.7k; egg buyers 2: +$1.2k. Melons -$7-8k in every split (structural). 12-melon portfolios on the controller: 15/120 vs T8
  and 18/40 vs omw (m1, m2): dead. Testing demand-gated tomatoes in the opening (tom_ramp buyers=true, tom_sw) on the wide block.
- CORRECTION: eliq on the full 120-game block vs T8 = 58/120 (48%), -$1,980 +- 676; the search champion s032 = 46/120 (38%),
  -$2,560. The accepted knobs (abs_last 5, prem_drop False, straw ne [6,5], land_wheat 8) were fitted to the first 40 games and
  HURT on the other 80. Champion reset to eliq. Yarn-town fix `herd_cap_by_yarn` {"1": 24, "2": 30}: on the worst yarn game
  (seed 6248, decoupled) the controller reaches 12-14 sheep instead of 8 and the loss shrinks from -$23k to -$14k (T8 goes to
  21 sheep with SE); adding SE at day 12 + anim_day_max 5 (y2) starves the farm (-$37k). Running on the eliq base, wide block:
  y1 (yarn cap), t1 (demand-gated tomato ramp), yt (both); search6 restarted from eliq (1 candidate at a time, 120-game T8 block).
- Town fixes on the eliq base, wide block, paired vs eliq: y1 herd_cap_by_yarn +$281 +- 326 overall (58 -> 55 wins; yarn>=2 towns
  +$4,643, straw-0 towns +$2,917; but omw 39 -> 36/40, pub 40 -> 35/40); t1 tom_ramp (buyers-gated) +$331 +- 258 (58 -> 56;
  straw-0 towns +$1,254, 0 -> 2 wins; omw 35/40, pub 38/40); yt both +$112 (58 -> 50, omw 32/40). Each fix pays in its target
  towns and costs elsewhere (bigger herds/tomato tiles starve cash against copies). Net effects are noise-level (~+$300);
  the controller opening stays at ~48% vs reacting T8 (eliq 58/120, -$1,980).
- FIRST REAL GAIN: p1e = eliq + access_free + anim_place_order [SHEEP, COW, GOOSE] (a sheep on the spawn tile: wool harvested
  at hour 1 of day 6, dropped and sold at hour 2, before T8's hour 5) on the wide block vs eliq: +$1,059 +- 384 (2.8 sigma),
  wins 58 -> 59, T8 margin -$921 (from -$1,980), wool +$837; omw 38/40, pub 39/40. g1 (sheep-heavier, goose-lighter table):
  +$477 but wins 58 -> 51, eggs -$1.8k: rejected. New base cfg_p1e.json; fresh-seed validation (6300-6339) running;
  search7 restarted from p1e.
- p1e on FRESH seeds 6300-6339 vs reacting T8: 50/80 (62%), +$898 +- 532, median +$916 (s032 on the same seeds: 41/80, -$589).
  With the wide block (59/120, -$921) the controller opening is at ~54% and about even in money against T8: the first build
  ahead of the tape on unseen towns. Live gates launched: PF = p1e with the tape only vs C2S3 (controller vs copies, herd-poor,
  herd-first, other), PS = p1e with the tape vs C2S3/chassis/herdpoor/majkel (controller vs herdfirst/other only).

### 29 Sep 19:10 UTC: PF / PS live gates (253 games from step 0, paired vs T8 and v29 by router class)
- PF (p1e controller everywhere except the C2S3 lineage -> tape): vs T8 +$3,695 +- 949 (143 -> 162 wins), vs v29 +$2,871 +- 931
  (154 -> 162; trimmed of 6 rival collapses +$1,989 +- 548, 141 -> 156). By class vs T8: chassis +$1,680 (71 -> 79, us +1,488),
  herdpoor +$10,409 (21 -> 29, them -5,895), herdfirst +$140 (23 -> 23), other +$19,981 (7 -> 10, them -12,655), C2S3 identical.
  The herdpoor/other gains are the recorded-rival pattern (their cash falls), the same shape as Codex's e_wave (+$3,125) which the
  reacting loop rejected. Reacting numbers for p1e stay the judge: T8 59/120 (-$921), omw 38/40 +$6,043, pub 39/40 +$6,133
  (T8 reference 40/40 +$6,297 / +$6,872).
- PS (tape vs C2S3/chassis/herdpoor/majkel; controller only vs herdfirst/other, 42 games): vs T8 +$1,200 +- 656 (143 -> 146),
  vs v29 +$375 +- 680 (154 -> 146; trimmed +$313 +- 232). Neutral, i.e. it is the tape.
- search7 from p1e: s133-s135 all below the base (crew a=3.8 + cow-first -$1.0k; land_wheat 20 + abs_last 3 -$24; crew a=2.5 +
  liq 6-11 -$0.9k); killed at 19:05 UTC to free the CPU. Crew ceilings c9 (hi 9) -$1.0k, c10 (a 2.8, lo 3, hi 10) -$0.3k. Every
  portfolio change in the search log lost $2-5k on the 40-game block (melon0 8/10/12, wheat0 4-10), i.e. the day-0 budget is on a
  knife edge; melon_fert always -$1-2k.
- New tools: `research/opening/sp_diag.py A B seed seat` (reacting self-play per-day cash gap + revenue by product for both
  farms); scratchpad `classify_pub.py` (step-1 signature and router class of a public agent).
- 29 Sep 19:45 UTC: every public agent in arena/cand (pub_*, r81, rich7, ses_d) is chassis class at step 1 (0 hands, $2,843-2,990),
  so there is no reacting herdpoor/herdfirst proxy; the +$10k herdpoor slice of PF's live gate cannot be verified and is treated
  as a recorded-rival artifact. PSy live: herdfirst -$1,420 (23 -> 19) vs PS +$140: the yarn/tomato stack is dropped.
- sp_diag (p1e vs T8, seeds 6300-6303, both seats identical): gap within $1.5k until day 9; day 10 -$6..12k (T8 sells 12
  fertilized melons for ~$15k, we sell 7 unfertilized for $4-9k; T8's day-10 cash 17k vs our 5k funds its land/cows); closed
  by day 20 (our 31 early strawberries sell $6-8k/day on days 17-20); days 21-28 decide it (T8's later strawberries and 2nd
  melon crop vs ours aging out; our strawberries get rotated to wheat on days 22-25 while T8 keeps 13 to day 27, likely the
  shared-market price effect of our earlier heavy selling). Finals -4.0k/-0.9k/-1.2k/+4.4k. Per product: melons -$4..8k every
  game, milk -$1..9k, wool -$0.7..5.5k, eggs +$3..8k, wheat/fert/carrot +$1..3k.
- The day-0 budget: 7 melons ($560) + 11-13 wheat + 3 cows ($1,200) + 2 sheep ($1,000) + 5 hires = the whole $3,000; T8's
  tape does 12 melons + 8 wheat + 2 cows + 2 sheep. batch_q tests T8's mix inside the controller (q1 melon 12/wheat 8/C2S2,
  q2 + melon_fert, q3 melon 10, q4 + hires0 4, q5 wheat 13), `eval_batch_q.log`.
- Kaggle 29 Sep 19:40 UTC: v28 T8 2558.9, v29 TP_A31g 2538.6 (both "complete").
- 29 Sep 20:10 UTC: PF elite gates. goldg (56 paired seats in tp/out refs): vs T8 -$2,350 +- 1,899 (27 -> 22; 吃白饭的大肥鱼 -$3.7k,
  THIRD FARM CLUB -$2.9k, Yizhou identical = tape), vs v29 -$1,949. top10g (60 paired, Boey/FQ): vs T8 -$1,054 +- 756 (5 -> 6),
  vs v29 -$1,438. Step time of PF: mean 9 ms, p99 0.3 s, max 0.68 s (step 576) under load; no errors in 270 + 111 + 253 rows.
- Engine: FERTILIZE sets fertilized_until_day = day + 2 and each watering in the window then adds 2 units instead of 1, so one
  fertilizer unit at melon age 6 gives 6 units by day 8 (harvest day 10 at 6 instead of 5). The earlier melon_fert tests ran
  with over.fert_keep 0, i.e. no fertilizer in the shed to apply: they never tested fertilizing. batch_q3 = melon_fert [6] /
  [6,7] with fert_keep 7 / 10. Strawberry max_yield 4 = four harvests (days D+10..D+16), so the early-planted strawberries
  finish on days 20-24 and are dug for wheat/carrots; not a bug, T8's finish 2-3 days later.

### 29 Sep 20:00 UTC: PF fresh loops, pure controller vs C2S3 recordings, market model
- PF fresh-town loops (seat 0 only, seats replay identical games): vs v29 (TP_A31g) 15/40, -$1,850 +- 795; vs T8 on
  6340-6379 23/40, -$456 +- 1,016 (earlier 6300-6339: 50/80, +$898). The controller is below our own tape v29 head-to-head.
- q6/q7 (melon0 9 with hires0 4, wheat0 11/9): -$9.7k and -$20k vs T8 (0-4 wins of 90), copies -$1.4k/-$10.7k: the controller's
  day-0 plan is a knife edge; any re-parameterisation of the budget breaks it. Only the tuned point (p1e) works.
- p1n (= p1e with route None) on the 69 live C2S3 games: +$30k vs T8 but 17 rival collapses; trimmed 52 games +$2,992 +- 2,067
  (16 -> 24 wins), our own cash +$3.6k. Recorded, so not evidence, but the controller does not fold in C2S3 towns.
- T8 vs top-10 recordings (tp/out refs): Boey us 106k vs elite 118k (-$11.9k, 3/30), Fourth Quadrant 88k vs 98k (-$9.8k, 2/30);
  gold-zone teams roughly even (吃白饭 -$1.2k 8/20, THIRD FARM CLUB +$3.3k 12/20, Yizhou +$2.3k 7/16). The top-10 gap is ~10%
  of final cash. `research/opening/elite_diag.py cand gid seat` = per-day ledger (cash gap, revenue by product, census) of a
  candidate vs the repaired elite in its town; runs on 6 Boey/FQ seats -> ed_T8_*.txt.
- Engine market (kaggriculture.py MARKET_PARAMS): price = base +- amp*f(|inv - 10000|), no relaxation; the only drain is the
  town: each unlocked shop instance takes 1 unit of each of its products every 4 steps (2 for single-product shops), the
  town centre 1/day of everything but fertilizer. Glut side: STRAWBERRY and MILK linear (T 100 / 122: selling T units moves
  the price by 1.6x base, i.e. the price is gone after ~60-75 units over the drain), MELON and WOOL sq (T 300 / 105, calm then
  crash), WHEAT/EGG log (gentle), CARROT/TOMATO sqrt. Scarcity side pays up to +70% (strawberry), +60% (milk), +80% (wheat),
  hinge spikes for carrot/tomato/egg once T units short. So the pool is shared and cumulative: whoever floods a product kills
  it for both, and unsupplied shop demand pushes prices above base.
- 29 Sep 21:40 UTC: Codex controller handover built: codex_pkg/controller_handover/ + kagg_controller_20260929.zip (149 files,
  8.5 MB): README_CONTROLLER.md (state, ledgers, engine market facts, elite decode, asks A/B/C, acceptance bar), sources
  (ctl_op.py, ctl.py, base_m7_t4.py, bm5.py, mk.py, mkcand.py), cfg (p1e/eliq/e/best, T8_knobs, batches), cands (p1e, PF,
  p1n, PS, eliq), opponents (T8, TP_A31g, omw, pub), harness, tools, rows (search/batch logs, live/elite/fresh rows), diag
  (spd/ed/ed2/orig ledgers), notes. Fertilized-melon batch f1-f3: 30/24/23 of 120 vs T8 (-$7.5k..-9.6k), copies lost too.
- 29 Sep 21:50 UTC: v30 = PF submitted (Kaggle 56651672, gold/submit/main_ctl_PF.py, sha ded15761...). Pair: v29 TP_A31g + v30 PF;
  T8 (v28, 2558.9) drops out. Kaggle showed v28 T8 above v29 (2538.6) on 29 Sep, within noise. Two submission slots remain on
  30 Sep to restore any pair (e.g. resubmit T8) before the 23:59 UTC deadline.

### 29 Sep 03:30 UTC: final pair T8 + PF (DATE CORRECTION: the entries headed "29 Sep 19:10 / 20:00 / 21:40 / 21:50 UTC" above were
really 28 Sep UTC; Kaggle's timestamps put v30 at 28 Sep 20:35 UTC)
- v30 PF's ladder overnight: 600 -> 2,169 in 77 games (71 wins, opponents ~2,100; the first-hour loss to a 1,253 player cost 111
  points at high uncertainty). v29 46/101 against opponents >= 2,300 (mean -$1,290), 2,537-2,555. T8 2,574.
- User resubmitted T8 (56661347) and PF (56661351) so the latest two are T8 + PF. Two slots remain on 30 Sep.

### 29 Sep 04:10 UTC: Codex ("astra") forecast patch on v29, `cands/full_FC_phase.py` (from Downloads/v29_phase_linear.py, sha 54f6ed19...)
- Exactly v29 (full_TP_A31g.py, CRLF vs LF only) + 220 appended lines. `_edge_track` wraps GoldCtl._mk_track: watches the
  rival's MILK and STRAWBERRY tiles (public), counts units harvested by a rival unit standing on the tile as hidden stock and
  per-unit cargo, minus the rival's observed sales (floor-price sales reset it). `_edge_phase_forecast` (day >= 12): the
  rival's sale hours from its last three sale days, and spreads hidden stock, cargo (after its walk to a shed-access tile),
  ripe tiles and tomorrow's due production over those hours. `_edge_dp_sell` = v29's `_dp_sell` line for line plus one line
  that swaps the rival forecast rv for the phase forecast. Wool is not in `_EDGE_TIMED` (only the linear-curve products milk
  and strawberry), which matches Codex's "keep v29's wool timing" variant.
- Codex's reported numbers (online session, not reproduced here): full forecast 66-14 vs reacting v29 and 52-28 vs T8 on 40
  dev towns both seats; 120-0 vs omw and pub (+$500 / +$299 margin over T8); wool-timing variant goldg 55 wins, +$214 vs v29.
- Smoke 6500 vs v29: -$1,864, 199 forecasts, 0 errors, step max 0.23 s. Gate: `research/opening/gate_forecast.sh` on seeds
  6500-6539 (vs v29, T8, PF) and 6500-6559 (omw, pub), then goldg / top10g; rows fc_phase_*.jsonl.
- The patch is a late-game selling layer on the shared GoldCtl: `_dp_sell`, `_mk_track`, `_copy_plan*` and `_town_draw` are
  identical in v29, T8 and PF, so it transplants unchanged. Built `cands/full_OP_PFfc.py` (PF + patch) and `cands/full_T8fc.py`
  (T8 + patch) by appending `research/opening/patch_phase_linear.py`. Smoke PFfc vs PF 6501: +$1,216, 324 forecasts, 0 errors,
  step max 0.35 s. Head-to-head runs fc_PFfc_PF.jsonl and fc_T8fc_T8.jsonl on 6500-6539 both seats.

### 29 Sep 04:40 UTC: why the resubmitted PF drops rating early, and the fix candidate PFc
- PFr (56661351) lost 1 of 7 early games (dk07dk, $141.6k vs $147.2k, -72 rating at 992). All three PF losses replayed
  (`elite_diag.py cand FILE.jsonl:GID 0`, now takes livefetch games; rows lloss_*.txt): the rivals are chassis copies (0 hands,
  $2,639 / $2,855 at step 1). PF replays reproduce the real games (-7.6k / -9.3k / -3.3k); T8 in PF's seat wins them
  (+16.5k / +5.9k / +22.1k) though the recorded rival's cash falls 122.8k -> 93.7k etc. (artifact). PF+forecast -6.8k / -9.1k / -3.0k.
- Reacting evidence on the same class (omw_v15a and pub_metav4v13 are chassis): T8 40/40 +$6,297 / +$6,872 vs p1e 38/40 +$6,043 /
  39/40 +$6,133 (6100-6119); T8's 120-row loops 6100-6159: 120/120 each, +$7,695 / +$8,437. The controller is weaker against copies.
- PFc = p1e with route tape for ["C2S3", "chassis"] (`cands/full_OP_PFc.py`, `cfg_PFc.json`): bit-identical to T8 vs a chassis copy
  (pub 6502: 79,339 vs 76,332 for both); the controller plays only against herdpoor / herdfirst / majkel / other. PFcfc = PFc +
  forecast patch. Running PF vs omw/pub on 6100-6159 (cl_PF_*_6100.jsonl) to pair with T8's 120-row loops.

### 29 Sep 04:30 UTC: forecast patch passes out of sample; it helps every agent
| run (reacting, both seats) | rows | wins-losses | mean +- se (per seed) |
|---|---:|---:|---:|
| FC_phase (v29+fc) vs v29, 6500-6539 | 80 | 62-18 | +$469 +- 87 (33/40 seeds) |
| FC_phase vs T8 | 80 | 52-28 | +$645 +- 208 |
| FC_phase vs PF | 80 | 52-28 | +$1,765 +- 678 |
| FC_phase vs omw / pub, 6500-6559 | 120 / 120 | 120-0 / 120-0 | +$8,619 / +$9,073 |
| PFfc vs PF | 80 | 64-16 | +$758 +- 180 (34/40) |
| T8fc vs T8 | 80 | 60-20 | +$456 +- 129 (32/40) |
- Elite gates FC_phase: goldg vs T8 -$187 +- 213 (27 -> 27), vs v29 +$215 +- 170; top10g vs T8 +$622 +- 215 (5 -> 3), vs v29 +$237 +- 125.
- PF vs the public copies on 6100-6159 (partial 96/100 rows): 88/96 and 95/100 wins, +$6,750 / +$6,984; T8 on the same seeds 120/120,
  +$7,695 / +$8,437: the controller loses ~7% of games to copies, the tape none. Supports PFc (tape vs chassis).
- Finalists: T8fc (`cands/full_T8fc.py`) and PFcfc (`cands/full_OP_PFcfc.py` = PFc + forecast). `research/opening/gate_final.sh`:
  T8fc vs FC_phase, PFcfc vs T8fc, T8fc vs omw/pub (6500-6559), pin249 and live191 (T8 vs T8fc paired), goldg/top10g for both.

### 29 Sep 05:10 UTC: every PF ladder loss below 2,300, replayed (elite_diag.py cand live_losses_all.jsonl:GID 0)
| game (rival, rating) | rival step 1 | class | PF (real) | T8 | PFc | PFcfc |
|---|---|---|---:|---:|---:|---:|
| 114883751 Mukesh R 1253 | $2,639, 0 hands | chassis | -7,633 | +16,529 | +16,529 | +16,637 |
| 114912430 islet 1833 | $2,854, 0 | chassis | -837 | +4,015 | +4,015 | +4,371 |
| 114944483 Takauchi Suguru 2078 | $2,855, 0 | chassis | -9,322 | +5,923 | +5,923 | +4,270 |
| 114996915 fufufukakaka 2143 | $38, 2 hands | other | -2,235 | +3,557 | -2,235 | +261 |
| 115011893 Arjun Vinod 2146 | $964, 0 | C2S3 (tape already) | -9,181 | -9,181 | -9,181 | -9,033 |
| 115060631 dk07dk 1129 | $2,639, 0 | chassis | -3,310 | +22,059 | +22,059 | +22,477 |
- PFc = T8 exactly in the four chassis games; PFcfc turns 5 of 6 into wins (recorded rivals: T8-side margins are inflated by
  the rival's collapse, direction matches the reacting copy evidence). Arjun Vinod beats the tape too (also beat v29 at 2,577).
  v29 was 21-0 below 2,300 on the ladder, T8r 8-0, PFr 8-1, PF 73-5.
- 29 Sep 05:05 UTC CORRECTION: Kaggle allows 5 submissions per UTC day (maxDailySubmissions 5 from the competitions API), not 2.
  29 Sep: 2 used (T8r 56661347, PFr 56661351), 3 left; 5 on 30 Sep.
- 29 Sep 04:59 UTC: submitted v31 = v29fc (56663285, main_ctl_v29fc.py = full_FC_phase.py) and v32 = PFcfc (56663295,
  main_ctl_PFcfc.py). Stage-1 finalist gates: T8fc vs FC_phase 25-55 (-$430); PFcfc vs T8fc 68/80 tied (PFc routes our tape as
  chassis, so they are near-twins); T8fc vs omw/pub 120-0 each (+$8,764 / +$9,368); pin249 T8fc vs T8 +$84 +- 46 (219 -> 217 wins).

### 29 Sep 05:40 UTC: seller experiments on v29fc (vs v29fc, 6600-6639 both seats)
- W25 (mkt_dp_rival_w 2.5) 47-33 +$71 +- 55; W10 (1.0) 36-44 +$41 +- 55; WB3 (w_behind 3.0) 68/80 ties (never fires in mirror
  games). FW (Codex's full forecast: _EDGE_TIMED += WOOL) 58-22 +$361 +- 77 (30/40 seeds): a real gain on top of v29fc.
- Codex saw FW lose 2 games to the third public agent via the wool/care coupling (care_worth needs pv >= care_min_price 12;
  flooded wool drops below). Running FW and v29fc vs pub_smallershock 6600-6659, FWc (FW + care_min_price 0) vs v29fc, FW elite gates.
- v29fc (56663285) still "pending" validation 40 min after submission while PFcfc (20 s later) validated; poller running.
  Older T8r/PFr still play on the ladder (T8r 1,979, PFr 1,519 at 05:38).

### 29 Sep 06:00 UTC: late-game search on the tape (user: "go ahead with the late game search too")
- `research/opening/late_search.py BASE par [names]`: single-change screen on the GC_P.update config line of a tape build
  (top-level keys appended last; knobs that also live in div_over / rich_over / herd_rich_over edited there too). Each variant vs
  the base on 6700-6719 seat 0 + 6720-6739 seat 1 (40 reacting games). Rows ls/<name>_{a,b}.jsonl, log ls/late_search_log.jsonl.
- Base: full_v29fc_FW.py (wool in the forecast). 24 variants: arb, arbc (glut arbitrage), herddeny, herdsheep, herdbig,
  wfert10, ferth0, fertidle, race, lateplan, digglut, dpper9, dpcap30, animfwd1/2 (care priced after drain: the wool/care fix),
  tickdefer, slots1, dpdue, lastplant, strawfc, strawfc19, hands17, nofloor, wfloor. Winners (> ~+$150) go to pin249 (day-12
  pinned, honest for late-game changes) + 80-game self-play + public agents + elite gates.
- 29 Sep 06:05 UTC, wool version FW (full_v29fc_FW.py) checks: vs pub_smallershock 6600-6659 118-2, identical losses to v29fc (seed
  6659 both seats), paired -$8 +- 57; FWc (care_min_price 0) vs v29fc 21-59 -$692 (dropped); goldg vs v29fc -$141 +- 118 (55 -> 56
  wins), top10g vs v29fc +$72 +- 53 (71 -> 74); vs T8 refs goldg -$392 (27 -> 28), top10g +$819 (5 -> 6).
- v29fc (56663285) stuck: 0 episodes after 64 min (EpisodeService ListEpisodes), PFcfc 11 episodes. Kaggle queue stall.
- Late search first 10 (vs FW, 40 games): arb -$865, arbc -$811, lateplan -$1,141 (bad); race +$213 +- 200; herddeny +$236 +- 238
  (31 ties); herdbig/herdsheep +$108 +- 100 (33 ties); fertidle +$105; wfert10 +$4; ferth0 -$141.

### 29 Sep 06:30 UTC: late-game screen results (vs FW, 40 games, split seats)
- Null line: identical agents in split seats do not tie (seat order breaks hire/land ties): the no-change pattern on 6700-6739 is
  5-2, +$108 +- 100 (wfloor, herdbig, herdsheep, strawfc, strawfc19 all equal it exactly, i.e. no effect). Versus that null no
  knob gains: race +104 +- 220, herddeny +128 +- 197 (37 ties), dpper9 +9, slots1 -14, lead2 -9. Clearly worse: lastplant -$2,018,
  lateplan -$1,141, digglut -$936, arb -$865, arbc -$811, animfwd2 -$723, dpcap30 -$631, tickdefer -$476, animfwd1 -$457.
- Takeover step: start384 (normal-path handover on day 16 instead of 20, so the forecast DP seller runs 4 more days) 29-7,
  +$851 +- 379 (vs null +$742 +- 411, better in 28/40 games); start288 (day 12) 6-29, -$1,714. Screening start 336-456.
- Handover-day screen vs null (40 games): d14 -$55, d15 +$790 +- 304, d16 +$742 +- 411, d17 +$269, d18 -$336, d19 +$797 +- 256.
  Not monotone: confirming d15/d16/d19 on 6800-6839 both seats (80 games, seat effects cancel).
- Controller class breakdown on the elite gates (PFhW vs T8fc per seat): 吃白饭的大肥鱼 herdpoor -$3,978 (9 -> 6 of 20), THIRD FARM
  CLUB herdpoor -$3,568 (13 -> 9), Majkel1337 majkel -$6,954 / other -$3,354 (8 -> 2 of 24); tape-routed classes equal T8fc.
  Routing herdfirst to the tape (PFh) changes nothing on goldg (those teams are herdpoor). T8fcW (T8 + wool forecast) vs T8fc
  24-16 +$225 +- 137 (split seats).

### 29 Sep 07:00 UTC: the day-16 handover is self-exploitation, rejected
- FWS (FW + start 384) vs FW: head to head 6800-6839 50-20 +$864 +- 239, but pin249 -$388 +- 122 (218 -> 217 wins), live191
  (127/191) -$466 +- 146 (110 -> 109), public copies omw +$29, pub -$314, sms -$233 (wins unchanged), goldg/top10g identical
  (elites are ADAPT-divergent: start_div 384 already). The gain exists only against our own tape (non-divergent copy of itself).
  Lesson: head-to-head against the base is not evidence; late-game changes need pin249/live191 + public agents.
- Honest candidates now: FW (v29 + wool forecast) and T8fcW (T8 + wool forecast). comp_T8b.sh: both vs plain T8 on identical
  games (h2h 6900-6939, publics, pin249, live191, goldg, top10g); rating_est.py converts win-rate changes to rating (s = 70 fitted
  on 140 ladder games, s = 174 Elo).

### 29 Sep 08:15 UTC: tape candidates vs plain T8 (identical games), rating_est.py
| gate | A = FW (v29 + wool fc) | B = T8fcW (T8 + wool fc) |
|---|---|---|
| head to head vs T8, 6900-6939 both seats | 61-19, +$779 +- 204 | 64-16, +$610 +- 162 |
| public omw / pub / sms (120 each, wins 120/120/118 for all) | +$91 / -$193 / -$7 | +$425 / +$107 / +$233 |
| pin249 (from day 12; v29 = T8 from day 12, identical rows) | +$226 +- 63, wins 219 -> 218 | same |
| live191 | +$261 +- 82, wins 171 -> 174 | same |
| goldg (111) | +$29, wins 58 -> 56 | -$76, 58 -> 56 |
| top10g (253 of 270) | +$391 +- 105, 60 -> 61 | +$216 +- 72, 60 -> 60 |
- Rating: field gates move wins by -2..+3, i.e. about 0..+30 points (s70..s174); head to head says +80..+240 (a relative of T8,
  the upper bound). Estimate ~2,600-2,630 vs T8's 2,574 ladder peak.
- Controller late-strawberry work: in the 7 worst herd-type elite seats the controller's strawberries end 2-4 days before the
  tape's (tape: 20 plants to day 10 then +28 on days 11-12; controller: 36 by day 9, +9 on day 12). Variants (build_ctl.py, cfg_p1e +
  wool fc; r = routed like PFc, p = pure controller): cL1-4 raise straw_max with a small late wave (cL1 on seat 113262156: same
  plant counts, +$12.6k from day-12 knock-on); cS1 ne [4,4] late [4,6,11] max 56; cS2 ne [6,5] sw [6,4,-0.25] late [6,6,11] max 60;
  cS3 late [10,4,11] max 64; cS4 ne [4,4] late [4,6,12] max 56. ctl_round1.sh: pure vs T8fcW (7000-7039) + routed elite gates.

### 29 Sep 08:30 UTC: build bug in "pure controller" variants, tape pick, v29fc live
- A route of null skips _opr_route entirely, so GC_P["start"] stays 0 and the controller also plays step 0; every routed build
  (and every controller number so far: p1e, PF, PFc...) sets start = 1, i.e. the TAPE plays hour 0 of day 0 and the controller
  takes over at step 1. Controller playing its own step 0: c0p vs T8 4-16, -$10,937 (seeds 7000-7009) vs p1e 10-10 +$256.
  build_ctl.py now builds the pure form with route {"tape": []} (router runs, sends nobody to the tape, start = 1).
  The first round r1_*p rows are invalid; rerun as r1f_*p. p1n (route null) on the C2S3 live games had the same defect.
- Tape pick: A (FW, v29 + wool fc) vs B (T8fcW) head to head 6900-6939: 46-34, +$457 +- 194 (24/40 seeds).
- Isolation 7000-7009: p1e vs T8 10-10 +$256; p1e vs T8fc 5-15 -$487; p1e vs T8fcW 3-17 -$713; PFfc vs T8fcW 10-10 +$337.
- Kaggle: v29fc (56663285) validated 08:13 UTC at 600; pair live = v29fc + PFcfc.

### 29 Sep 08:50 UTC: controller late-strawberry round (negative) and Codex controller handover v2
- Corrected reacting round, pure forms (route {"tape": []}) vs T8fcW, 7000-7039 (54-56 of 80 games at packing): base c0
  32-24 +$1,993 +- 1,052; cL1 -$2,597, cL2 -$5,849, cS1 -$8,198, cS2 -$8,035, cS3 -$8,339, cS4 -$6,326 (all 6-10 wins of ~55).
  goldg routed vs c0r: cS1 -$1,496, cS2 -$553, cS3 -$2,316, cS4 -$311 (herdpoor seats -$0.4k..-$6.6k). The late-strawberry gap
  is a symptom: moving or adding strawberry waves breaks the controller's cash plan. The pure controller with the forecast is
  AHEAD of T8fcW in reacting play; its problem is the herd-type elites (c0r: THIRD FARM -$3,379, 吃白饭 -$3,508 a seat).
- Handover: codex_pkg/controller_v2/ + kagg_controller_v2_20260929.zip (181 files, 13.4 MB), README_CONTROLLER_V2.md; asks
  A (budget-coherent opening), B (opening for herdpoor/herdfirst/majkel rivals), C (anything in the rows); due 30 Sep 14:00 UTC.

### 29 Sep 09:10 UTC: CDP = the forecast DP seller during the tape (chassis) phase
- `research/opening/patch_cdp.py` + a one-line hook before `_GC._mk_store` in the chassis-phase block of the wrapper: from
  GC_P["cdp"]["from_day"], our SELLs of STRAWBERRY/MILK/WOOL are replaced by `_GC._dp_sell` on the shed stock after this turn's
  drops (x None = hold); steps whose list buys or hires keep the tape's sells; held units capped by tonight's shed room (release
  from hour 20). Built on FW: full_FWcdp12.py / full_FWcdp8.py / full_FWcdp15.py.
- TRAP: kaggle and lean.load take the LAST callable of the module as the agent; an appended helper function becomes "the agent"
  (our side then never acts: $3,000 final). Every appended patch must end by re-binding `xxx_submission_agent = agent`.
- Smoke 7100 vs FW: cdp12 -$1,086 (held 844 unit-steps, sold 185, skip_buy 62, released 12), cdp8 -$3,761; step max 1.1 s under
  heavy load (re-time unloaded before shipping). Test: cdp_test.sh (h2h 7200-7239, pin249/live191, publics).

### 29 Sep 09:20 UTC: tape push after the controller handover
- CDP (forecast DP seller during the tape phase) rejected: cdp12 vs FW h2h 7200-7239 21-29 -$182 +- 144 (54 games), pin249 -$99
  +- 83 (42), live191 +$111 +- 94 (42); cdp8 worse (13-40, -$650). The tape's own days 12-19 selling is already good.
- FWt = FW + TOMATO in the forecast seller (mkt_dp_prods += TOMATO, _EDGE_TIMED += TOMATO, the forecast's crop production
  formula generalised from _GC_CROPS fy/iv/mx; the generalised formula alone (FWg) is identical to FW on strawberries): h2h vs FW
  23-18 (30 ties) +$31 +- 44 (71/80), pin249 +$48 +- 25 (102 games, 39 changed, wins equal), live191 +$21 +- 30 (105). Small, safe.
- Day-29 sell-off screen (late_search.py, 8 variants on FW): fs0_0, fs0_6, fcap17, fcap22, late28, fbyval, d28cap22, h0first.

### 29 Sep 09:40 UTC: Codex recovered leads (Downloads/kaggriculture_recovered_leads_20260929.zip -> codex_pkg/recovered_leads)
- courier (PFc_courier1p/r = our c0p/c0r + 78-line courier_patch): during opening days 1-15 (not liq days), a harvest of one of
  our animals (>= 3 units) gets its own delivery trip at the head of a route when the visible rival animal stock of that product
  would lower our price by more than the trip's marginal wage ("protected" price).
- fund1 = "contract" layer (in the alloc builds): replaces plan_day with a copy that funds operating inputs (feed wheat for
  today's unfed animals, profitable fertilizations at fert_buy_margin, $100 runway) before optional capital (land/animals/seeds),
  and raises _open_keep in _open_midday by the same amount. alloc = fund1 + allocation_patch (herd additions ranked by marginal
  product + fertilizer receipts - animal, feed, tile and wage costs, k = 1..3 per kind).
- Built here: cands/full_CX_courier1{p,r}.py, full_CX_alloc1{p,r}.py, full_CX_fund1{p,r}.py (alloc minus the allocation patch).
  Smoke vs T8fcW 7000: courier -$3,220 (7 plans), fund1 -$115, alloc +$2,312 (267 evals); 0 errors; all load as `agent`.
- cx_test.sh: pure forms (+ c0p baseline) vs T8fcW and vs FW 7000-7039 both seats; routed forms on goldg/top10g vs r1_c0r_*.
- Day-29 screen vs null (40 games, FW base): fs0_0 -$67, fs0_6 -$57, fcap17 -$88, fcap22 -$277 +- 80, late28 +$15, fbyval +$27
  +- 14 (32 same), d28cap22 -$200 +- 73, h0first +$10. Nothing: the tape's endgame is tuned. Tape work left: FWt (tomato fc).

### 29 Sep 10:10 UTC: Codex's immediate candidates (its analysis: days 0-5 fine, 6-9 strained, 10-15 out-capitalised, late game rescues)
- New opening knob `straw_gate` in ctl_op.py ({"from", "to", "ahead"}; default None; backup ctl_op_before_strawgate.py): strawberry
  seeds (morning _open_crops and mid-day s_res) only spend cash above (next land price if due within `ahead` days) + tomorrow's
  feed shortfall. Rebuilt base g0p plays identically to c0p (seed 7000 vs T8: 106,019 vs 106,614 both).
- Builds (build_ctl.py, r/p forms): gA = mid_melon True (the second melon batch bought mid-day, 2 buys on seed 7000); gB = straw_gate
  {3, 12, 1} (8 gated plantings, reserve up to $2,396); gC3 / gC6 = access_free_last 3 / 6 (gC3 identical on seed 7000).
- g_test.sh: p forms vs T8fcW and FW 7000-7039 both seats (baseline cx_c0p_*), r forms on goldg/top10g (baseline r1_c0r_*).
- FWt (tomato forecast) publics done: see ft_*.jsonl.
- 29 Sep 10:00 UTC: FWt vs FW on the public agents (paired, same towns): omw +$70 +- 37, pub +$135 +- 66, sms -$38 +- 27, wins equal.
  FWt totals: h2h +$31 +- 44 (80), pin249 +$48 +- 25, live191 +$21 +- 30, publics +$56 avg: a small, consistent add-on.
- Codex recovered leads, reacting vs the base c0p on 7000-7039 both seats: courier -$646 +- 337 (vs T8fcW) / -$834 +- 297 (vs FW);
  fund1 exactly 0 (never changes a decision with cfg_p1e: lean opening); alloc -$5,733 +- 1,176 / -$6,136 +- 1,030. fund1r/alloc1r
  elite runs stopped; courier1r elite runs continue (it targets herd rivals).
- New opening knob `melon_fert_jit` (ctl_op.py; default False): with melon_fert, the opening's evening fertilizer reserve also keeps
  one unit per melon reaching a melon_fert age tomorrow unfertilized (and below max yield); nothing is held on other days. Base
  still identical (g0bp). gD6 = melon_fert [6] + jit (7 reserve units on seed 7000), gD67 = [6, 7] + jit. Reacting runs g_gD*.

### 29 Sep 10:40 UTC: session restart; Codex quick candidates rejected; controller slot = full forecast + routing option
- All runs died at the restart (fork failures: > ~50 processes). Keep <= ~16-20 python processes.
- Partial rows (paired vs c0p on 7000-7039): gA mid_melon -$2,979 +- 677 (6/25 better) vs T8fcW, -$4,459 vs FW; gB straw_gate
  -$11,393 / -$10,610; gC3/gC6 access_free_last identical in all 25 games (no-op); gD melon_fert_jit -$1.2k..-$3.9k (4-6 games).
- Routing from existing rows (controller c0r vs tape T8fcW per router class; tape-routed classes identical): goldg herdpoor
  THIRD FARM -$3,379 (9 vs 14 wins), 吃白饭 -$3,508 (6 vs 8); top10g herdfirst Boey -$1,878 (3 vs 3), FQ -$609 (3 vs 2),
  majkel Majkel1337 -$7,517 (1 vs 5), other Majkel -$3,732 (1 vs 3). Routing herdpoor+majkel+other to the tape: goldg 49 -> 56
  wins, top10g 69 -> 75; the controller then plays only herdfirst (11% of live253 games).
- Builds: patch_phase_linear_wt.py (wool + tomato forecast, generalised crop formula); build_ctl2.py NAME ROUTE PATCH [over]
  (adds mkt_dp_prods += TOMATO when the patch times tomatoes). c0tr (PFc routing + wool/tomato fc), c2tr (tape vs C2S3, chassis,
  herdpoor, majkel, other), c0tp (pure), c2wr (c2 routing, wool only), T8fcWt (T8 + wool/tomato fc). c0tr == c2tr == T8fcWt vs
  pub_metav4v13 6502 (identical tape). final_gates.sh: FWt goldg/top10g, c0tp vs T8fcW/FW, c2tr goldg/top10g, c0tr top10g.
- 10:50 UTC stage A: FWt vs FW goldg +$76 +- 35 (56 -> 56), top10g +$57 +- 23 (74 -> 75); FWt vs live v29fc goldg -$64 +- 122 (55 -> 56),
  top10g +$129 +- 57 (71 -> 75). Controller c0tp (wool+tomato fc) vs c0p (wool): +$16 +- 82 vs T8fcW, -$3 +- 76 vs FW (neutral).
  c2tr (herdpoor/majkel/other to the tape) goldg vs c0r: +$1,342 +- 940 (49 -> 57 wins); vs T8fcW +$101 +- 37 (tomato).
- Ladder by router class (ladder_class.py; recorded acts are offset: acts[t+1] = action at step t): PFcfc 64 games: chassis
  45/46 (tape), C2S3 2/5 (tape), herdpoor 3/5, other 3/5, herdfirst 3/3 (controller: 9/13). v29fc 41 games: chassis 30/30,
  herdpoor 6/6 (opp mean 795), other 3/4, herdfirst 0/1.
- REACTING HERD-TYPE OPPONENTS EXIST in pubnb/x_*.py (step-1 classes via max_steps=2 vs T8, flagged sources skipped):
  herdpoor: findings-from-zero-to-top-meta, strongest-farmer-of-today, x544-nah-i-d-win, limit-breaker-agent, weedproof-clone-
  market, adaptive-public-state-multi-route, breaking-the-tie, precomputed-schedule-policy, c01-scenario-v7-reproduction,
  counter-cyclical-orchard, two-reinforcement-learning-examples-from-kaito-v27, v21-r1-public-state-route-portfolio;
  herdfirst: v01-drip; other: c02..c06 ($636/6 hands), wide-sigma-cma, c07..c10 ($1,318/2), king-v4e-rc4, titan-frontier,
  shabby-farm, hamburger, notebooke394244546. herd_screen.py = one game each seat vs T8fcWt (seed 7400).
- 10:55 UTC stage B (top10g 270): c0tr vs c0r (tomato) +$37 +- 22 (69 -> 70); c2tr vs c0tr (routing) +$709 +- 170 (70 -> 76, all
  from Majkel1337 2 -> 8); c0tr vs live PFcfc +$75 +- 56 (68 -> 70); c2tr vs live PFcfc +$784 +- 178 (68 -> 76); goldg c2tr vs
  PFcfc +$1,070 +- 947 (50 -> 57: 吃白饭 5 -> 8, THIRD FARM 8 -> 14, mtmr -1, TheEggman -1, Yizhou -1, Kaggledew +1).
- The public herd-type agents are weak (T8fcWt beats them by $19k-$200k); herd_panel.py = c0tp / T8fcWt / FWt vs the 12 herd-poor
  agents, seeds 7500-7509 both seats (margins only; wins are 100%).
- Candidate pair: tape FWt (full_FWt.py) + controller c0tr or c2tr (full_OP_c0tr.py / full_OP_c2tr.py). Submit the tape first.
- 11:10 UTC herd panel (reacting, 12 herd-poor public agents x seeds 7500-7509 x both seats = 240 games each): controller c0tp,
  T8fcWt and FWt all 240/240 wins, no errors. Controller cash - T8fcWt -$1,809 +- 1,518, - FWt -$3,170 +- 1,488. Split: controller
  +$19-24k vs adaptive-public-state-multi-route, breaking-the-tie, strongest-farmer-of-today, v21-r1; -$13-27k vs findings,
  limit-breaker, weedproof, kaito-v27, x544. Weak opponents: no win-rate signal; the herd-poor win-rate evidence stays the elite gates.
- Submission files ready (gold/submit): main_ctl_FWt.py (sha 42196f53ee5585bd), main_ctl_c0tr.py (32f6ed0a12461193),
  main_ctl_c2tr.py (fb1b68e2b2581c2e); parse, load as `agent`, 48 benign pattern matches like the live files, step max 0.3-0.6 s.
- Ladder 10:30 UTC: PFcfc 2,391 (56/64), v29fc 2,345 (39/41). Daily slots: 29 Sep 4 of 5 used.
- 11:20 UTC Codex courier on the elite gates (routed courier1r vs routed base c0r, seat by seat): goldg -$167 +- 109 (49 -> 47 wins;
  THIRD FARM -$298 9 -> 8, 吃白饭 -$631 6 -> 5; 6-8 courier plans a game), top10g -$86 +- 62 (69 -> 68; Boey -$206 3 -> 2, FQ -$39,
  Majkel -$435 / -$674). Negative everywhere, including the herd matchups it targets. Every Codex controller idea is now closed:
  only the forecast seller (its first patch) is a gain.
- 11:35 UTC: c0tr goldg vs c0r +$75 +- 38 (49 -> 51), vs live PFcfc -$196 +- 103 (50 -> 51); c2tr vs c0tr goldg +$1,267 (51 -> 57).
  Codex update package codex_pkg/controller_v3/ + kagg_controller_v3_20260929.zip: results of every Codex controller idea,
  wool+tomato forecast, routing by class, reacting herd agents (herd_agents/), ladder by class, traps; asks A (class-specific
  openings via route["class_over"]), B (phase forecast from day 6 in the opening), C (larger designs); due 30 Sep 16:00 UTC.

### 29 Sep 12:00 UTC: Codex round 4 (E1 minimum liquidation, E2 opening forecast, E3 herd split)
- ctl_op.py (backup ctl_op_before_e1.py): opening knob `urgent_min` (None = old). plan_day and _open_midday now store
  `_open_need` = cost of the unfunded schedule (strawberries x $100 capped by free tiles, the next land price when due,
  missing animals capped by anim_day_max) minus the cash left after today's commitments (midday land hold: price - cash).
  In _sell_orders, with urgent_min set, urgent steps sell non-DP products as before but DP products (mkt_dp_prods) go
  through the forecast seller; then extra DP units, dearest first, only until need + buffer is covered. Telemetry
  gc_urg_* (every urgent step: value sold, value beyond the step's shortfall) and gc_e1_*.
- Trace, c0tp-equivalent e0 (identical game) seed 7000 vs T8fcW: 333 urgent steps (14 opening days), urgent sales $46,464
  ($23,901 premium), $33,299 beyond the step's shortfall.
- Builds (build_ctl2.py, pure route {"tape": []}, wool+tomato fc): e0 (trace only), e1a/e1b/e1c = urgent_min 0/100/250.
  e1_test.sh: vs T8fcW and FW 7000-7039 both seats (paired with fg_c0tp_*).
- 12:15 UTC E1 reacting (7000-7039 both seats, paired with fg_c0tp_*): e1a (buffer 0) vs T8fcW 40 -> 55 wins, flips L->W 18 /
  W->L 3, +$296 +- 444; vs FW 31 -> 42, 18 / 7, +$368 +- 563. e1b (+$100) vs T8fcW 40 -> 49, 12 / 3, +$460 +- 358; vs FW 31 -> 49,
  18 / 0, +$444 +- 377 (seeds 11 up / 0 down). e1c (+$250) vs T8fcW 40 -> 50, 15 / 5; vs FW 31 -> 37, 12 / 6, -$332. Our cash
  changes little (-$460..+$471): the gain is in timing against the rival. FIRST OPENING CHANGE THAT WINS.
- E3 herd features (herd_features.py -> herd_features.txt/json): herd-poor splits by step-1 money: $25 / 5 hands = tape copies
  (day 1: C2 S2 me12 wh7): controller +$19-24k vs 3 of them, -$5k/-$13k vs precomputed/x544 (second melon wave); $5-10 / 4-5
  hands = wool-heavy lineage (day 1: C1 S4 me5 wh5; 36-52 wool sold by day 10): controller -$19..-27k (it grows S6-S9 into their
  wool book). Gold-zone herd-poor elites are $17-18 / 4-5 hands at step 1 (bw_* replays).
- e1_confirm.sh: fresh towns 7700-7739 both seats (c0tp and e1b vs T8fcW, FW), herd panel e1b (herd_panel2.py), elite
  goldg/top10g for e1br (routed c0 + urgent_min 100). Also built e1b2r (routing c2 + urgent_min 100).
- 12:25 UTC E1 FRESH TOWNS 7700-7739 (both seats, paired): e1b vs c0tp: vs T8fcW wins 54 -> 50, -$456 +- 370, flips 7 / 11; vs FW
  47 -> 44, -$412 +- 404, flips 8 / 11. The 7000-7039 gain did not replicate; pooled money ~0, wins lean positive (flips 45 / 25).
  Third set 7800-7839 queued (e1_third.sh: c0tp, e1b, e1a vs both tapes).
- E2 patch (patch_phase_linear_wt_e2.py): GC_P edge_from_day (default 12) and edge_phys (no sale history -> goods sell at their
  earliest arrival: hidden stock now, cargo on landing, ripe tiles after the walk). e2a = e1b + from 6 + phys; e2h = from 6 only
  (identical to e1b on 7001: no history in the opening); e2p = phys only. e2_test.sh: e2a/e2p vs both tapes 7000-7039.
- 12:45 UTC E1 third set 7800-7839: e1a vs T8fcW 40 -> 47 (15/8) +$341, vs FW 27 -> 31 (10/6) +$91; e1b 40 -> 43 (13/10) +$499,
  27 -> 35 (14/6) +$493. POOLED e1a (7000 + 7800) vs T8fcW 80 -> 102 (33/11, p 0.001) +$318 +- 335, vs FW 58 -> 73 (28/13, p 0.03);
  e1b (3 sets) vs T8fcW 134 -> 142 (32/24) +$168 +- 221, vs FW 105 -> 128 (40/17, p 0.003) +$175 +- 216.
  Where the routed controller plays: herd panel e1b cash -$1,577 +- 983 (240/240 wins both); elite e1br vs c0tr goldg -$990 +- 903
  (51 -> 47: THIRD FARM 9 -> 7 -$4,640, 吃白饭 7 -> 5), top10g +$564 +- 484 (64 -> 66: FQ 3 -> 4 +$4,610, Boey +$592).
  E2a (E1b + from day 6 + phys) vs E1b: FW 49 -> 39 (2/12): rejected. E2p (phys only from day 12) +$176 +- 90 / +$78 +- 143.
  GPT's town router (Smoothie/Pizza first shop) fails on fresh 7700 seeds; only FARMERS_MARKET-first (+) and YARN_STORE-first (-)
  keep their sign (3-6 towns).
- 12:55 UTC: ChatGPT loop started (user's instruction): thread "Claude Workflow Chat" in the built-in browser; the browser has no
  file upload, so each round's README goes as text (typed line by line with shift+Enter; form_input flattens newlines).
  Round 1 = codex_pkg/gpt_round1 + kagg_gpt_round1_20260929.zip. GPT replies are research input only; no submissions without the owner.
- 12:57 UTC ChatGPT round-1 reply (research input): ship c2 + E1b (gate vs c2 base: no goldg win loss, >= +2 top10 wins);
  F1 = E1b but WOOL keeps the old urgent dump on days 5-10 while the rival shows >= 4 sheep (front-running hypothesis);
  instrument THIRD FARM/吃白饭 days 5-11; F2 = defensive liquidation by predicted price damage; herdpoor subtype router only if
  a step-1 separator exists; stop crop/animal quantity changes, delayed strawberries, fertilizer retention, courier labour,
  Smoothie/Pizza router, point-mass earliest-arrival forecast from day 6.
- ctl_op.py knob `e1_defend_wool` (backup ctl_op_before_f1.py); builds f1 (pure) / f1r (routed c0), e1bx (= e1b, identical).
  Smoke 7001: f1 == e1b vs T8fcW (defend fired 107 steps, no change); vs limit-breaker f1 +25,834 vs e1b +31,455 (rival +$5.2k).
- step1_dump.py: the five tape-copy herd agents (adaptive, breaking-the-tie, strongest, precomputed, x544) are identical at step 1
  ($25, 5 hands, same positions, one pasture at (4,4)); x544 stays identical through step 6; precomputed differs from step 2
  ($79 vs $106). No step-1 separator: the herdpoor subtype router is dropped (ChatGPT's own condition).
- r2_queue.sh: e1b2r top10g/goldg (c2 + E1b), c0tp/e1b vs v01-drip (herdfirst) 7500-7519, c0tp/e1b/f1 vs T8fcW and FW on fresh
  7900-7939, herd panel f1, goldg f1r.
- 12:59 UTC ARTIFACT CORRECTION of E1 elite results: goldg seat (113193141, 0) THIRD FARM: base c0tr us 173,713 m +87,212 (elite
  recording collapsed to $86.5k) vs e1br us 131,433 m -11,769 (elite $143.2k, as vs the tape). Excluding seats where the elite's
  cash swings > 20% between runs: e1br vs c0tr goldg -$99 +- 174 (50 -> 47; THIRD FARM +$325 8 -> 7, 吃白饭 -$853 7 -> 5), top10g
  +$87 +- 93 (70 -> 71; the FQ +$4,610 was also an artifact, (113831971, 1) elite 103k -> 48.8k). E1 is neutral on the elite gates.
- e1_instrument.py (days 5-11, wool/milk sales by hour): 吃白饭 seats 113103588/1 and 113513519/1: E1b vs base differ only in
  splitting the day-6 wool lot (2:3 + 3:3 instead of 2:6) and dripping day-10 milk; the -$2.6k..-$3.4k of our cash and +$3.5k..
  +$7k of the elite's come later (divergence compounding), not from the opening sales.
- E1a on 7700 set: vs T8fcW 54 -> 52 (7/9) -$343, vs FW 47 -> 38 (5/14) -$310. POOLED 3 sets: e1a vs T8fcW 134 -> 154 (40/20,
  p 0.013) +$98 +- 253, vs FW 105 -> 111 (33/27) +$50; e1b vs T8fcW 134 -> 142 (32/24) +$168, vs FW 105 -> 128 (40/17, p 0.003) +$175.
- 13:21 UTC round-2 queue results: fresh 7900-7939: e1b vs base vs T8fcW 47 -> 49 (10/8) -$362 +- 370, vs FW 30 -> 37 (14/7)
  +$544 +- 509; f1 identical to e1b on both panels (+$3, +$7, zero flips). Herd-first v01-drip 7500-7519: e1b vs base +$1,036
  +- 1,067 (40/40 wins both). c2+E1b (e1b2r) vs c2tr: top10g +$115 +- 69 without the artifact seat (76 -> 76; with it +$578,
  76 -> 77), goldg identical (all tape). Herd panel: f1 - e1b +$309 +- 438 (wool-heavy lineage +$866 +- 1,312), f1 - base
  -$1,269 +- 900. goldg f1r vs e1br -$15 +- 22 (47 -> 47). F1 null: the front-running hypothesis is not supported.
  E1b POOLED 4 sets (320 games each): vs T8fcW 181 -> 191 wins (42/32, p 0.3) +$35 +- 190; vs FW 135 -> 165 (54/24, p 0.001)
  +$267 +- 206. Ladder 13:22 UTC: tape v29fc 2,460.9, controller PFcfc 2,420.7.
- 13:45 UTC ChatGPT round-2 reply: keep E1b out of the final c2 build; trusted test = elite-derived reacting archetype agents,
  benchmark candidate - FWt; next = hand-over sweep (p1e controller vs herd-first, hand over at day 6..16); c2's tape branch should be
  FWt; stop E1 tuning / F1 / E2 / subtype routing / unstable-margin decisions; "if the deadline hit now: FWt + c2tr base".
- build_mix.py TAPE CTL OUT: one file embedding both sources (separate exec namespaces); step 0 = TAPE's move (identical in all our
  builds: BUY_PRODUCT WHEAT 10, SELL WHEAT 10, BUY_SEED WHEAT 1; step 1 identical vs copies too); at step 1 the CTL build's router
  (_OPR['cls'] vs its route['tape'] list) picks CTL or TAPE for the rest of the game. full_MIX_c2_FWt.py (2.9 MB) = FWt except vs
  herd-first rivals (c2tr controller): verified identical to FWt vs pub_metav4v13 and limit-breaker, identical to c2tr vs v01-drip.
- Elite (from rows): MIX goldg 56 / top10g 75 wins = FWt alone 56 / 75; c2tr (T8-based tape) 57 / 76. Controller vs FWt on
  herd-first elite seats: Fourth Quadrant -$1,376 +- 932 (3 vs 3 wins), Boey -$2,062 +- 1,121 (3 vs 3 wins, 29 stable seats).
- E1b POOLED 5 sets (8000-8039 added: vs T8fcW 48 -> 57, 17/8, +$688; vs FW 39 -> 38, 10/11, +$341): vs T8fcW 229 -> 248 (59/40,
  p 0.07) +$166 +- 169; vs FW 174 -> 203 (64/35, p 0.005) +$282 +- 174.
- Hand-over sweep (open.until = 6/8/10/12/14; h6..h14 pure, h6r..h14r c2-routed): sweep.sh runs the routed forms on hf60 (the 60
  Boey + Fourth Quadrant seats of top10g; gold/top10/gates/hf60_refs.jsonl) and the pure forms vs v01-drip 7500-7519.
- 13:46 UTC HAND-OVER SWEEP (vs FWt): hf60 elite seats (stable seats), controller - FWt: until 6 -$35,197 (10 stable), 8 -$31,692
  (12 stable), 10 -$7,022 (3 vs 3 wins), 12 -$3,385 (3 vs 6), 14 -$3,346 (2 vs 6), 16 -$1,713 +- 728 (6 vs 6). v01-drip (40 games,
  our cash vs FWt 162,371): until 6 -$49k, 8 -$72k (22/40 wins), 10 -$5.5k, 12/14/16 -$7.6k..-$7.9k. No hand-over day beats FWt;
  early hand-over breaks the farm. The p1e controller is below FWt in every rival class we can test.
- 13:58 UTC ChatGPT round-3 reply: don't submit MIX (= FWt); keep c2tr only if on stable herd-first elite seats p1e beats T8fcWt by
  >= +2 discordant wins with no losses, else the 2nd slot = T8fcWt; stop p1e research except herd-first flip mining; new idea:
  TAPE-META router between FWt and T8fcWt by rival class (class table of FW-only vs T8-only wins on stable seats, cross-validated by
  team; accept only >= +2 stable wins over both FWt and T8fcWt). Retire E1/F1/E2/hand-over/strawberry/melon/fertilizer/courier/
  allocation/town-router/subtype work.
- 14:03 UTC CLASS TABLE (class_table.py; T8fcWt elite rows = c2tr rows on tape-routed seats + r4_T8fcWt_hf60 on herd-first seats;
  all 381 paired seats opponent-stable): FWt vs T8fcWt wins / FW-only / T8-only: chassis 10 vs 11 (0/1), C2S3 86 vs 86 (1/1),
  herdpoor 21 vs 22 (1/2), herdfirst 6 vs 7 (0/1), majkel 5 vs 5 (1/1), other 3 vs 3 (0/0); totals 131 vs 134. Reacting: publics
  all wins, FW - T8 -$305 / -$249 / -$247; v01-drip +$253; herd panel +$1,361 +- 269. No class signal: the tape-meta router is moot.
  Elite totals: T8fcWt 57 / 77, c2tr 57 / 76, FWt 56 / 75. Herd-first stable seats (58): p1e vs T8fcWt 6 vs 7 wins, p1e-only 3 /
  T8-only 4, -$1,638 +- 736; p1e vs FWt 3 / 3, -$1,933 +- 707. Fails ChatGPT's keep-p1e bar (>= +2 discordant wins, <= 0 losses).
  Discordant herd-first seats: p1e-only wins at Boey 113687501/0 (rival step-1 2338/5), FQ 113316908/1 (1596/3), FQ 113568874/0
  (1033/4); tape wins at Boey 113065954/1, Boey 113808862/1 (2338/5), FQ 113686462/1 and 113709444/0 (393/4).
- 14:10 UTC ChatGPT round-4 reply (research input): freeze research; final pair FWt + T8fcWt (c2tr = T8fcWt with a slightly worse
  strategy on ~11% of games); one last analysis = common-loss audit (continue only if one archetype dominates); then a freeze
  preflight on the exact upload bytes (compile, no network/fs/ids/seed logic, clean process, both seats, big smoke, max step time,
  memory, state reset, stdout, size, determinism, gate counts reproduce) and save FWt_final.py, T8fcWt_final.py, SHA256SUMS.txt,
  FINAL_RESULTS.md.
- 14:15 UTC COMMON-LOSS AUDIT: both tapes lose 244 of 381 stable elite seats, spread over every top team (FQ 90%, DSM 87%, Boey
  87%, M&M 86%, DECEM 73%, Majkel 73%); ledger gap vs the elite on those seats WHEAT -5,329, EGG -4,902, STRAWBERRY -2,378, CARROT
  -1,990, WOOL -1,748, MILK -1,121, FERTILIZER -804, TOMATO -182, MELON +5,901. No single archetype or product -> stop (GPT's rule).
- 14:26-14:40 UTC PREFLIGHT (exact bytes gold/submit = gold/final, sha256 FWt 42196f53..., T8fcWt bf1da448..., c2tr fb1b68e2...):
  py_compile ok; stdlib imports only (base64 copy itertools json math random time zlib); the one open() sits behind path = None;
  the only game-seed read is an opening coin flip in dead code (_ALT_MODE = 'HybridOpening', not 'Mixed'); other 'seed' reads are
  crop seed prices. Smoke (preflight_smoke.sh, 12 opponents x 12 seeds x both seats, 288 games per file): 0 errors, 0 NaN,
  0 gc_errors (FWt 266 W 14 T 8 L; T8fcWt / c2tr 266 W 22 L, losses only to T8 and FW). preflight_state.py: determinism True
  (719 steps), state reset True, stdout 0 chars, memory flat (23-49 MB) for all three. preflight_timing.py (idle machine, 24 games
  each): max step 0.56 s FWt / 0.62 s T8fcWt / 0.64 s c2tr, always step 480 (day 20 hour 0), zero overage; under the 36-process
  smoke load FWt reached 4.45 s (overage bank 60 s/game). Live v29fc + PFcfc: 185 ladder games, all statuses DONE/DONE (livefetch
  14:34 UTC; ratings 2,480 / 2,444). Official kaggle_environments self-play (official_selfplay.py): DONE/DONE 720 steps.
  gold/final/{FWt,T8fcWt,c2tr}_final.py + SHA256SUMS.txt frozen (cmp-identical to gold/submit and to the gated cands builds).
- 14:47-15:00 UTC REPRODUCTION (repro_gates.sh): exact bytes on goldg + top10g: FWt, T8fcWt and c2tr each 381/381 seats identical
  to the frozen rows (56/75, 57/77, 57/76). Second smoke batch (6 opponents x seeds 8600-8619 x both seats): FWt 528 games total
  458 W 42 T 28 L, T8fcWt 528 games 468 W 60 L, 0 errors; only non-wins outside our tapes: FWt -$183 vs omw_v15a seed 8615 (both
  seats). Head to head over both batches: FW beat T8fcWt 42-22, FWt beat T8 53-11, T8fcWt beat T8 46-18. final_table.py/.txt.
  gold/final/FINAL_RESULTS.md written; files + hashes copied to ../../kaggriculture_FINAL_20260929/ (outside the working tree).
- 14:52 UTC ChatGPT round-5 reply: freeze; pure rank = FWt + T8fcWt, one-tape/one-controller = FWt + c2tr ("completely
  defensible", 1 elite win of 381); submit now, FWt first; replace only on crashes / repeatable class collapse; optional moonshot =
  day-1 market score switching between two existing policies, fresh seeds, >= +5 wins per 80 games vs both frozen agents.
- 15:00 UTC TOWN FINDING: shops unlock one random draw (with replacement) every 3 days from day 3, 8 instances. Final towns with
  no YARN_STORE (128/381, (7/8)^8): FWt wins 26% (-$4,898) vs 41% with one yarn store, 36% with 2+; goldg 40% vs 56%, top10g 19%
  vs 32%. In no-yarn towns us / elite: WOOL 4.8k / 5.9k, WHEAT 8.0k / 13.0k, EGG 5.9k / 10.5k, CARROT 6.8k / 8.1k, total -5.8k
  (vs -2.1k in one-yarn towns); the elite moves into wheat/eggs/carrots and buys fewer animals. 94 of 244 shared losses (39%).
  A day-1 score is impossible (no shops before day 3); by day 15 the split is 32% vs 39%. Not fixable safely before the deadline.
- 15:05 UTC ChatGPT round-6 reply: freeze final (FWt + T8fcWt untouched); one isolated challenger allowed, NY_SHEEP_CAP (no new
  sheep while day >= 16 and no yarn store visible), only if a feasibility audit shows post-day-16 sheep purchases on >= 25% of
  no-yarn seats or >= 0.5 sheep/seat; bar: +5 net wins/80 on a zero-yarn panel, <= 1 net win lost on a control panel, then >= +2
  net wins on the 128 elite no-yarn seats.
- 15:08 UTC SHEEP AUDIT (sheep_audit.py, exact frozen bytes, engine BUY_ANIMAL hook, margins identical to the gate rows): on all
  128 no-final-yarn elite seats T8fcWt and FWt buy 0 animals of any kind after day 16; every sheep is bought by the tape on days 0,
  8 and 9 (256 + 256 + 202, 5.6 per seat). NY_SHEEP_CAP would never fire -> not built. Round 7 (15:10 UTC) told ChatGPT the freeze
  is final.
- 16:05 UTC FINALS vs LIVE PAIR. Elite goldg+top10g (381 seats, 378 stable across all five; v31 rows = fc_phase_* (full_FC_phase.py
  == main_ctl_v29fc.py), v32 rows = fin_PFcfc_*): wins v31 v29fc 126 (55/71), v32 PFcfc 118 (50/68), FWt 131 (56/75), T8fcWt 134
  (57/77), c2tr 133 (57/76). Paired stable: FWt vs v31 7/3 (net +4, cash -$213 +- 58); T8fcWt vs v31 13/5; T8fcWt vs v32 26/9
  (+$1,171 +- 245); c2tr vs v32 22/6 (+$695 +- 184). By class v31/v32/FWt/T8fcWt/c2tr: herdpoor 20/12/20/22/22, majkel 5/1/5/5/5,
  other 3/1/3/3/3, chassis 8/10/10/11/11, C2S3 87/87/86/86/86, herdfirst 3/6/6/7/6. Head to head (vslive.sh, 9000-9039 both
  seats, 80 games): FWt vs v31 52-28 (+$63), FWt vs v32 43-37 (+$242), T8fcWt vs v31 41-39 (-$137), T8fcWt vs v32 41-39 (+$26);
  c2tr = T8fcWt there (both live files are chassis class). Live ladder (205 games): v31 77/103 (chassis 54/61), v32 83/100
  (chassis 65/68); ratings 2,463 / 2,465.
### 29 Sep 16:10 UTC: tape mix (owner: c2tr locked as the controller slot; push the tape by combining FWt and T8fcWt)
- DECOMPOSITION: FWt and T8fcWt differ in 7 diff blocks only: FWt = T8fcWt + the tape-plus section (879 lines, off when
  GC_P['tp'] is None) with tp = {nw4: 3, ne6, ne6_extra, fert_keeper, nw4_rival_max: 7}; same T8 tape, GoldCtl, hand-over
  (start 480, start_div 384) and forecast seller. nw4 = day-4 NW feed-wheat replants -> strawberries (skip if the rival holds
  > 7 strawberry plots); ne6/ne6_extra = day-6 NE wheat -> strawberries, only vs rivals _tp_is_div() (step-2 cash rule / ADAPT).
- SPOILER MECHANISM (same opponent/seed, FWt - T8fcWt): vs T8 ours -$668, rival -$987 (rival strawberry -$1,188, rival wheat
  +$374); vs v29fc -$567 / -$767; vs omw -$617 / -$911. Wins vs copies FWt/T8fcWt: T8 53/46, v29fc 52/41, PFcfc 43/41, omw 62/64,
  pub/sms 24/24. Elite 381: both sides lose cash when a layer fires (C2S3 ours -$406 elite -$400), wins 131 vs 134 (3/6, noise).
- Step-2 cash rule (div2_band 1000-1070 at step 2): all 381 elite seats divergent; T8-lineage + omw/pub/sms = copy.
- Package codex_pkg/kagg_tapemix_20260929.zip (owner attached it in the ChatGPT thread). ChatGPT: build CGt = T8fcWt + tp only
  when gc_div2 == copy (nw4 + fert + rival_max7; ne6 off); verify exact T8fcWt identity on divergent rivals; run the fresh gate;
  pair CGt + c2tr; no-yarn only if the fresh data shows a big reproducible regime.
- CGt = gold/top10/cands/full_CGt.py (from FWt_final.py: + _tp_copy() [_DIV2 'on' is False], nw4 condition + copy_only,
  tp = {nw4: 3, fert_keeper, nw4_rival_max: 7, copy_only}). Identity on 448 reacting games (smoke seeds 8200-8211 x 12 opponents,
  vslive 9000-9039 x 2): copies == FWt 280/280, divergent == T8fcWt 168/168, 0 errors.
- FRESH ELITE GATE fresh28 (tools/fresh_gate_build.py: 851 seats of top-45 teams on the 30 Sep LB from the 27-28 Sep daily
  datasets, cap 80/team, M&M (now rank 199) excluded; 289 no-yarn towns): FWt 133 / T8fcWt 131 of 850 stable (15.6% / 15.4%),
  FW-only 5 / T8-only 3, margin +$16 +- 58. Copy band: 1 of 851 (Boey, $1,053). Top teams improved sharply vs the 25-26 Sep gates
  (~35% win rate then): UMG 0/80, Vadim 2/80, DECEM 3/80, DSM 4/80, Boey 9/80, Victor 6/47, KawattaTaido 0/29; Azat 39/80,
  Anton 17/43, Majkel 18/80, FQ 15/61. No yarn regime (final yarn 0/1/2: 16/16/15%); fresh_analysis.py / fresh_analysis_tapes.txt.
  LB 30 Sep 16:21 UTC: rank 10 = 2,871.6, rank 30 (gold) = 2,735.2; offhand #174 at 2,456.
- 17:24 UTC CGt VERIFIED + FROZEN: old goldg+top10g 381/381 == T8fcWt (134 wins); fresh28 850/850 divergent == T8fcWt, the copy
  seat == FWt (132 wins); reacting 448/448 == predicted parent; preflight_state (determinism, reset, stdout 0, memory flat) and
  official self-play DONE/DONE x2. gold/final/CGt_final.py = gold/submit/main_ctl_CGt.py, sha256 d1eeea13544eb240...;
  SHA256SUMS.txt updated (4 files) + backup ../../kaggriculture_FINAL_20260929/. Sent the results to ChatGPT (17:30 UTC).
- 16:14 UTC the owner submitted c2tr_final.py himself as v33 (56681632; 2,429.7 at 17:30). Counting pair now v33 c2tr + v32
  PFcfc; 29 Sep UTC slots all used (5/5); CGt waits for 00:00 UTC. ChatGPT (17:32): CGt + c2tr, CGt first; one moonshot =
  what changed in the top teams between 25-26 Sep and 27-28 Sep.
- 17:50 UTC TEMPORAL (research/temporal: extract_t.py = openmine extractor on 25-28 Sep corpora, 40 games per team and batch,
  906 seats; temporal.py report -> temporal_report.txt): own final money barely moved (UMG +$1.8k, DECEM +$1.4k, DSM +$1.9k,
  Vadim -$2.7k). Common to 7/8 teams: fewer wheat tiles on days 12-25. UMG / Vadim / DECEM shared a structural shift: cows by
  day 6 2.5-3.0 -> 5.1-5.3; geese by day 9 1.7-2.6 -> 4.8 (Vadim, DECEM; eggs $8.1k -> $10.9k DECEM, $9.8k -> $11.2k Vadim);
  wheat tiles by day 9 7-10 -> 15-19 (then fewer later); tomato seeds 15-17 -> 3 (Vadim, DECEM), tomato sales ~$7k -> ~$2k;
  melons 1 -> 4 tiles on days 12-15; wages $6.3-6.7k -> $4.7-5.1k. Our CGt on 60 of those seats (extract_t.py ours, 12 wins,
  -$5,849): cows 4.0 @6, geese 0.0 @6 / 0.7 @9 / 2.4 @15, sheep 8.2 @15, wheat tiles 3 @6 / 5 @9 / 20 @12, 12 melon tiles on
  days 6-9, 28-29 strawberry tiles @12-15, eggs $3.7k. The egg gap (-$5.7k..-6.1k per game on fresh28) is our largest.
- 18:00 UTC ChatGPT: one moonshot EG_shift (vs divergent rivals, days 0-6 unchanged, advance the tape's day-10/11 geese and coop
  to days 7-8, tomato spend -> wheat, no extra hires/cash); feasibility trace first, abort if it needs new cash.
- 18:05 UTC EG_SHIFT ABORTED (feasibility, ours_CGt_days.jsonl on the 18 UMG/Vadim/DECEM seats): geese bought day 10 (2) + 11 (1)
  in 9 seats, day 6 (2) + 10-11 in 4, none through day 16 in 7; 4 free coops on day 10; tomato seeds days 6-9 only $200; min cash
  on days 6-9 $18-$860 (typically $250-500) until the day-11 early-melon payout ($14-18k), exactly when the tape buys the geese;
  7-9 hands busy. Advancing 2 geese ($600) needs cash the tape does not have -> not built. The elites afford early geese because
  they skip our early-melon cash cycle: a new opening, out of scope. Freeze final: v33 c2tr live, CGt at the UTC reset.
- 18:10 UTC c2tr on fresh28 (cgt_queue): 124 wins vs CGt / T8fcWt 132 of 851; herd-first seats 142 (Boey 78, FQ 54): stable 133,
  c2tr 14 vs T8fcWt 19 wins, c2tr-only 2 / T8-only 7 (p 0.18), cash -$5,174 +- 567 per herd-first game (old gates 3/4, -$3,107).
  ChatGPT (18:08): freeze confirmed; final plan v33 c2tr (live) + CGt at the UTC reset. Owner decides whether to keep c2tr.
### 29 Sep 17:50-18:25 UTC: v33 c2tr losing streak analysis (research/v33loss)
- v33 ladder (live_v33.jsonl, livefetch): 23-0 to 2,523, then 1-5 vs C2S3-lineage agents at 2,428-2,560 (Y & G -15.6k, RS
  Turley -9.9k, Siyuan Wang -23.2k, pangzi233 -10.7k, Tremble -7.8k; win vs QQ = copy of our tape) + lzeee (chassis class,
  step 0 = COW 1) -11.2k; 26-1 vs everything else; ~2,440 at 18:10. All five share the new top-team opening (step 0 WHEAT 5 +
  COW 1 + 3 SHEEP, step 1 5 hires + COW), unit actions 39-66/120 identical (forks/replays). Exact replays (extract_t job_elite):
  their day 9 = 6-8 geese, 18-21 wheat tiles; eggs $17-19k; bakery/brunch towns; our strawberries $10-16k (vs $32-45k in wins);
  deficit -5..-8k at day 15, -13..-19k at day 20. No public notebook (28 Sep sweep + latest versions via pub_refresh.py) has it.
- Blind replays (blind.py) of their recorded games in 20 fresh towns vs CGt: CGt 20/20, 14/20, 9/20, 16/20; blind replay of our
  own game 0/20 vs CGt (-$14k), so the new meta played adaptively >> our tape.
- Ladder mini-gate (ladder_gate.py: rival = repaired recording in its own town; the tape reproduces live within $60): full
  controller c0tp (route tape []) -10.9k / -7.4k / -23.6k / -9.8k vs tape -15.7k / -9.9k / -23.2k / -10.7k: no flips.
  c0tp blind replays 16/14/11/16 of 20 (level). FRESH28 c0tp 81 wins vs c2tr 124 vs CGt 132 (stable 13 vs 59, -$4,068 +- 262;
  C2S3 56 vs 82). The full controller is much worse; c2tr as-is is the best controller form.
- Package codex_pkg/kagg_ctl_newmeta_20260930.zip (3.1 MB) for ChatGPT; proposal: new-meta opening library (top-team day 0-15
  recordings routed by first shops, chassis repair layers) + GoldCtl from day 16.
- 19:00-19:45 UTC ChatGPT plan (owner-driven): tape-free direction, phase 1 = a new-meta branch vs the 960 band (step-1 rival
  money 940-980, no hands; fresh28: 420 of 851 seats = all UMG / DSM / DECEM / Vadim + most Victor); teacher (recorded opening
  replay) then student (distilled targets in the p1e profile); bar: >= 2 loss->win flips and 0 win->loss on the real ladder
  losses, >= 65/80 on the blind panels (tape 59).
- TEACHER NM1 (build_nm1.py: c2tr + Chassis replay of Vadim 114166771 seat 1 steps 1-383, step-0 buys merged into step 1,
  start_div2 = 384; cands/full_NM1.py): far worse on every 960-band game (Y & G -27.3k, RS Turley -13.4k, Siyuan -33.4k, pangzi
  -49.1k, Tremble -44.3k, azamat +9.4k -> -24.9k). trace_nm.py: desync from day 1 (a cow left in the shed all game after the
  step-1 pickup fails; daily FEED/CARE/COLLECT fails; coops not built -> geese in the shed; 4 wheat tiles on day 9 vs 20; 42
  wheat + 13 eggs unsold on day 12). Exact replay does not survive a different game. Remember: re-binding `agent` keeps its
  old dict slot -> end every patch with `_xxx_submission_agent = agent` (NM1 first loaded the parent).
- STUDENT NMp1/NMp2 (build_nmp.py: 960 band -> p1e controller with profile overrides: straw_max 26/22, fewer NE/SW
  strawberries, melon 12, geese 7-8 / 8-9 by day 9, anim_day_max 4/5): real losses NMp1 -10.9k / -4.0k / -20.2k / -5.1k /
  -13.0k (tape -15.7k / -9.9k / -23.2k / -10.7k / -7.8k), azamat +1.0k; NMp2 -13.5k / -1.2k / -17.8k / -8.6k / -8.2k, azamat
  -5.4k (a win lost). Zero loss->win flips. Blind panels NMp1 60/80 (tape 59, c0tp 57). Both fail the bar.
