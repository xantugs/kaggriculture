# Kaggriculture: the elite gap, a tomato annex, and v8's latest losses (21–22 Sep)

**Status (22 Sep ~00:30 UTC).** Active pair: **v8** (2737, 55-11 over 66 games) and **v9** (= v8 + day-28 pre-emption, 1532 and climbing, 10-1; the loss is the validation self-play). Leaderboard lines: gold 2917 (rank 29), silver 2619 (rank 487), bronze 2429 (rank 975); rank 100 = 2799, rank 200 = 2738. No public notebook scores above ~2715.

## v8's losses since the last doc
| opponent | margin | what decided it | v9 in replay |
|---|---:|---|---:|
| codezzzsleep (mv13 + own day 29) | −176 | mirror to day 28 (+102). On day 29 they sold tomatoes at steps 704–709 (avg $321) vs our 716–717 ($301), sold wool/milk earlier, collected 15 more animal fertilizer | **+89** |
| Pico (other lineage) | −56 | swingy game, decided at the last step | −202 |
| Illia Dolenko | −553 | lost wool/milk/strawberry races on days 20–28 | −658 |
| Munal Singh (mv13 to step 150) | −76 | strawberry race, days 20–28 | −121 |
| Jayden Y | −670 | low-scoring game; wool/egg timing | −653 |
| Rio (sms/awl lineage) | −30 | strawberry race | **+427** |
| **Mengfei Li (2808)** | **−23,858** | see below | same |

Replays against opponents that react to us are approximate.

## Mengfei Li: what a tomato town is worth
Same lineage as ours: both farms were **tile-for-tile identical at step 144**. The town had PIZZA ×3 and FARMERS_MARKET ×2 by day 18. From day 7 Mengfei planted fewer strawberries (12 vs our 33 tiles) and more wheat. On days 11–17 it converted ~40 wheat tiles to tomatoes: 80 fertilizer applications, 320 waterings, **314 tomatoes (7.85/plant), $41.4k at $132 avg**. Its hires were ≤12/day, like ours; the labor came from dropped strawberry/wheat work, not extra hands. Our V219 fired on day 18 (SE, 10 plots): 80 tomatoes, $8.6k.

## Checking Codex's elite-gap report
- **Tomato mechanics are right** (engine 1.32.7). There are 4 productions at the end of ages 7–10, each +2 when fertilized and watered that day, capped at 4 held. So 8/plant needs 2 fertilizer rounds (ages 6+8, 6+9 or 7+10), waterings at ages 0,2,4,6,7,8,9,10, and harvests at ages 9 and 11. That's 13 tile actions. The plant decays from the start of age 12.
- **Elites use the same land and the same labor bill as the chassis.** From 51 top-40 replays: SE was bought in 1 of 51 games; SW on day 8–9 vs the chassis's 11; hire cost $5,616 vs $5,651 per game; ~11 hands/day for both. Crop calendar: strawberries from day 2–5, ~10 tomato tiles on days 10–20, carrots all season, and fewer idle tiles late (day 28: 20.5 vs 35.1 empty).
- **The elite margin is not mainly tomatoes.** Margin by tomato shops among the first 4:

  | tomato shops | games | mean margin | median | tomato revenue diff |
  |---|---:|---:|---:|---:|
  | 0 | 14 | +$10.9k | +$8.4k | +$2.9k |
  | 1 | 20 | +$10.6k | +$9.5k | +$5.3k |
  | 2 | 14 | +$13.8k | +$14.2k | +$8.7k |
  | 3 | 3 | −$11.2k | −$3.7k | −$26.6k |

  Roughly $8k of the gap exists even in towns with no tomato demand; it is general economy. In 3-shop towns V219-type chassis opponents out-earned the elites on tomatoes.
- All 41 route tapes buy NE on day 6 and SW on day 11; none buys SE or plants tomatoes.

## Experiments (all offline, rejected)
- **Elite / Mengfei tape transplant into the chassis.** DSM's recorded moves first crashed in the opening layers, which assert route-0 content. With `_ALT_MODE='Original'` they ran, but lost −$23.5k vs omw on seed 9000. Mengfei's moves from step 144 lost −$24.8k vs omw on 9013 and **−$42.5k on Mengfei's own seed**. Recorded moves do not transfer.
- **SE tomato annex** (`layers/annex.py`, `build_ax.py`): buys SE on day 11–13 when ≥2 tomato shops, with its own daily crew hired after all native/r51 hires. The yield is fixed at ~6.5–7/plant when buying the full fertilizer need and splitting plots into per-worker segments. **But the chassis already hires 9–12 hands/day, so each extra worker costs fib(10..14) = $89–610/day.** On seed 9016 (3 tomato shops): 20 plants, 128–139 tomatoes, $8.7k–15.4k of extra hires. Net ≈ $0 before land, and it pre-empts V219. Buying SE also changes future shop draws (weed RNG consumes one draw per empty tile), so single-seed comparisons are dominated by town changes.
- **Day-29 animal fertilizer in fd4.** As plain targets: −$29…−$75 vs omw and −$89…−$357 vs v9, because it delays premium deliveries. After-delivery only (`final_day8.py`): +$0…+$15. Not worth a submission.

## Conclusion
Closing the ~$10k elite gap needs a different season plan on the same land and labor, i.e., a new agent, not a layer. Layers that add production pay Fibonacci labor, and layers that replace route production break its feed/care coupling. Keep v8 + v9. Gold is not realistic by Sep 30.
