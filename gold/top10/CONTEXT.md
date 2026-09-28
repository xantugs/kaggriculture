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
