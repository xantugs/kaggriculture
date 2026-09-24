# gold/ — takeover controller experiment (24 Sep 2026)

`ctl.py` is a full controller appended to the live chassis (`base_v15a_adapt.py` = uploaded v15a + ADAPT).
From `GC_P['start']` (hour 0 of a day) it owns every unit and the market: daily job valuation, hires by
marginal value vs Fibonacci wage, cheapest-insertion VRP routing (3 insertion orders + 2-opt), shed stops
only when the end-of-day load would overflow, dynamic feed/fertilizer reserves, final-day delivery.

Build: `python3 build.py out.py '{"start": 288, "max_hands": 14, "drop_slack": 0}'`

## Status (closed loop vs live v15a, seeds 6000-6009, both seats, decoupled engine)

| version | takeover | mean margin |
|---|---|---|
| v1 | day 10 | about -$50k (shed overflow, no deliveries) |
| v3 | day 12 | -$15.0k |
| v11 | day 12 | **-$10.5k** (best) |
| v16 | day 12 / 20 / 24 | -$12.1k / -$6.0k / -$3.5k |

Pinned strong-team replays from day 12 (v6): -$18.2k vs the chassis continuation (copies -$19.3k, divergent -$15.8k).

The remaining gap is production volume, not price: strawberries (production-eve waterings dropped when labour is
tight), wool (occasional escapes, skipped care), wheat, and fertilizer sold. The chassis converts what are idle
turns for us into many small useful actions; matching its labour efficiency is the open problem.

## Diagnostics
`diag.py` (daily census), `flowdiag.py` (harvest/sold/lost per product), `plandiag2.py` (daily plans),
`opcmp.py` (action counts per day, both seats), `prodaudit.py` (doubled vs single ongoing-crop productions),
`strawlife.py`, `escdiag.py`, `fertdiag.py`, `sellpat.py`, `eodiag.py`, `wheatdiag.py`, `chroutes.py`.
