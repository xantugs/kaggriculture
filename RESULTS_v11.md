# V11 — calibration against the public field, and four structural fixes

20 September 2026. Engine: kaggle-environments **1.32.7** (current; constants verified
identical to `kaggriculture.py` field by field — only key names differ).

`main_v11.py` SHA-256: `19df35c67d4f1287bb189a708d643df37b69a7d99ab8d0e23d3dffed6b10dfc3`

## Headline

**V11 beats the previous `main.py` 35W–5L–0T over 40 paired games (87.5%, 95% CI
74–95%), mean margin +$11,734.** Mean final cash $103,972 vs $92,237. Zero errors.

The win rate is the number that matters: the ladder scores wins and losses only, and the
final Bradley-Terry tournament is fitted on outcomes, not coin margins. Earlier project
results were reported as mean cash margin, which overstated some changes and understated
others — the V8 "selected" change, for instance, went 4W–4L, i.e. no ladder gain at all.

## What changed

| parameter | was | now | why |
|---|---|---|---|
| `goose0` / `ban_goose` | 3 geese, unlimited | 0, geese banned | eggs are break-even after wheat feed and cost ~3 unit-turns/day each |
| `max_sheep` | uncapped (reached 15) | 5 | wool's above-target curve is `sq` (amp 3.20); 15 sheep crashes realised wool to ~$33/unit |
| `max_land` | 3 extra quadrants | 2 | the 4th quadrant costs $4,000 and spreads the crew too thin |
| `hire_margin` | 2.5 | 1.5 | hires past the optimum cost more than the turns return |
| `cap_guard` | absent | on | V9 fix: sell down so the end-of-day drop fits under `shedCapacity`; validated 60.0% over 80 fresh games vs V8, plus 57.8% over an earlier 64 |

`fert_rev_w`, `herd_cap` and `sheep_share` were added as tunables and left at
no-op defaults; they measured neutral once `max_sheep` and `max_land` were in.

## Where this agent actually stands

Calibrated against Rayk Kretzschmar's MIT reference ladder (tiers 0–5) and against two
public route-replay agents. Three paired seeds, both seats, six games per opponent.

| opponent | W/L | my cash | their cash | margin |
|---|---:|---:|---:|---:|
| Fallow Finn (tier 0, passive) | 6/6 | $168,883 | $3,000 | +$165,883 |
| Wheat Walter (tier 1) | 6/6 | $162,832 | $6,646 | +$156,186 |
| Rotation Rosa (tier 2) | 6/6 | $144,318 | $11,722 | +$132,596 |
| Homestead Hana (tier 3) | 6/6 | $154,798 | $13,558 | +$141,239 |
| Melon Mateo (tier 4) | 6/6 | $149,924 | $9,100 | +$140,824 |
| Rancher Rita (tier 5) | 6/6 | $115,198 | $13,090 | +$102,107 |
| a public hand-written planner | 6/6 | $129,875 | $42,895 | +$86,980 |
| an early public route-replay tape | 2/6 | $91,144 | $100,892 | −$9,748 |
| a current public route-replay tape | 0/6 | $76,811 | $120,896 | −$44,085 |
| previous `main.py` (V8) | 3/6 | $106,827 | $97,250 | +$9,577 |

**Overall 50/66 = 75.8%.** The agent beats every hand-authored reference agent decisively
and beats other people's closed-loop planners. It loses to route-replay tapes. Against a
passive opponent it banks $168,883 where the shared public meta line banks ~$186,000 —
about 9% short in raw production, but much further behind in contested play, which means
the tapes are better at taking market share, not just at producing.

Tuning moved the deficit against the current strong tape from −$49,396 to −$33,832
(16 games, 0W), and against the earlier tape from −$15,473 to −$7,561 with 3 wins in 10.
Further parameter search on fertilizer weighting, hold policy, discounting, investment
hurdles and melon targets all measured within noise.

## Reliability

`actTimeout` is **1 second per turn** with a 60-second overage bank. Measured over a full
719-turn game against the strongest opponent: **mean 2.04 ms, p99 5.45 ms, max 7.27 ms,
zero turns over 1 s.** Roughly 140× headroom at the worst turn. Standard library only
(`math`, `time`); `agent` is the last callable; `DEBUG = False` so the try/except fallback
is live. 106 games run during this review with **zero errors and zero non-DONE statuses.**

The flip side: the agent uses about 0.2% of its allowed compute. That headroom is the
largest untapped resource in the project.

## Competition facts that shape strategy

- **9,644 teams.** Gold ≤ rank 29 (2913.6), Silver ≤ 482 (2616.9), Bronze ≤ 964 (2432.5).
- Entry deadline 23 Sep; final submission 30 Sep; games continue to ~15 Oct, then a
  Bradley-Terry tournament over those two weeks produces the final leaderboard.
- Five submissions per day, but **only the latest two are tracked** and those two are
  what enter the final evaluation. Every new submission restarts at rating 600 and is
  ~90% converged after ~60 games (~5 hours). Re-submitting an unchanged agent buys a
  nicer live number and nothing else.
- The live leaderboard is not the final ranking. What matters on deadline day is two
  strong, error-free agents in the two slots.

## Engine mechanics worth keeping in view

Read directly out of `kaggle_environments/envs/kaggriculture/kaggriculture.py`:

- `SELL` fills **only from `private["shed"]`** and aborts when the shed runs dry; carried
  unit inventory never counts. Our sizing is already correct on this point.
- `BUY_PRODUCT` is quoted at *post-buy* inventory, so a buy/sell round-trip against an
  unchanged market nets exactly zero. There is no price-spread arbitrage.
- **Melon appears in no shop**, so nothing ever drains it — a fixed one-shot pot of about
  $26k. Worth collecting, not worth scaling.
- Milk and strawberry are *linear* above target and absorb volume; melon and wool are
  quadratic and collapse. Lean on the first pair.
- One `FERTILIZE` covers two strawberry production events, taking a tile from 4 units to
  8 over its life. Fertilizer is not scarce: every animal tile regenerates one per day.

## Reproduce

From the project directory, with the pinned environment:

```powershell
..\.venv\Scripts\python.exe tools\benchmark.py --opponents v8 -n 20 --seed0 90000
```

Seeds used here: 70000–70039 (cap_guard), 80000–80003 and 85000–85009 (screening),
86000–86002 (ladder), 90000–90019 (final validation). Screening seeds and validation
seeds are disjoint. Screening ran one seat only; every headline number above is both
seats, paired.

## What is not established

- The tuned parameters were selected against two public tapes and validated on fresh
  seeds against the previous champion. They have never met the actual ladder population.
- `hire_margin` 1.8 looked best on four seeds and turned out to be noise on ten. Treat
  any effect under about $8,000 on fewer than 20 paired games as unmeasured.
- No submission has yet been made, so the agent's real rating is unknown.
