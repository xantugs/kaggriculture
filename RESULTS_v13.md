# V13 — one real gain (carrot), and everything else ruled out

20 September 2026, third round. Gate: head-to-head win rate against the incumbent on
paired seeds.

`main_v13.py` SHA-256: `e5c1a9eca79361e2c1d4efd2a689ce2a205559242b55ea31173c7897bada0c32`
V13 = V11 with one change: **`carrot_w` 0.5** — carrot's projected revenue is halved in
the filler-crop comparison.

## Result

**97W–43L over 140 fresh paired games vs V11 = 69.3%** (95% CI 61.2–76.3%), mean margin
+$4,113. Pooled with an earlier 60-game batch on separate seeds: **131–69 over 200 games,
65.5%.**

Full reference-ladder gate, three paired seeds, both seats:

| opponent | V13 W/L | margin | V11 W/L |
|---|---:|---:|---:|
| Fallow Finn (tier 0) | 6/6 | +$131,148 | 6/6 |
| Wheat Walter (tier 1) | 6/6 | +$143,065 | 6/6 |
| Rotation Rosa (tier 2) | 6/6 | +$155,373 | 6/6 |
| Homestead Hana (tier 3) | 6/6 | +$151,864 | 6/6 |
| Melon Mateo (tier 4) | 6/6 | +$128,644 | 6/6 |
| Rancher Rita (tier 5) | 6/6 | +$109,714 | 6/6 |
| public hand-written planner | 6/6 | +$84,325 | 6/6 |
| early public tape | 0/6 | −$18,781 | 2/6 |
| current public tape | 0/6 | −$32,130 | 0/6 |
| `main_v9_capguard.py` | 6/6 | +$16,504 | 3/6 |
| old `main.py` (V8) | 6/6 | +$20,549 | 3/6 |

**54/66 = 81.8%** overall, against V11's 75.8%. Zero errors across every run.

## The mechanism

Fillers are chosen between WHEAT and CARROT only. V11 was running 14 carrot tiles
mid-season. Halving carrot's valuation flips them: day-18 composition goes from
`STRAWBERRY 29, CARROT 14, TOMATO 7, MELON 8` to `STRAWBERRY 25, TOMATO 18, MELON 7,
WHEAT 6`, and the freed budget also buys more animals — the day-18 herd goes from roughly
5 cows / 11 sheep to **10 cows / 10 sheep**.

Carrot is $35 base with two shops demanding it, and it needs a PLANT and a HARVEST every
three days. Tomato and wheat return more per unit-turn on the same tile. The meta line
grows no carrot at all.

`carrot_w` 0.5, 0.2 and 0.01 all produce the same farm — the filler choice flips fully at
0.5 — so the exact value does not matter. 0.8 measured indistinguishably in two screens.

## Rejected this round

All measured against V11 or V13 on 8 paired seeds unless noted; ±$10k is the noise band
at that sample size.

| change | result |
|---|---|
| working sheep cap (`count_animal` fix, V15) | shrinks the herd instead of rebalancing it — 20 animals → 12, $99,959 → $83,831 on the probe seed. Rejected. |
| `animal_w` SHEEP 0.4/0.6/0.8, COW 1.2/1.3 | all within noise of base |
| `crop_w` TOMATO 1.5, STRAWBERRY 1.5, MELON 0.7 | all within noise |
| `melon0` 16 | −$34,602, 0/8. Melon does not scale. |
| `feed_days` 1 and 2 (retested on the new base) | −$8,952 / −$14,400. Same wheat-denial effect as round 2. |
| `hire_margin` 1.2, 2.0 | within noise of 1.5 |
| `max_land` 3 | within noise of 2 |
| `use_valuation_day0`, `care_rule`, `split_feed_care` | byte-identical or within noise |
| `helpers`, `early_deliver` | −$2,219 / −$2,543 |

## Two things ruled out as bottlenecks

**Market slots.** Neither V13 nor the tape gets near the 10-orders-per-turn cap — V13
averages 1.12 orders/turn and hits the cap 21 times in 720 turns; the tape averages 0.96
and hits it 9 times. The market layer is not where the games are being lost, despite being
the documented differentiator among the top four ladder rungs.

**Endgame liquidation.** Only 6.4% of gross income lands in the final 8 turns (94 units)
and 11.8% in the final 48. Prices realised there are around $87/unit. Spreading the
endgame dump would not recover much.

## Where this leaves things

V13 beats every hand-authored reference agent, both public closed-loop planners, and both
previous versions of this agent. It still loses every game to the route-replay tapes,
though the margin against the strongest one narrowed from −$44,085 (V11) to −$32,130.

Three rounds of screening have produced exactly two validated changes — the V11 package
and `carrot_w`. Parameter search is done; anything further has to be structural.

## Seeds

V13 selection: 85000–85007, 95000–95007. Validation: 95000–95029 (60 games) and
96000–96069 (140 games), both seats, disjoint. Ladder gate: 96500–96502.
