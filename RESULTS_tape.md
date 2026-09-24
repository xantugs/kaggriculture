# Route mining — a 93.9% ladder agent, and three ideas that failed

21 September 2026. Engine: kaggle-environments 1.32.7.

`main_tape_110905948.py` SHA-256 prefix `c2cc463e3c6ecee76e13`, 16.7 KB, stdlib only.

Built from public Kaggle episode replays, which the competition host has explicitly
confirmed is permitted: asked directly whether "replay-derived tapes from public episode
replays" breach Rule 3.14.a, Kaggle staff answered *"Using public replays to train, build,
inform your submission is allowed and encouraged."* (discussion 738837).

## The agent

A verbatim replay of the 719-step action route recorded by the winning seat of episode
110905948 (2026-09-19), whose agent was rated **2813**. No repair layers — they measured
worthless (below). Hands are padded or truncated to the live hand count; market orders are
capped at 10; a try/except returns a legal no-op.

| | ladder | vs first public tape | vs strongest public tape | vs V13 |
|---|---:|---:|---:|---:|
| V11 | 75.8% | 2/6 | 0/6 | — |
| V13 | 81.8% | 0/6 | 0/6 | — |
| **tape 110905948** | **93.9%** | **6/6** (+$28,189) | 2/6 (−$7,320) | **90%** (+$28,812) |

Full ladder gate, three paired seeds, both seats, **zero errors in 66 games**: 6/6 against
every reference tier 0–5, 6/6 against a public hand-written planner, 6/6 against
`main_v9_capguard` and the old `main.py`, 6/6 against the earlier public tape, 2/6 against
the strongest one.

Timing: import 3.0 ms, **mean 0.007 ms/turn, max 0.051 ms** against a 1-second limit.

## How the nine candidates were chosen

`GET /competitions/episodes/<id>/replay.json` is public and unauthenticated, as is
`competitions.EpisodeService/GetEpisode`. Episode IDs map monotonically to time
(91.5M ≈ 10 Aug, 111M ≈ 19 Sep), so the recent space can be sampled directly and each
candidate filtered on both agents' ratings and rewards before downloading 33 MB.

Nine routes were mined and ranked against the strongest reference tape, 20 paired games
each on one common seed set:

| tape | source rating | win rate | mean margin |
|---|---:|---:|---:|
| **110905948** | 2813 | **35%** | **−$4,560** |
| 110489425 | 2677 | 30% | −$8,464 |
| 111040851 | 2806 | 30% | −$10,182 |
| 110575890 | 2825 | 30% | −$12,219 |
| 110783009 | 2770 | 25% | −$10,294 |
| 110636388 | 2915 | 20% | −$9,112 |
| 110970300 | 2841 | 20% | −$20,141 |
| 111135179 | 2808 | 10% | −$13,231 |
| 110994292 | 2857 | 0% | −$14,708 |

110905948 also ranked first on an earlier, disjoint seed set, so the selection replicates.

**Source rating barely predicts tape quality.** The highest-rated source (2915, at the
gold cutoff) yielded a 20% tape; the 2857 yielded the worst in the set. Rating measures the
*agent*; what transfers is a route that survives open-loop replay, and those are different
properties. Likewise **recorded reward is actively misleading**: 110489425 banked $153,599
on tape, the most of any candidate, and went 0/20 against a strong opponent — a high
recorded score usually means the opponent failed to contest the market.

## Two bugs that cost hours, both worth recording

**Off-by-one in the replay format.** kaggle-environments stores the action at index *i* as
the one taken *from* the observation at index *i−1*. Replaying `route[step]` scores **$0**
every time. Caught by recording a local game, replaying it, and diffing emitted actions
against the live agent's: 713 mismatches at `route[step]`, **zero** at `route[step+1]`.
With the fix, replaying a recording against its original opponent on its original seed
reproduces the recorded reward exactly ($117,458).

**The weed-repair "shift" destroys tapes.** The published notebooks describe substituting
DIG for a scripted plant that lands on a weed, replaying the intent next step, and shifting
the route. Implemented faithfully, that desynchronises everything: over four fresh seeds,
**$33.7k with the shift versus $84.5k plain verbatim**. The tape now replays in strict
lockstep with no cursor movement.

## Three things that measured worthless

**Repair layers.** Weed repair and sell-slot reordering, alone and together, changed the
mean margin by **less than $10** over 24 games against the strongest tape (−8,636 /
−8,638 / −8,646). Verbatim is simpler and identical.

**The tape/planner hybrid.** The idea: replay the tape, but hand control to V13 when live
cash falls below what the recording held at the same step — tapes are open-loop and their
documented failure is going bankrupt when the market drifts. Four switch thresholds, 20
paired games each:

| switch | win rate | mean margin |
|---|---:|---:|
| ratio 0.3, from day 14 | 35% | −$4,560 (never fired) |
| ratio 0.5, from day 12 | 35% | −$4,560 (never fired) |
| ratio 0.7, from day 10 | 25% | −$7,167 |
| ratio 0.9, from day 8 | 25% | −$19,303 |

Whenever the switch actually fires it **loses money**. V13's economy is weaker than the
tape's even from a position where the tape is behind. The hybrid is kept in `hybrid/` as a
negative result.

**Endgame liquidation.** The tape ends every game with an empty shed, nothing carried, and
zero unsold value. There is nothing to recover.

## Reproduce

```
python3 extract_route.py replays/<id>.json routes     # route (~120 KB)
python3 extract_cash.py  replays/<id>.json routes     # reference cash series
python3 build_tape.py routes/route_<id>.json tapes/tape_<id>.py
python3 ladder.py '{}' <seeds> tapes/tape_<id>.py     # the gate
```

Seeds: selection 97000–97003 and 98000–98009; ranking 99900–99909; ladder 99000–99002;
hybrid 99900–99909. Selection and ranking sets are disjoint.

## What is not established

The tape has never played the live ladder. Its source agent was rated 2813 and silver is
2617, but a replayed route is not its source agent — local validation says it beats
everything available except one private reference tape, and that is the whole of the
evidence.
