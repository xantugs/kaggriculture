# V12 experiments — all rejected. V11 remains the champion.

20 September 2026, second tuning round. Gate: **head-to-head win rate against V11**, the
incumbent, on paired seeds. That is the gate that matches the ladder, which scores wins
and losses only. Optimising margin against a single strong opponent — which is what the
first half of this round did — turned out to be actively misleading; see "The wheat
result" below.

`main_v12_experimental.py` adds five tunables and one bug fix to V11. **None of them beat
V11.** V12 is kept for the record and for the knobs; the submission file stays
`main_v11.py`.

## Duel results, 8 paired seeds each, candidate vs V11

| candidate | W/L | mean margin |
|---|---:|---:|
| `straw0` 6 / 10 / 14 | 4/8 | +$3,398 |
| `carrot_w` 0.5 | 4/8 | +$215 |
| `max_sheep` 4 (with the counting fix) | 5/8 | −$999 |
| V12 defaults (sheep-cap fix active) | 3/8 | −$2,541 |
| `straw0` 10 + `carrot_w` 0.5 | 3/8 | −$3,227 |
| `max_sheep` 4 + `max_cow` 9 | 1/8 | −$7,795 |
| `feed_days` 2 | 2/8 | −$8,690 |
| `feed_days` 2 + `carrot_w` 0.5 (24 games) | 11/24 (46%) | −$1,405 |

Everything sits inside the noise band. Eight paired seeds resolve roughly ±$10,000, so
nothing here is a measured effect.

## A bug in the V11 sheep cap

V11's `max_sheep` counts sheep **standing on tiles**. Animals are bought into the shed and
placed later, so the count lags and the cap never binds: a day-18 census showed 11 sheep
against a cap of 5. V12 adds `count_animal(S, ctx, kind)` — placed, plus shed, plus unit
inventories, plus planned this turn — and the cap then binds exactly (11 → 5 sheep,
16 → 10 pastures).

**Fixing it measured neutral-to-negative** (3/8 vs V11). So V11's accidental over-shoot on
sheep is not costing it anything detectable, and the fix is not worth a submission slot on
its own. It is in `main_v12_experimental.py` if a future change makes the cap matter.

## The wheat result — the most useful thing learned this round

Holding wheat back to feed the herd properly (`feed_days` 2) does exactly what it should
mechanically:

| | V12 default | `feed_days` 2 |
|---|---:|---:|
| FEED actions | 173 | 216 |
| CARE actions | 142 | 168 |
| PLANT actions | 328 | 265 |
| own final cash | $70,790 | $81,827 |

and across six seeds against the tape it lifted own cash from $100,971 to $120,130 — a
19% production gain, the largest single effect found in either round.

**It still loses.** The opponent's cash rose from $113,173 to $136,874 — more than ours
did. Dumping wheat into the market was suppressing the opponent's largest revenue line;
feeding the herd instead hands that revenue back. Wheat has five shops draining 30 units a
day, so it is the deepest market in the game and the one every meta-line agent leans on.

The general lesson: **in a duel, denying the opponent revenue can beat producing more of
your own.** An agent tuned on absolute cash — or against a passive opponent — will walk
straight past this. It also means any future "produce more" change has to be gated on
head-to-head win rate, never on own cash.

## `straw0` does not do what its comment says

The comment reads "strawberry tiles planted on day 0 (outer tiles)". Measured at day 6:

| config | day-6 crops | final |
|---|---|---:|
| default | WHEAT 18, CARROT 12, MELON 12, STRAWBERRY 2, TOMATO 2 | $97,618 |
| `straw0` 6 | WHEAT 24, CARROT 5, MELON 12, **STRAWBERRY 0** | $83,058 |
| `straw0` 14 | identical to `straw0` 6 | $83,058 |

Setting it *removes* strawberry from the early farm and costs ~$14k on this seed, and 6
and 14 are indistinguishable because the day-0 budget binds first. Leave it at 0. Worth a
closer look in the opening-book code if anyone revisits the opening.

## Unit-turn accounting: labour is not the problem

Full-game action census, V12 vs the tape on seed 85000:

| | V12 | tape |
|---|---:|---:|
| unit-turns | 6,386 | 6,716 |
| productive | 44% | 42% |
| MOVE | 51% | 43% |
| PASS | 5% | 15% |
| CARE | 142 | 285 |
| FEED | 173 | 290 |
| PLANT | 328 | 202 |

The tape wastes three times as many turns on PASS and still earns 30% more. Labour
efficiency is already at parity; what differs is what the labour is applied to — the tape
tends a high-value herd where we churn short-cycle filler crops. The `feed_days` result
above is the direct test of that, and it did not convert into wins.

## Where this leaves the project

V11 stands: 35W–5L (87.5%) over 40 paired games against the previous `main.py`, and
50/66 = 75.8% across the full reference ladder. Parameter search is exhausted at the
sample sizes available — two rounds of screening produced one validated package (V11) and
nothing since.

The two directions that remain are both blocked or expensive:

1. **Submit V11 and read the real rating.** Five hours to a converged number, and it
   should decide everything after it. Needs `kaggle.json`.
2. **Spend the compute.** The agent uses 2 ms of its 1,000 ms per turn. Turning the
   single-pass greedy day-planner into something that evaluates several candidate plans is
   the only remaining idea with real headroom — and the precedent is discouraging: a
   comparable team logged eleven consecutive failed A/Bs on their closed-loop planner
   before abandoning it for route replay.

## Seeds

Duel screens: 92000–92007. Panel: 85000–85002 across six opponents, both seats.
Validation of the rejected `feed_days`/`carrot_w` pair: 92000–92015, both seats, 24 games.
All disjoint from the seeds used to select V11 (70000s, 80000s, 85000s, 86000s, 90000s).
