# Kaggriculture — silver push: public chassis, final-day controller, opening squeeze (v7, v8) (2026-09-21)

**Status (21 Sep, 10:45 UTC):** two live slots.
- **v6** = One More Wheat (public, dmitriigluzdov, Apache-2.0), exact archive, main.py sha256 `10f58185…`, submission 56419222.
  **2600.5, rank 543 (bronze)** after ~70 games.
- **v7** = One More Wheat + our final-day controller (`final_day4`), plain `main.py`, sha256 `92317f54…`, 1,032,756 bytes,
  submission 56425941, submitted 10:27 UTC. Validated; 2-0 in its first games.

**Update (21 Sep, ~12:40 UTC):** **v8 submitted** = v7 + opening squeeze, plain `main.py`, sha256 `11699637…`,
1,034,338 bytes. Active pair is now **v7 + v8** (v6 dropped out of the latest-two window at 2612). At submission time:
v7 26-2 / 2346 and climbing; silver line 2617.5 (rank 486).

## The opening squeeze (v8) — the biggest edge found
Found by identifying the agent that beat v7 by $19.8k live ("yy" = exact copy of public **rr7**, "Kaggriculture V7:
Reactive Market-Master", Apache-2.0, aurax7 et al.). rr7 beats One More Wheat on **12/12 seeds by $5–28k** yet its
public score is only ~2510: it is a counter to the route-0 chassis family, not a stronger farm.
- **Mechanism:** both farms trade wheat on turn 0 and orders settle unit by unit in lockstep. rr7's round trip is
  BUY 10 / SELL 10 (net wheat bought on turn 1) vs omw's BUY 20 / SELL 15. That leaves an omw rival **$11** poorer.
  The chassis opening spends cash down to $8–12 (step 21: $12 in the mirror), so at step 24 the rival has **$1** and
  gets 1 of its 3 day-1 hands; the scripted farm build never recovers (2 cows + empty pasture at day 5 instead of
  4 cows; 7 empty tiles and 2 empty pastures through day 25).
- **Our version (layers/squeeze.py):** step 0 market = [BUY_PRODUCT WHEAT 10, SELL WHEAT 10, BUY_SEED WHEAT 1]
  (keeps One More Wheat's extra wheat crop); step 1 prepends [BUY_PRODUCT WHEAT 5]. Nothing else changes.
  Our own cushion at step 24: $22 vs omw, $14 vs rr7 (hires need $4).
- **Panel** (paired vs v7, 14 seeds × 2 seats where run): omw/mwss/p16/yum/prv **+$14–20k per game**; **rr7 0-16 → 16-0**;
  dm29, mv13, fs2, tape_a2, awl, erg, sms, ge4, mr, v47, v53 unchanged (−$1…+$23). Totals: 128-8 vs 120-16
  (17 agents, 4 seeds) and 112-8 vs 94-24 (7 agents, 10 fresh seeds).
- **Replaying v6's 56 real games:** v8 **53-3** (v7 47-9, v6 real 38-16-2). Remaining: mv13 copy −$71, Batuhan −$1.2k,
  JeremiahMannings −$2.3k. Tape opponents can't react, so their collapse is approximate; closed-loop public copies
  collapse the same way.
- **Risk:** anyone else using a stronger squeeze could break our own opening (cushion $14–22). Candidate defense:
  keep a larger cash reserve before the step-24 hires.

## Leaderboard (21 Sep 10:30 UTC, 9,730 teams)
| | last rank | score |
|---|---:|---:|
| Gold | 29 | 2909.1 |
| **Silver** | **486** | **2618.6** |
| Bronze | 973 | 2420.1 |
| #1 | 1 | 3182.6 |
Rank 100 = 2806, 200 = 2744, 300 = 2690, 400 = 2656, 600 = 2582. v6 is 18 points under the silver line.

## What the field runs (unchanged)
- The 2500–2800 band is dominated by one public lineage (Tschinkel Metav4 v13 → Pipe16 → One More Wheat / More Wheat
  Smarter Sales / prvsiyan frontier), all route 0 + the same 41-tape shop-pair router. Clone-vs-clone games are
  deterministic and seat-symmetric, so any consistent +$1 wins every such game.
- Top (3000+) is a different class (adaptive schedulers beating the band by $12–20k).

## The edge: final-day controller (`layers/final_day4.py`)
Takes over units and market on day 29 (steps 696–718), everything before is the untouched parent.
- **Harvest**: greedy value-per-step tours over everything still harvestable, hire count chosen to maximise value −
  fib hire costs; closed-loop execution (each unit re-reads the board every step), premium goods reach the shed ≥4 steps early.
- **Selling**: staples sold on delivery. Milk/wool/strawberry/melon/tomato are held and sold one step before the rival
  can dump the same good. Rival carries are tracked from public tile-yield drops and positions; the parent's own sell
  order this turn is used as the forecast of a mirror rival's queue, and contested goods go into the earliest slots.
  Everything still held is flushed from step 716.
- Panel (paired, 14 seeds × 2 seats): **+$306/game vs omw (28-0, base 0-0-28 ties), +$304 vs prv (28-0 vs 0-28),
  +$304 vs p16, +$302 vs mv13**, positive on average vs every other public agent tested. Never negative vs the four clones.
- Earlier versions (immediate liquidation; fd2) lost the slot race on milk/wheat — fixed by using the parent's order as
  the rival forecast.

## Counterfactual on v6's real games (the check that matters)
56 of v6's live episodes vs 2000+ opponents downloaded as action digests (browser → single file → project folder).
Local replay reproduces **all 56** real results exactly. Opponents identified by step-by-step action matching
against 30 public agents: exact matches for the p16 family (7), omw/mwss (2), dm29 (4), mv13 (2), v53 (2), ge4, fs2, mr,
v49, sms; the rest are modified clones (e.g. DeeSaa = omw until step 679, Sankalp = omw until 600, eugenn = mv13 until 603).

Replaying the same seeds with **v7 in our seat** (identified agents closed-loop, the others as recorded tapes):
| | W | L | T |
|---|---:|---:|---:|
| v6, real | 38 | 16 | 2 |
| **v7, counterfactual** | **47** | **9** | 0 |
10 losses/ties flip to wins (NineThree, Fried Chicken Love, eugenn, DeeSaa, Tien N., sdy623, Ziad EL ARARI,
Auto Fermers, s_a_ai_engineer, 福原 大知); 1 win flips to a loss (Marwan Ashref, p16 family, +28 → −75).
Still lost: linmumu009 −653, Civitasmass −714, Sankalp −530, linyifangzhenshuai (mv13) −94, Batuhan Ustun −1238,
JeremiahMannings −2314, Taeyang −242, 福原 大知 −77, Marwan Ashref −75.

## Tested and rejected: sell-ahead before day 29
Sankalp's agent is omw with only the **market timing** changed on days 25–28 (strawberries and milk sold earlier),
worth +$723 against omw. Engine check: market stock starts at 10,000, every unit sold (>$1) adds one, town shops drain
it slowly (every 4 steps), and each order slot settles unit by unit in lockstep for both players, so a unit sold before
the rival's lowers the rival's price. But a blanket rule (sell never-input produce from the shed immediately, from
day 20) **loses**: 14-agent panel, 6 seeds × 2 seats, candidate 64-28 vs base (v7) 83-8, with single-game drops to
−$2,330. The chassis's holding is worth real money (prices recover as the town drains stock). The chassis already
has calibrated race logic: `_sell_lead` (tape sells pulled one step early), V9_RACE (infers rival sales from market
inventory and adapts the lead horizon), RACEPX (lead only when price ≥ base), r36 reserves.

## Where the top agents' money comes from (51 games, top-40 agents vs 2500–2780 opponents)
All 51 reproduce exactly. Mean reward $103.9k vs $93.6k (+$10.3k). Revenue is **identical** ($136.9k vs $136.7k);
the aggregate gap is costs (wheat bought −$8.9k, land −$1k), but that is skewed by a few wheat-arbitrage opponents.
Per game, the consistent pattern is diversification:
- **Tomatoes** in almost every top game ($2–29k) where the chassis-type opponent sells none.
- **Carrots**: typically $5–25k vs $2–9k.
- **Better strawberry prices** (e.g. 123 vs 94, 112 vs 73, 75 vs 49): fewer units into a glutted book.
Engine: tomato/carrot/egg use a *hinge* scarcity curve (HINGE_GAIN 8), so a good the town drains and nobody supplies
explodes in price (tomatoes at ~$400 on days 27–29 in one v6 game, strawberries ~$70). Tomato also yields on days
8–11 after planting (strawberry 10–16) at half the seed cost. The chassis grows a fixed tape (41 routes by the first
two shops) and cannot respond to shops unlocked later. This is the lever for anything beyond silver; it needs an
adaptive production layer, not a timing tweak.

## Final-day controller variants (paired panel, 9 agents × 14 seeds × 2 seats)
| variant | record | vs fd4 (v7) |
|---|---|---|
| fd4 (v7) | 238-14 | — |
| fd5b: don't hold tomatoes | 238-14 | −$20/game vs the four clones |
| fd5a: premium goods delivered 6 steps early (was 4) | 232-20 | loses 2 games each vs omw/p16/prv |
v7 stays as submitted.

## v7 against recorded top-40 agents
Open-loop test (top agent replayed from its recording, our agent in the other seat) is only partly valid: swapping the
opponent changes the empty-tile count, hence the shop draws, so the recording desyncs and collapses in 18/51 games
(fake +$46–113k "wins"). Where it stays in sync, v7 loses by a median ~$6.8k (omw ~$7.0k; v7 − omw = +$158/game).
Gold needs a different production economy, not more timing edges.

## v9 research, round 1 (21 Sep afternoon)
- **Opening-squeeze search** (`sq_search.py`): 900 variants of our turn-0/1 wheat orders (buy 0–40, sell ≤ buy, turn-1
  buy 0–30, turn-1 sell 0–13) × 12 public families, simulated to the day-1 hires. Only the omw/p16/prv lineage can be
  broken, and only by v8's exact trade (buy 10 / sell 10). sms/awl only buy 5 wheat on turn 0; mv13/dm29/erg/rr7 keep
  $22 and the v53 family $27 at step 24 (hires cost $4), and nothing in this space takes enough from them.
- **Our robustness** (`sq_attack.py`): 728 attacker variants (omw + any turn-0/1 wheat trade) against v8: none break
  its day-1 or day-2 hires; lowest cash at step 24 is $8. A hire guard (sell stock if a scripted hire is unaffordable)
  was built (`layers/hire_guard.py`) but never triggers, so it stays out.
- **Opening cash profiles** (mirror, seed 9000): every family runs down to single digits between steps 24 and 32
  (omw/p16/prv/sms/awl $8 after the hires; mv13/dm29/erg/rr7 $2 at step 32; v53/v47/ge4 $7 at step 32). Everyone is
  broke then, including us, so later squeezes can't be funded.
- **v53 family** (Ahmed's EXP260 line: v47/v53/ge4/mr) is the main public agent v8 doesn't dominate: seed-dependent,
  v8 wins ~2/3 (margins −$2.6k…+$3.6k).
- **Band map (2780–2950)** pending: Kaggle's episode API returned 429 after 151 quick lookups; retry slowly.

## Gold levers, round 2 (21 Sep afternoon)
- **Land-fill (grow extra crops on idle land with idle workers): no slack to use.** v8 mid/late game (days 10–27,
  three seeds): ~2 empty tiles per day at noon, ~4% idle unit-steps (scattered). Hands and inventories reset every
  day (engine end-of-day: hands removed, inventories dropped, farmer respawned), so borrowing an idle worker is safe —
  but there is almost no idle land or labor to borrow.
- **Top agents' openings are also knife-edge**: in the 51 recorded top-40 games most run cash to $0–5 around
  steps 20–32, and several (DSM, Vadim, Unknown Mother-Goose, ymg_aq, QQ, Orbital) get only 0–1 hands on day 1.
  They are adaptive, so a squeeze makes them re-plan rather than collapse; can't be measured offline without their
  code. Watch v8's live games against them.
- **Late carrots → wheat when wheat ≥ carrot price (from day 22): worse** — 38-12 vs v8's 44-2 over 52 paired games,
  −$275…−$464/game vs non-copy families. Rejected.

## Tomato switch (the top-10's biggest line item) — tested, rejected (21 Sep)
Top-10 vs chassis-type opponents (30 games): median margin +$13.1k, top agent wins 27/30; tomatoes +$5.1k (they sell
~81/game in 27/30 games, the opponent none), strawberry price $125 vs $93 (+$3.1k), carrots/eggs/wool +$1.8k/+$1.8k/
+$1.4k, less melon/fertilizer/milk (−$3.5k/−$4.0k/−$1.3k), costs about equal.
Bolt-on test (`layers/tomato_switch.py`): convert the route's strawberry seed buys and plantings to tomatoes, spoof the
route's seed view so its plan continues, sell the tomatoes ourselves.
- Tomato/strawberry price ratio during the planting window (days 6–18) is 0.3–0.5 in all six seeds checked;
  strawberries collapse only around days 21–24 when both chassis farms harvest together (not in every seed).
- The route plants strawberries on days 5–8 (20 tiles) and day 11 (13 tiles).
- Switch everything: −$45k…−$63k per game vs v8. Switch only the day-11 batch: 4-44 vs v8's 38-2, ≈ −$13k/game.
- Why: fertilized strawberries in the route yield ~8 units per tile over 16 days (seed 9000: $225 each); a tomato tile
  holds at most 4 units and wastes fertilizer yield unless harvested daily, which the route's crews don't do; the switch
  also disturbed care routines (2 cows lost). The top agents' tomato income comes with a daily-harvest labor plan —
  a different agent, not a layer.

## Plot-block second crop (external review's proposal) — tested, rejected (21 Sep evening)
External review (GPT) of v8: correct that v8 has more adaptation than "a script" (carrot substitution, herd choices,
rival-sale prediction, order reordering, and V219: a day-18 tomato investment needing ≥3 pizza/farmers-market shops,
tomato ≥ $70, cash ≥ $12k and the SE quadrant still locked — it buys the quadrant and 10 tomato plots with dedicated
workers). Correct that medians aren't additive: reconciled per game (all 30 top-10 games sum exactly); excluding 5
wheat-arbitrage opponents, mean margin +$11,350: carrots +3.7k, tomatoes +3.1k, wool +3.0k, strawberries +2.4k,
eggs +1.8k, wheat +1.3k, melon −2.4k, fertilizer sales −3.9k (buys −2.1k), land +1.4k. Data + script saved to
`review_20260921/top10_reconciliation/`.
Experiments (layer `plot_block.py`, off-mode reproduces v8 exactly):
- Opening melon plots (12, NW corner) are harvested on day 10; 11 go into 3–4-day wheat cycles watered almost daily,
  1 becomes a sheep pasture. That wheat is the herd's feed.
- Ride-along tomatoes on those plots (route's visits water them; ripe visits harvest): tomatoes survive but give ~3
  units/plot (~$60–88); 6–11 plots cost −$8.5k…−$26k/game vs v8, including tomato-rich seeds (≥2 tomato shops by
  day 9: 23 of 151 seeds). Cause: feed shortfall from day 17 (shed wheat 0–5 vs 7–20), animals unfed → 2 sheep and
  2–4 cows escape, then milk/wool/strawberry losses.
- Buying replacement wheat to keep ≥10 in the shed: no better — the route sells the extra wheat (sales 290 → 523 units).
- In 2-tomato-shop games tomato prices are only ~$80–88 on days 18–22; they explode later (days 24–28) as stock drains.
- V219 threshold 3 → 2 tomato shops: fires in 16 of 52 games; per-game change −$1.5k…+$2.7k, mean −$9.5, wins lost 4,
  gained 2. Not an improvement.
Conclusion: the route's production, feed and trading are tightly coupled; production changes cascade. v8 stays.

## Other checks
- v7's worst step time in the panel: 0.21 s (limit 1 s).
- Late-game spending audit (omw mirror, days 22–29): hires ~$232/day, small seed buys that still mature; the day-28
  coop build is free. Nothing to cut.
- Public kernels (21 Sep 11:00 UTC): One More Wheat still the top public agent (2722); new since morning: farmer-john
  wheat-seller (2657), Ahmed v54 (2598). Band composition unchanged.

## Negative results
- Capping omw's strawberry plantings loses $5–18k/game in the mirror.
- First final-day controller (immediate liquidation) lost $170–514 on 3 of 4 seeds.
- Counter-routing (forcing the day-6 route per shop pair): single-seed screen was noisy; most pairs failed validation.

## Practicalities
- kaggle.com is blocked from the cloud sandbox and the file VM; data comes through the logged-in browser pane.
  Downloads: build one bundle in-page, trigger it from a real click, and copy it the moment it lands in Downloads
  (the pane cancels a pending download after ~50 s); gzip into `kaggriculture/replays/` and stage.
- Submission: rebuild the file in-page from the public notebook + our layer, verify sha256, attach to the dialog.
  Descriptions kept short ("v7").
