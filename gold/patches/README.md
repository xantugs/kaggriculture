# m5 + sells-first (market order index) + divergent-path day 29

Built on the other session's branch `claude/adoring-sagan-kcq65p` (not merged here):
`gold/ctl.py` (sha256 284cfde5...), `gold/base_m7_t4.py`, `gold/cfg/cfg_m5.json`, and the lean m5
`gold/submit/main_ctl_mkt5_lean.py` (sha256 61cc0b49...).

- `m5_sells_first.patch`: against that `gold/ctl.py`. Every new switch defaults off (m5 plays unchanged):
  `sells_first`, `sells_first_chassis`, `sells_first_slots`, `sells_first_sort` (the market-order index fix),
  `mkt_dp_d29` (the programme also times day 29), plus probes that were rejected or neutral
  (`sells_first_div_sort`, `sells_first_slots1`, `sells_first_order`, `sells_first_dp_due`, `fert_h0`,
  `race_from`/`race_to`, `mkt_dp_d29_prods`).
- `bm5.py`: base + patched ctl + cfg_m5 merged with overrides (`div_over`/`rich_over` merge key by key).
  The candidate `sf5b`:
  `{"sells_first": true, "sells_first_chassis": true, "sells_first_slots": true, "sells_first_sort": true,
    "div_over": {"mkt_dp_d29": true, "final_sell0": 0, "final_cap": 21}}`
- `lean_patch.py`: the same changes on the lean file, options hardcoded:
  `python3 lean_patch.py main_ctl_mkt5_lean.py out.py '{"sort": true, "slots": true, "div29": true}'`
  (lean sf5b plays identically to the full sf5b build on all 210 elite-gate seats and 40 closed-loop games).
See `gold/README.md` (26 Sep afternoon) for the gates.

## sf6 / sf7 (26 Sep, night)
- `m5_sells_first.patch` (regenerated) also carries `mkt_dp_cap` use in `div_over` (a config value, no code),
  `cash_guard_min` (new, default 0) and the rejected/inert probes `early_harvest`, `mkt_dp_w_behind`/`_ahead`,
  `anim_fwd_days` (all default off).
- **sf6** = sf5b + `"div_over": {"mkt_dp_cap": 30}` (bm5 overrides:
  `{"sells_first": true, "sells_first_chassis": true, "sells_first_slots": true, "sells_first_sort": true,
    "div_over": {"mkt_dp_d29": true, "final_sell0": 0, "final_cap": 21, "mkt_dp_cap": 30}}`).
  Lean: add `'mkt_dp_cap': 30` to the lean sf5b's `div_over` literal (one edit; `c_lsf6.py`, certified identical
  on the 249 pinned games).
- **sf7** = sf6 + `"cash_guard_min": 5`: on day 0 the chassis's seed orders never take the cash below $5, so the
  day-1 hires always happen (a rival's step-0 wheat trading once left us at $0, no hands, two cows escaped).
  Lean: `python3 lean_patch_cg.py lean_sf6.py lean_sf7.py` (certified identical to the full sf7 on the broke games).
