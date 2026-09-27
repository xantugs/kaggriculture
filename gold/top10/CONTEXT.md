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

## Leads open on 27 Sep (from the other session's last hours, code lost with its container)
- Copy takeover day 22 instead of 24: +$760 +- 163 a game on the 105 live copy games (93 -> 96 wins), measured on sf6.
  Being re-measured on sf8 (days 21/22/23) by the main session.
- 11 divergent live games lose sheep right after the day-16 takeover (escapes), e.g. vs XJHya233.
- Night-drop shed overflow: ~$880 a game of goods discarded (29 of 106 games > $1k), days 23 and 26 mostly; one game
  (Ryui68925, day 26) harvested 218 units against a 98-unit night room with every hand booked to hour 23. A forced
  courier and an hour-23 room sale both failed to pay; cheaper idea: skip harvests/pickups that would only be discarded.
- Early wool sale variants (ces15/ces25) rejected.
