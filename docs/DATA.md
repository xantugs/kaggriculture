# Data not in this repository

The working tree was about 5.15 GB. Almost all of it was game replays and evaluation output, so those files are left out of git, including its history. They are available on request, and may be published later as a GitHub Release.

Paths below refer to the `research` branch. The extension rules are in `.gitignore`; the size-based ones are listed below.

## What was left out

| Category | Files | Size |
|---|---:|---:|
| Raw replays and run logs (`replays/`, `logs/`) | 241 | 152.1 MB |
| Evaluation output and replay dumps (`*.jsonl`, `*.gz`, `*.pkl`, `*.bin`) | 5,799 | 2.86 GB |
| Public-notebook bundles (`kgbundle_*.json`) | 2 | 62.2 MB |
| Other files over 5 MB | 11 | 140.8 MB |
| Single-game replay dumps (`*.json`, 200 KB and up) | 325 | 112.2 MB |
| Arrays and archives (`*.npz`, `*.zip`) | 5 | 8.8 MB |
| Generated candidate builds (`gold/top10/cands/`, about 1.4 MB each) | 956 | 1.36 GB |
| **Total** | **7,339** | **4.70 GB** |

The candidate builds are generated agent files rather than data. The build scripts and the final agents are kept.

## By directory

| Directory | Files | Size |
|---|---:|---:|
| `gold/top10/research/` | 5,107 | 1.68 GB |
| `gold/top10/cands/` | 956 | 1.36 GB |
| `gold/top10/gates/` | 269 | 963.5 MB |
| `moon/` | 300 | 209.4 MB |
| `replays/live_0926/` | 198 | 112.5 MB |
| `moon/elite/` | 7 | 87.4 MB |
| `public_kernels/` | 2 | 62.2 MB |
| `gold/elite/` | 116 | 39.2 MB |
| `moon/kout/` | 4 | 38.5 MB |
| `moon/g2800/` | 131 | 34.6 MB |
| `logs/` | 26 | 30.6 MB |
| `moon/g_hold/` | 81 | 21.4 MB |
| `moon/g_fresh16/` | 46 | 12.1 MB |
| `arena/cf/` | 13 | 12.1 MB |
| `replays/` | 17 | 9.0 MB |
| `agentic_planner/rl_pilot_20260923/` | 5 | 8.8 MB |
| `moon/g_fresh17/` | 24 | 6.3 MB |
| `gold/top10/audit_handover/` | 17 | 1.4 MB |
| `agentic_planner/codec_samples/` | 4 | 1.1 MB |
| `arena/runs/` | 14 | 0.8 MB |
| `review_20260921/` | 1 | 0.7 MB |
| `review_20260921/top10_reconciliation/` | 1 | 0.4 MB |

## Files over 5 MB

| File | Size |
|---|---:|
| `gold/top10/gates/crawl/sample_games.jsonl` | 363.3 MB |
| `gold/top10/gates/live0927.jsonl` | 111.5 MB |
| `gold/top10/research/openmine/elite_days.jsonl` | 101.7 MB |
| `gold/top10/gates/live0928_T5T8.jsonl` | 98.9 MB |
| `gold/top10/research/opening/live_v3132.jsonl` | 79.9 MB |
| `gold/top10/gates/crawl_refs.jsonl` | 70.0 MB |
| `gold/top10/research/temporal/elite_days.jsonl` | 68.3 MB |
| `gold/top10/research/openmine/herd/compact.jsonl` | 63.1 MB |
| `gold/top10/research/openmine/land_cash/cache_days.pkl` | 61.3 MB |
| `gold/top10/research/openmine/labour/rows.pkl` | 60.6 MB |
| `gold/top10/research/opening/live_losses_all.jsonl` | 56.4 MB |
| `gold/top10/research/opening/live_v31v32.jsonl` | 53.6 MB |
| `gold/top10/research/opening/live_v30v29.jsonl` | 52.1 MB |
| `moon/elite/part_0922.jsonl` | 46.4 MB |
| `gold/top10/research/opening/live_final_pair.jsonl` | 40.8 MB |
| `public_kernels/kgbundle_2.json` | 39.9 MB |
| `gold/top10/gates/fresh28_refs.jsonl` | 38.8 MB |
| `gold/top10/research/opening/live_pf_losses_src.jsonl` | 37.0 MB |
| `gold/top10/research/opening/live_v33.jsonl` | 37.0 MB |
| `moon/strong2800.json` | 34.6 MB |
| `moon/kout/il_rows.jsonl.gz` | 33.1 MB |
| `logs/diagnosis_v9_match.pkl` | 30.3 MB |
| `gold/top10/research/openmine/sf/out/c6_top10g_days.jsonl` | 26.4 MB |
| `gold/top10/gates/fresh29_refs.jsonl` | 26.2 MB |
| `gold/top10/gates/crawl_games.jsonl.gz` | 25.7 MB |
| `gold/top10/research/openmine/crops/days.pkl` | 24.9 MB |
| `gold/top10/research/opening/live_v3435.jsonl` | 23.0 MB |
| `public_kernels/kgbundle_1.json` | 22.4 MB |
| `moon/hold2700.json` | 21.4 MB |
| `gold/top10/research/openmine/crops/tiles_elite.jsonl` | 20.3 MB |
| `moon/recent_loss.json` | 14.0 MB |
| `gold/top10/gates/fresh960_refs.jsonl` | 13.9 MB |
| `gold/top10/gates/top10g_refs.jsonl` | 13.5 MB |
| `gold/top10/gates/fresh28_games.jsonl.gz` | 13.0 MB |
| `moon/strong_new.json` | 12.8 MB |
| `moon/elite/games_2026-09-20.jsonl.gz` | 12.6 MB |
| `moon/elite/games_2026-09-21.jsonl.gz` | 12.5 MB |
| `moon/fresh16_games.json` | 12.1 MB |
| `moon/v12_all_0922.json` | 12.0 MB |
| `moon/elite/games_2026-09-22.jsonl.gz` | 12.0 MB |
| `gold/top10/research/mix/out/diag_24.jsonl` | 11.1 MB |
| `gold/top10/research/mix/out/diag_23.jsonl` | 11.1 MB |
| `gold/top10/research/mix/out/diag_26.jsonl` | 11.0 MB |
| `gold/top10/research/mix/out/diag_25.jsonl` | 10.9 MB |
| `gold/top10/research/openmine/sf/out/c7mcs_goldg_days.jsonl` | 10.1 MB |
| `gold/top10/research/openmine/sf/out/c7c_goldg_days.jsonl` | 10.1 MB |
| `gold/top10/research/openmine/sf/out/c6_goldg_days.jsonl` | 10.0 MB |
| `gold/top10/research/openmine/sf/out/c7_goldg_days.jsonl` | 10.0 MB |
| `gold/top10/research/openmine/sf/out/c7m_goldg_days.jsonl` | 10.0 MB |
| `gold/top10/research/openmine/sf/out/c7u12_goldg_days.jsonl` | 9.9 MB |
| `gold/top10/research/openmine/sf/out/c7t_goldg_days.jsonl` | 9.7 MB |
| `gold/top10/research/mix/out/top10g_rest_refs.jsonl` | 9.0 MB |
| `moon/saleprof_omw_ad_a1_MIRROR.json` | 9.0 MB |
| `gold/top10/research/labour/r3/top10g180_refs.jsonl` | 9.0 MB |
| `gold/top10/gates/fresh29_games.jsonl.gz` | 9.0 MB |
| `gold/top10/research/openmine/hf/out_T8oth.jsonl` | 8.2 MB |
| `gold/top10/research/market/top10g_fills.jsonl` | 8.2 MB |
| `gold/top10/research/openmine/hf/out_p1_oth.jsonl` | 8.0 MB |
| `gold/top10/research/labour/goldg_T5_hl.jsonl` | 7.9 MB |
| `gold/top10/research/phase/gapday_goldg_sf8.jsonl` | 7.8 MB |
| `gold/top10/gates/au_market/probe_T5.jsonl` | 7.7 MB |
| `gold/top10/research/mix/out/gdiag_top10g_rest.jsonl` | 7.6 MB |
| `gold/top10/research/openmine/hf/out_p1_80.jsonl` | 7.6 MB |
| `gold/top10/gates/fresh960_games.jsonl.gz` | 7.5 MB |
| `gold/top10/research/openmine/hf/out_i4_80.jsonl` | 7.5 MB |
| `gold/top10/research/openmine/ours_T7_opp_days.jsonl` | 7.4 MB |
| `gold/elite/elite_gate_refs.jsonl` | 7.3 MB |
| `moon/saleprof_omw_ad_a1_DIVERGENT.json` | 7.2 MB |
| `gold/top10/research/endgame/data/eg_dl_goldg_T5.jsonl` | 7.0 MB |
| `gold/top10/gates/fresh29_hf_refs.jsonl` | 6.7 MB |
| `gold/top10/research/market/goldg_fills.jsonl` | 6.6 MB |
| `gold/top10/research/endgame/data/dl_top10g.jsonl` | 6.6 MB |
| `gold/top10/gates/lad24_refs.jsonl` | 6.5 MB |
| `gold/top10/research/phase/gapday_top10g_sf8.jsonl` | 6.5 MB |
| `moon/fresh17_games.json` | 6.3 MB |
| `gold/top10/research/openmine/ours_T7_days.jsonl` | 6.1 MB |
| `gold/top10/gates/hf60_refs.jsonl` | 6.1 MB |
| `gold/top10/research/endgame/data/eg_dl_t10_T5.jsonl` | 6.0 MB |
| `moon/top_probe.json` | 5.9 MB |
| `gold/top10/gates/crawl/episodes.jsonl` | 5.8 MB |
| `gold/top10/research/phase/gapday_T5hyb22_top10g.jsonl` | 5.6 MB |
| `gold/top10/research/phase/gapday_hyb22_top10g.jsonl` | 5.6 MB |
| `gold/top10/gates/live_v27_fills.jsonl` | 5.6 MB |
| `gold/top10/research/phase/gapday_T5hyb16_top10g.jsonl` | 5.5 MB |
| `gold/top10/research/phase/gapday_hyb16_top10g.jsonl` | 5.5 MB |
| `moon/strong_v9.json` | 5.5 MB |
| `gold/top10/gates/top10g_games.jsonl.gz` | 5.5 MB |
| `gold/top10/research/phase/gapday_hyb12_top10g.jsonl` | 5.4 MB |
| `gold/top10/research/phase/gapday_top10g_T5hfx13.jsonl` | 5.2 MB |
| `gold/top10/research/phase/gapday_top10g_T5.jsonl` | 5.2 MB |
| `gold/top10/research/labour/top10g80_hl.jsonl` | 5.2 MB |
