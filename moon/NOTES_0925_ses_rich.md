# 09-25 notes from the eval session (SES layer, v19, rich_m7 eval)

Scope split: this session works on everything except the GOLD controller (chassis before takeover, loss
diagnosis, benchmarks, evaluating GOLD files). The GOLD session owns `GoldCtl` / `GC_P`.

## SES layer = v19 (staged, NOT submitted)
- `moon/ses_layer.py`, built with `moon/build_ses.py out [cfg] [base=adapt]`. It inserts the layer before GOLD.
- What it does: when all 4 day-12 shops are strawberry shops (BRUNCH / ICE_CREAM / SMOOTHIE / FARMERS_MARKET),
  it does the following on day 12:
  - buys the SE quadrant and plants 25 strawberries;
  - runs a crew of ≤ 2 hands whose top priority is watering whatever would otherwise die, then fertilizes at age 9, harvests, and sells its own units.
- It masks SE from ADAPT's similarity check.
- It turns itself off in towns with ≥ 3 tomato shops, because the chassis' V219 day-18 tomato block needs SE.
- `arena/cand/ses_d.py` = `submit/v19/main.py` = v18 + SES.
- Closed loop vs v18 on 150 seeds where all 4 shops buy strawberries (`moon/ses_seeds.json`, 300 games):
  **250-42-8, +$6.2k/game**.
- It fires in about 6% of towns.
- Why the gate is 4/4: a 3-of-4 gate loses money (extra supply crashes the price of the chassis' own 33 strawberries).

## rich_m7 (GOLD session's `main_ctl_rich_m7.py`) — evaluation
- **The raw file ships the OLD v16d chassis knobs.** The differences from v18:

  | Knob | rich_m7 | v18 |
  |---|---|---|
  | `V9_FERT_FIRST_DAY` | 14 | 10 |
  | `V9_RACE_DEFAULT` | 40 | 50 |
  | `_CA_MARGIN` | −12 | −18 |
  | `_OR2_SLOT_H` | 8 | 10 |

  As a result, raw vs v18 in closed loop is **91-109-0**. Please build on `arena/cand/adapt.py`, or always graft
  the GOLD section (`moon/graft_gc.py`).
- Grafted onto v18 (`arena/cand/rich7.py`), it is identical to v18 except in rich towns.
  - Closed loop seeds 0-99: 37-31-132 (+$123).
  - Official runner max step 0.198 s.
- **Towns where all 4 shops buy strawberries:** rich takeover 203-97 (+$5.7k) vs SES 250-42-8 (+$6.2k) on the
  same 300 games, so SES is better there.
  - The exception is towns with ≥ 3 tomato shops, where SES skips: rich goes 12-8.
- **Towns where 3 of 4 shops buy strawberries** (150 seeds, `moon/rich3_seeds.json`):
  - rich fires in 80/300 games and goes 42-38 (+$680) — marginal.
  - The outcome is decided by the NEXT shops, not visible at day 12:

    | Shops 5 and 6 | Record | Margin |
    |---|---|---|
    | neither buys strawberries | 0-18 | −$5.4k |
    | only one of the two does | 22-18 | |
    | both do | 20-2 | +$4.7k |

  - Shop 5 unlocks at day 15 (step 360).
- Pinned wins over 282 games (train, hold, fresh16, fresh17):

  | Agent | Wins |
  |---|---|
  | v18 | 170 |
  | v19 | 177 |
  | rich7 | 179 |
  | hybrid | 181 |

  fresh17 implied rating: rich7 2771 vs v19 2741.

## Hybrids (in `arena/cand/`)
- `rich7h.py` — v19 (SES) + rich7 GOLD, but rich only when exactly 3 of the first 4 shops buy strawberries
  (new `GC_P['rich_max']` = 3). SES handles towns where all 4 do.
  - Closed loop seeds 0-99: **40-26-134 (+$481)**, vs rich7 37-31-132.
- `rich7d.py` — like rich7h, but the rich check runs at step 360 (day 15) on the first 5 shops, needing ≥ 4
  strawberry shops (`rich_nshops` 5, `rich_min` 4, `rich_max` 5). It gives up one production to skip the
  towns where shop 5 doesn't buy strawberries. **Closed loop running.**

## Tools
- `moon/evalnew.sh their_file.py name` — the full eval: timing, fresh16/17, train/hold, closed loop vs v18.
- `moon/cl_split.py` — splits a closed-loop jsonl by strawberry-shop count and by rich firing.
