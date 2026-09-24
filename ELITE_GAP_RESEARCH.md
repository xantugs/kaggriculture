# Closing the elite-farm gap: evidence and a development path

21 September 2026. This report extends the review of supplied v8 (`main (2).py`, SHA-256 `11699637…`) with the newly available reconciliation records and direct replay instrumentation. No submission or production-agent change was made.

## What was checked

- Recomputed the 30 games identified as top-ten games in the supplied dataset: 27 wins, mean margin $10,765.87, median $13,079. Every game's supplied economic ledger reconciles to its cash margin.
- Retained the prior analysis's separate 25-game subset excluding opponents spending over $30,000 on wheat purchases: 23 wins, mean margin $11,349.92. This is an analytical subset, not a new unbiased benchmark.
- Replayed six recorded games, one each from DSM, Majkel1337, THIRD FARM CLUB, Otter Vibe, Vadim Vasilenko and ymg_aq, using both original action streams and seeds. All six final scores reproduced exactly. Instrumentation measured successful planting, fertilizer use and actual harvest receipts.
- Verified a small tomato production schedule directly against the installed Kaggle Environments 1.32.7 engine.

The opponent names are the dataset's historical top-ten classification, not a fresh leaderboard check. None of this demonstrates that a new agent can yet reproduce their performance against reacting opponents.

## The important new findings

### 1. The tomato experiment tested a much weaker production process

The six reconstructed elite games yielded:

| Recorded team | Tomato plants | Harvested units | Units per plant |
|---|---:|---:|---:|
| DSM | 18 | 143 | 7.94 |
| Majkel1337 | 16 | 115 | 7.19 |
| THIRD FARM CLUB | 25 | 179 | 7.16 |
| Otter Vibe | 26 | 208 | 8.00 |
| Vadim Vasilenko | 5 | 40 | 8.00 |
| ymg_aq | 14 | 108 | 7.71 |
| Total | 104 | 793 | 7.63 |

The failed bolt-on reportedly yielded about three per plot. It therefore did not reproduce the elite crop economics. That is a reason to test a complete crop job, not evidence that a complete job is profitable on v8's farm.

Of these 104 tomato plants, 89 received two fertilizer applications. Previous crops were wheat (49), strawberry (21), carrot (8), melon (9), and previously unused plots (17). These are observed rotations, not instructions to replace the same number of v8 tiles. Removing wheat still requires an explicit replacement feed plan.

### 2. Eight tomatoes do not mechanically require daily harvesting

I verified this isolated schedule with a stationary worker and prepositioned inputs. Ages are relative to planting:

| Plant age | Work |
|---|---|
| 0 | Plant, water |
| 2, 4, 6 | Water |
| 7 | Fertilize, water |
| 8 | Water |
| 9 | Harvest four, water |
| 10 | Fertilize, water |
| 11 | Harvest four |

It produces eight tomatoes with one seed, two fertilizer, eight watering actions and two harvest actions: **13 tile actions**, excluding clearance, input pickup, travel, delivery and trading. Each listed action is a separate turn. The worker does not perform multiple actions in one turn.

The production events are at ages 8–11, and the plant holds at most four units. Harvesting at ages 9 and 11 avoids clipping in this schedule. Alternate-day watering before production preserves survival; watering during the relevant production refreshes enables the fertilizer bonus.

This is a feasibility result, not a full-farm profit result. Daily harvesting can still be preferable if it earns earlier prices, supplies cash, or fits worker tours better. The planner should compare both schedules.

For scale only: increasing ten plants from three units to eight adds 50 units, or $4,250 gross at a hypothetical unchanged $85 realized price. Fertilizer opportunity cost, workers, travel, displaced crops and the extra supply's price impact must be subtracted. Do not treat $4,250 as an expected score gain.

### 3. The elite calendar differs before tomatoes appear

In the 25-game subset, mean farm composition was:

| Snapshot | Elite farms | Their opponents |
|---|---:|---:|
| Strawberry tiles, day 3 | 4.04 | 0 |
| Strawberry tiles, day 6 | 16.52 | 12.24 |
| Strawberry tiles, day 12 | 26.52 | 32.44 |
| Tomato tiles, day 18 | 11.44 | 3.32 |
| Carrot tiles, day 21 | 8.00 | 1.16 |

Across those games, 260 of 321 tomato planting requests occurred on days 11–18. These are requested actions; successful plant counts were checked separately in the six traces.

The evidence supports testing an earlier, smaller strawberry crop, staggered midseason tomatoes, and earlier late-season carrots. It does not support planting every tomato on day 10 or waiting only for an extreme current-price spike.

This also corrects an over-simple melon interpretation: elite farms sold **77.64 melons on average versus 72.96**, but earned less melon revenue. Lower revenue does not imply lower total production. They had fewer melon plants on day 0 but approximately the same number by day 6. Opening timing and the opportunity cost of capital need analysis alongside totals.

### 4. Similar hiring cost hides different work allocation

The same subset averaged:

| Measure | Elite farms | Opponents |
|---|---:|---:|
| Total hiring cost | $6,019 | $5,970 |
| CARE commands | 320 | 409 |
| WATER commands | 1,217 | 1,120 |
| FERTILIZE commands | 180 | 112 |
| HARVEST commands | 488 | 491 |

Command counts are not all successful actions, and these differences do not isolate causality. They nevertheless suggest allocating existing worker time differently rather than adding a complete new workload to an already occupied farm.

Skipping CARE must be priced against the future product it adds; it is separate from FEED and survival. Capacity clipping in the six traces was not uniformly worse in the opponents, so it would be unjustified to call all extra care waste.

### 5. The money comes from a joint portfolio

In the 25-game subset, mean revenue advantages were approximately $3.70k carrot, $3.10k tomato, $2.96k wool, $2.35k strawberry and $1.81k egg, alongside disadvantages in other goods. These are accounting differences, not independent improvement budgets.

Elite strawberry sales were 193 units at a pooled $128.19 versus 242 at $92.79; wool was 143 at $153.68 versus 166 at $114.30. Producing fewer units can earn more when price and timing improve.

Tomato sales were 93 units at a pooled $95.43 versus 28 at $206.27. The elites' advantage was therefore not simply waiting for the highest tomato prices. Fertilizer also needs net accounting: they earned $3.92k less from selling it and spent $2.07k less buying it, a combined $1.85k disadvantage before the value of its use on crops. Land spending was $1.44k lower on average.

## The development path with a plausible scale of upside

Build a season planner around **complete, executable production jobs**, using v8 as the frozen control. The earlier adaptive V13 in this workspace is not a proven replacement; reuse its useful valuation code only after checking its forecasts and execution.

### First: one resource ledger shared by all decisions

Reserve wheat by scheduled feed obligations and actual delivery deadlines. Reserve fertilizer for accepted crop jobs and money for committed hires and purchases. A sale can use only surplus after those reservations. Reservations must be visible to every market layer; buying wheat while another layer sells it must be impossible by construction.

Track actual successful purchases, transfers and harvests. A requested action is not inventory. Budget both shed capacity and worker-carried supplies. Begin with conservative feed protection; changing survival policy is a separate experiment.

### Second: a small library of crop and livestock jobs

Each job specifies crop choice, plot occupancy, input requirements, feasible watering/fertilizer/harvest windows, transport, and conservative revenue at sale. Include both the verified two-harvest tomato job and more frequent-harvest variants. Include wheat-for-feed, carrot rotations, strawberry cycles, and animal feed/care/harvest jobs.

The dispatcher must demonstrate that the jobs fit the available workers and their starting positions. Reject economically attractive jobs that cannot be executed. Value the extra worker at the actual marginal Fibonacci hiring cost, not the average cost of existing workers.

### Third: search whole production packages

The first family worth testing is:

- An earlier, smaller strawberry tranche, with its opening cash and labor funded explicitly.
- Staggered tomato jobs planted during a demand-dependent midseason window, targeting high yield on already owned land.
- Carrot rotations started early enough to supply later demand.
- A herd whose feed and care costs fit that crop plan, rather than inheriting every scheduled animal purchase.

Choose plot count, planting dates, care intensity and harvest frequency together. Do not infer that the average elite farm is an optimal fixed template. Different shop sequences and rivals require different packages.

Replan new investments at dawn, shop openings and significant harvest/farm changes. Preserve accepted obligations between replans. Include the existing continuation as a candidate, but do not let its later raw actions undo accepted replacement jobs.

### Fourth: value future market inventory, not today's sticker price

Forecast each good from current inventory, town consumption, own pipeline, and plausible rival deliveries. Sample unrevealed shops; their exact future sequence is not available to the agent. Price candidate batches unit by unit, including their own market impact. Use the same forecast for production and selling.

Evaluate a quiet-rival and a high-supply case as well as the central forecast. Log forecast errors after actual harvests and sales. A complex model that systematically overvalues carrots or underestimates feed costs can be worse than a fixed route.

## How to build it without another blind rewrite

1. **Trace the teachers:** use the exact replays to extract successful crop jobs, worker visits, input movements and sale outcomes. The six instrumented traces already provide the first examples. Learn crop decisions and timing; copying raw movement streams will reproduce the original fragility.
2. **Prove one complete tomato block:** its inputs are protected, its eight-unit potential is actually harvested and delivered, and no baseline animal escapes because of the intervention. Measure its full incremental cost. The isolated schedule is a starting point, not this milestone's completion.
3. **Establish execution parity:** test the new dispatcher on baseline production obligations before asking it to improve the crop mix. Large scheduling losses must not be mistaken for bad economics.
4. **Search the production package offline:** make a limited set of joint changes, run full simulations and inspect failures. Keep tune seeds and opponent families separate from validation.
5. **Validate against reacting agents:** use several available strong public families, the current v8 and diverse production styles. Replay opponents are useful for diagnosis but are not reliable counterfactuals when our changes alter their prices, cash or shop sequence. Freeze a finalist before untouched testing.

A worthwhile research milestone is a recurring several-thousand-dollar improvement in whole-game margin, spread across opponent styles. A full $10k improvement or top-ten result remains to be demonstrated. The evidence now points to mechanisms large enough to investigate; it does not license adding their apparent gains together.

## Saved evidence

- `review_20260921/elite_structure.json`: recomputed 30-game and 25-game economics, calendar and command summaries.
- `review_20260921/elite_rotation_<episode>.json`: six exact replay traces with crop jobs, fertilizer, harvests, shops and daily sales.
- `review_20260921/tomato_job_verified.json`: the eight-unit/two-harvest engine check.
- Reproduction scripts: `analyze_elite_structure.py`, `trace_elite_rotations.py`, and `verify_tomato_job.py` in that folder.

The web search did not establish a stronger validated public replacement. Notebook titles advertising ratings are not evidence of achieved performance. Mechanics were checked against the local official engine; the [official environment guide](https://github.com/Kaggle/kaggle-environments/blob/master/kaggle_environments/envs/kaggriculture/AGENTS.md) provides the public reference.
