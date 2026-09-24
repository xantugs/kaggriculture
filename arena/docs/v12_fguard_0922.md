# Kaggriculture: v12, the fertilizer guard (22 Sep)

**Status (22 Sep, 08:45 UTC).** v12 submitted as **56459281** ("v12", plain `main.py`, 1,058,902 bytes, sha256 `caffc2ba0457e32e…`) = public One More Wheat `main.py` + v11 layers + FGUARD + WFEED. It replaces v10 in the latest-two pair (v11 + v12).
- Ratings at submission: v10 2815 (51-7), v11 2804 (41-4, climbing after a dip to 2733).
- **Validation passed** (episode 111955614, self-play 71,648 / 72,296). Local self-play of `cand/omw_v12.py` on seed 0 reproduces it exactly.
- The eligible pair is now **v11 (56454323) + v12 (56459281)**; v10 dropped out.
- Head-to-head vs v10: **28-0, +$1,017/game** (min +$21). v11 vs v10 was 28-0, +$744.
- vs public rr7/sms/v53/yum/prv: 40/40 wins.

## v11 check
- v11 was never broken. The dip came from three losses in four games:
  - TheEggman (−$12.7k) and fuxi (−$12.5k): strawberry-poor towns (0–1 strawberry shops by day 9). v10 loses both the same way in replay (−12.8k, −12.4k).
  - Ugnė (−$201): a coin flip (v10 +178 in replay).
- Live v11 matches the local build move for move.
- **The real ceiling is shared by both versions:** v10 was 10-1 vs teams rated 2750–2805 but **0-5 vs 2809+**; v11 was 0-1 there.

## The six losses to 2810+ teams
| rival | margin | cause |
|---|---:|---|
| feel the agi (2836) | −3.9k | Different farm: +58 tomatoes (+$12k) and +92 eggs |
| KouFu (2831) | −2.8k | +17 milk (~$4.2k), +20 tomatoes |
| shyjin (2809) | −1.1k | omw + tweaks: sells day-28 strawberries in small lots before our 689 sale; collects fertilizer instead of doing useless late care |
| Kaggriculture Agent (2814) | −0.9k | Wheat speculation (3,228 sold / 3,042 bought); mostly break-even round trips plus more wheat/melons/eggs |
| URAD (2845) | −0.9k | Mirror until day 23, then carrots instead of wheat on days 23–24 (our carrot swap stops on day 23 and at a 40-wheat reserve) |
| QQ农场 (2821) | −0.8k | Mirror with **0 failed fertilizings vs our 4**, +6 strawberries, and a day-28 strawberry drip |

## What v12 fixes
1. **FGUARD (the R97 supply guard, for fertilizer).**
   - The route tape sometimes sells fertilizer at step t and picks up more at t+1 than the shed then holds.
   - The short unit's FERTILIZE is a no-op. That happens about 1.5 times per game, almost always on strawberries.
   - When next turn's tape pickups exceed what this turn's orders leave in the shed, the guard first trims this turn's fertilizer sale, then tops up the purchase.
   - In QQ's game it removes all 4 failures, and our fertilizings then match QQ's exactly (strawberry 65→68, wheat 49→50).
2. **WFEED.**
   - On day 26 the farmer picks up 1 wheat at step 625 and feeds twice (629, 641). The tape expects wheat from a harvest at 634, but the carrot swap had turned that tile into carrots.
   - So the second feed fails and a goose (sometimes a sheep) escapes. This happens in about 28% of games.
   - WFEED sizes a unit's wheat pickup to the FEEDs its tape gives it before the next pickup.

## Evidence
| test | result |
|---|---|
| 114 real games, prefix replay from step 144, real town | **v12 +$206/game** (median +$56), 65 better / 25 worse, flips +1 / −0. FGUARD alone +$167; buy-only FGUARD +$24 (the trim does the work) |
| Closed loop, 14 seeds × 2 seats vs v11/v9/dm29/mv13 (112 games) | **v12 +$283/game** margin, +$100 money, **18 flips to wins, 0 to losses**. vs the v11 mirror: 18 wins, 10 ties, 0 losses |
| Timing | max 0.11 s/turn, no errors |

- Worst replay case (−$445 vs Roman Katasonov): the 4 extra strawberries went into a crashed book. In glutted strawberry books the marginal strawberry can be worth less than nothing.

## Tested and rejected today
- **Earlier day-28 pre-emption** (673/677/681/685 vs 689), 114 games from step 648: −$168 / −$80 / −$57 / −$34 per game, net negative flips. 689 stays.
- **Useless late CARE → COLLECT_FERTILIZER** (shyjin's trick): ~6.6 swaps/game, but late fertilizer sells for $5–15, so it nets ≈ $0–50. Dropped.
- Not tested: carrot swap through day 24 (the wheat reserve binds at 12–20 held, so only a much lower reserve would copy URAD, with feed risk), and a "chase" rule against day-28 drip sellers.

## Earlier notes still valid
- Strawberry price is set by the town: 0–1 strawberry shops by day 9 → our 245 strawberries average $15–60. The tomato switch and strawberry caps were already rejected (21 Sep), so this stays a production-plan gap.
