# Current v8: the route toward stronger opponents

Reviewed the newly supplied `C:/Users/khant/Downloads/main (2).py`, SHA-256 `11699637b73ee495f3676f621b48b185902ebec8eb754985a6f32d46c80691e4`. This is a different agent lineage from this folder's original `main.py` and `versions/main_v8.py`. Findings about the old A2 tape should not be transferred to this file without checking.

## Verdict on Claude's analysis

The demand-driven crop-mix hypothesis is credible. The installed engine confirms that tomatoes and carrots have shop demand, while melon has only town-center consumption. But the supplied agent already has adaptive production and selling layers. The useful next step is to expand its ability to choose and execute new crop rotations, while retaining its working opening, worker logistics and baseline behavior.

The provided 30-game summary is observational evidence. Its raw games and calculation script were not supplied, so this review does not independently confirm 27/30, the $13.1k median gap, or current top-10 identities. Different crops and sale prices do not establish that the opponents recompute their entire strategy every turn. A library of well-chosen plans can also create those patterns.

Do not add the listed per-product medians to explain the median score gap: medians are not additive. The displayed signed figures sum to approximately $4.4k, which neither disproves the $13.1k result nor accounts for it. Reconcile each game's actual filled-sale revenue, all purchase costs, and starting/final cash first; then summarize the reconciled differences. A higher average strawberry sale price can come from quantity, harvest dates, shop composition, sale timing, or their interaction.

## What the supplied file actually does

| Component | Verified behavior | Source lines |
|---|---|---|
| Base production | 41 embedded routes; none contains a tomato planting command | 948 and loaded route data |
| Route selection | Chooses at step 144 from the first two shops, with a rival fingerprint exception; switches to a common route at step 648 | 961–979 |
| Tomatoes | Separate ten-plot investment checked on day 18; requires three tomato shops, price at least 70, cash at least 12,000, and a suitable unbought fourth quadrant | 1265–1285, 1412–1426 |
| Carrots | Changes wheat plantings based on current prices, expected visits/yields and feed reserves; manages replacement seeds and sales | 4589–4719 |
| Herd | Several conditional substitutions use shops or projected animal returns; some are deliberately limited to purchase windows | 5293–5396, 6193–6200, 6244–6257 |
| Selling | Includes early-sale reservations, replay-based rival-sale prediction, harvest/cargo tracking, order reordering, and capacity guards | 3499–3537, 4791 onward, 6121 onward |
| Final day | Replaces the ordinary action path with harvest tours and rival-aware sales from step 696 | 6915–7000 |

Thus, “a script plus a squeeze and $300 of liquidation” understates the active system. A more accurate limitation is: **most long-lived production commitments remain tied to the selected route; adaptive changes cover a narrow set of opportunities.**

One full instrumented match confirmed active adaptive behavior. With seed 210001, current v8 in seat 0 versus the older local A2 opponent, both completed normally. V8 telemetry recorded 25 carrot substitutions, 17 replay-prediction sale triggers, and 27 sale-order reorderings. The engine recorded 174 carrots sold and zero tomatoes. The chosen route remained 107 from day 6 through day 26 despite later shop openings. This is a mechanism check, not evidence of current top-10 strength; the scores were 74,219 versus 73,166.

## The highest-value production experiment

**Give a small block of existing plots a demand-driven second crop after the opening harvest.**

Start with four to eight plots and compare their existing continuation against tomato, strawberry, carrot and wheat schedules. Choose on expected incremental final cash after labor, seeds, fertilizer, transport, displaced production and feed replacement. This avoids making every tomato opportunity pay for a new quadrant and a separate late crew.

The current ten-tomato expansion purchases land and seeds for $4,500 before worker costs. That may explain its conservative gate, but it does not establish that tomatoes on already owned land need the same gate. Simply lowering the three-shop threshold keeps that expensive architecture and may lose money.

An opening melon plot cleared around days 8–12 is a candidate location, not a guaranteed profitable conversion. Tomatoes first produce at age eight and have only four scheduled production events, ages 8–11. They are not permanent daily income. A tomato planted on day 10 can produce during days 18–21; one planted on day 18 produces during days 26–29, leaving little recovery time for delays. Fertilizer and timely harvesting change realized yield; storage on the plant is capped.

Begin by changing the continuation after the first harvest. Removing opening melons also changes the cash that pays for the early farm, so treat that as a separate experiment once later crop choice works.

### Implement the whole crop job, not just PLANT

The controller needs explicit ownership of selected plots and enough worker time for planting, survival watering, production-window fertilizer, harvesting and delivery. Suppress or replace conflicting future route jobs for those plots. Preserve the original feed supply and mandatory jobs elsewhere.

The current file already contains useful pieces: the tomato worker controller, observed worker confirmation, deterministic unit simulation, visit forecasting and projected shed state. Reuse them. A full rewrite would also discard execution quality that the earlier adaptive planner in this workspace failed to match.

## The forecast that should drive the choice

For each candidate crop, project market inventory until its harvest dates:

`future inventory = current inventory + our planned sales + rival net supply - town consumption`

Convert that inventory into revenue using the actual per-unit price curve. Include the candidate's own added supply; today's high price is not the price of every unit of a future batch.

Under default settings, there are six shop-consumption ticks per day:

| Good | Demand from each relevant shop per day | Town-center demand |
|---|---|---:|
| Tomato | Pizza shop: 6; farmers' market: 6 | 1/day |
| Carrot | Pet café: 12; farmers' market: 6 | 1/day |
| Strawberry | Brunch, ice cream, smoothie, farmers' market: 6 each | 1/day |
| Melon | No shop demand | 1/day |

Repeated shops count repeatedly. Future shops are drawn with replacement. Model unrevealed shops as scenarios rather than assuming that the first two determine the rest. Reassess new investments at shop openings, harvests and substantial rival-farm changes; avoid repeatedly tearing up committed crops when a short-lived price moves.

Use the rival's visible crop types, planting ages, yields and animals to estimate supply. Private cargo is hidden, so retain uncertainty around delivery timing. A cheap forecast checked against subsequent observations is more useful than a detailed forecast that confidently gets the pipeline wrong.

The carrot controller currently compares expected yields with current prices. Replacing that price assumption with harvest-date marginal revenue is a smaller experiment than introducing an entirely new planner.

## Selling: improve coordination with production

The market policy already does considerable work. The next question is whether its predictions are accurate and whether they agree with the production valuation.

- Use the same expected inventory path to value planting and holding stock. Producing for a future shortage while another wrapper sells prematurely can defeat the intended strategy.
- Compare selling now, after an imminent town-consumption tick, or before predicted rival delivery. The engine settles sales before town consumption, so these times are economically different.
- Treat wheat and fertilizer as production inputs as well as saleable goods. Lower fertilizer revenue is not necessarily worse if fertilizer is profitably used on crops; buying replacement wheat also changes the value of substituting carrots.
- Optimize actual batches and ordered market slots under the engine's lockstep settlement. Displayed price times batch size overstates revenue when a batch moves the market.

Higher average sale price alone is not the objective. A policy can raise it by selling fewer units and still finish with less cash.

## A practical experiment sequence

1. Freeze this exact v8 and reproduce its behavior with a feature-disabled experimental controller.
2. Enable a small plot-block continuation planner, with the existing sale policy unchanged. Measure incremental final cash, missed care/feed, harvest completion, added labor and input costs.
3. Improve harvest-date price forecasts, then test joint production-and-sale decisions. Keep these changes separable so their effects can be identified.
4. Evaluate on the same seeds and both seats against several different farm styles, including tomato-producing and low-melon rivals. Keep mirror-family results separate from other opponents.
5. Hold out complete opponent families and fresh seeds during tuning. Recorded top-agent actions are useful diagnostic opponents, but replaying them does not reproduce how the original adaptive agent would react to a changed market.

A top-10 target requires evidence against the stronger population. Beating the current v8 or one old tape is an engineering gate, not proof of that outcome. No code change in this review has yet been validated as a score improvement.

## Evidence

`review_20260921/received_v8_probe_210001.json` contains actual per-good filled-sale quantities/revenue, daily farm/shop snapshots, and controller telemetry. `review_20260921/probe_received_v8.py` reproduces the mechanism probe using the supplied file and the pinned local engine. The supplied submission file was not modified.

Mechanics reference: [Kaggle's official environment source](https://github.com/Kaggle/kaggle-environments/blob/master/kaggle_environments/envs/kaggriculture/kaggriculture.py). Calculations here were checked against the locally installed 1.32.7 source rather than assuming the moving master branch is identical.
