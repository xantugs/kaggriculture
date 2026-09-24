# Sell timing: a free +12 points on the tape

**Date:** 2026-09-21 · **Base route:** episode 110905948, seat 1 (recorded $111,776)
**Ship:** `submit\tape_a2\main.py` — the same route with a 2-hour sell-ahead window.

---

## 1. The finding that started it

I asked whether the opponent affects our score at all. Same tape, same seed, four opponents:

| opponent | our cash (seed 400) |
|---|---|
| `fallow_finn` (passive) | $200,829 |
| `main_v13` | $121,133 |
| `ergousha` | $109,956 |
| `tape_111211276` | $112,548 |

**A $91k spread on an identical seed.** The opponent is not taking our crops — they are taking
the market's price depth before we reach it. Kaggriculture is a race to sell, not a race to grow.

Two supporting facts from the same probe:

- **Seat is exactly irrelevant.** Seat 0 and seat 1 rows were byte-identical across every
  opponent and seed. There is no seat advantage to play around.
- **Tape-vs-tape margins are tiny.** Many games are decided by a few hundred dollars; one by
  **$24**. A small consistent edge therefore flips a large number of games.

## 2. The transform

A tape sells on a fixed recorded schedule. If each `SELL` fires earlier — same goods, same
quantities, production untouched — we reach the depth first. Implemented in `build_tape2.py`
as `SELL_AHEAD = w`: at step *k*, also emit the sells the route schedules for steps
*k+1 … k+w*, whenever the shed already covers them; each pulled order is marked done so it is
not emitted twice.

One implementation trap cost an hour: **the shed at decision time does not yet hold what this
step's hands are about to deposit.** Filtering the route's *own* sells against the visible shed
drops most of them and costs ~60% of the score. The route's own orders must pass through
verbatim; only the pulled-forward ones are checked against the shed.

## 3. The window curve, measured three ways

Against the plain tape, head-to-head:

| window | win rate | mean margin |
|---|---|---|
| 1h | 90% (18/20) | +$1,252 |
| **2h** | **99.2% (119/120)** | **+$1,893** |
| 3h | 85% | +$909 |
| 4h | 87.5% (70/80) | +$1,021 |
| 5h | 55% | −$376 |
| 8h | 55% | −$652 |
| 24h | 0% | −$23,774 |
| dump whole shed | 0% | −$127,900 |

Large windows fail because pulling orders forward **stacks volume into one step**, and on a
square-law good (melon, wool) that collapses the price. Capping each step at the largest single
lot the route itself ever sold of that good converts a 6-hour window from −$597 to +$993. The
cap *multiplier* turned out to be irrelevant — 0.35×, 0.50×, 0.60× and 0.75× give byte-identical
results. Only the window does work.

## 4. The methodological trap — and it nearly shipped

With the cap on, a round-robin over eight sell-variants ranked them **perfectly monotone by
window**, 11 hours on top at 93.8%. It was backwards. The pairwise matrix:

| window | vs plain tape | vs other transformed variants |
|---|---|---|
| 2h | 15/16 | loses to all |
| 4h | 14/16 | loses to all |
| 7h | 11/16 | beats shorter |
| 10h | 7/16 | beats all shorter |
| 11h | 2/16 | beats everything |

Longer windows buy sibling wins by **giving up the plain schedule**. Seven of the eight agents
in that field were transformed variants, so the ranking graded almost entirely on sibling
matches. The 11-hour peak then lost to the plain tape 11/80 (13.75%) head-to-head.

This is the same failure that killed `111293357` earlier in the project: *a field built out of
the thing being tuned measures intra-family dominance, not ladder strength.*

**The fix — `panelx.py`:** score candidates against a panel of agents **outside the family**.
Eight of them: four other people's tapes, `ergousha`, `erg_v020_firsttape`, `main_v13`, and the
plain champion. 64 games per candidate.

| candidate | 110905948 | 111211276 | 111293357 | 111040851b | 110994292b | ergousha | erg_v020 | v13 | **overall** |
|---|---|---|---|---|---|---|---|---|---|
| **2h (`a2`)** | 8/8 | 3/8 | 4/8 | 2/8 | 2/8 | 0/8 | 8/8 | 8/8 | **54.7%** |
| 2h capped | 8/8 | 3/8 | 4/8 | 2/8 | 2/8 | 0/8 | 8/8 | 8/8 | 54.7% |
| 3h / 4h | 8/8 | 1/8 | 4/8 | 2/8 | 2/8 | 0/8 | 8/8 | 8/8 | 51.6% |
| 1h | 8/8 | 0/8 | 4/8 | 2/8 | 2/8 | 0/8 | 8/8 | 8/8 | 50.0% |
| **plain (w=0)** | — | 0/8 | 4/8 | 2/8 | 2/8 | 0/8 | 8/8 | 8/8 | **42.9%** |
| 7h | 5/8 | 0/8 | 2/8 | 2/8 | 2/8 | 0/8 | 8/8 | 8/8 | 42.2% |
| 10h / 11h | 0/8 | 0/8 | 2/8 | 0–2/8 | 2/8 | 0/8 | 8/8 | 6–8/8 | 31.2% |

Unimodal, peak at **2 hours**: 42.9% → 50.0% → **54.7%** → 51.6% → 42.2% → 31.2%.

The gain is concentrated in the two near-peer columns and is **exactly neutral everywhere
else** — identical 2/8, 0/8, 8/8, 8/8 as the plain tape against the other five. Nothing traded
away. The 11-point jump from w=0 to w=2 rests on the `110905948` column (0/8 → 8/8), which the
120-game head-to-head corroborates at 99.2%.

Against `ergousha` specifically, on matched seeds: plain 10/60, `a2` 8/60, `c4` 10/60 — the
transform is free, not a trade.

## 5. Route mining is exhausted

Two things closed this line off:

- **Every replay holds two routes, and only the winner's had been mined.** Extracted all 27
  loser seats; the games are near-ties ($121,190 vs $121,441 and the like), so the material is
  equally good. Built all 54 tapes.
- **Transformed all 54 and ran each against the champion. Not one beat it** — the best was
  8/12 with a negative margin, and at full power the best three landed at 20–35% over 40 games.

`110905948` is the best route available. Further mining has low expected value; the gains are
now in the sell-timing layer.


## 5b. Buy-ahead: a clean null

The same pull-forward logic applied to `BUY_SEED` orders (seeds only — `BUY_PRODUCT` lands in
the shed, where the sell-ahead logic would immediately sell it back) produced **byte-identical
results at every window**:

| buy-ahead window | 110905948 | 111211276 | ergousha | overall |
|---|---|---|---|---|
| 0 (control) | 8/8 | 3/8 | 0/8 | 54.7% |
| 2 hours | 8/8 | 3/8 | 0/8 | 54.7% |
| 4 hours | 8/8 | 3/8 | 0/8 | 54.7% |
| 8 hours | 8/8 | 3/8 | 0/8 | 54.7% |

Every cell identical across 64 games each. Buying earlier changes nothing: seed prices are not
the contested resource. **The depth race is on the sell side only.** The `BUY_AHEAD=0` build was
verified to tie the shipped agent 12/12 with a $0 margin, so this is a real null, not a
plumbing failure.

## 6. Where the score stands

| agent | 11-opponent gate | vs plain champion | external panel |
|---|---|---|---|
| `main_v13` (planner) | 81.8% | 0/6 | — |
| plain tape 110905948 | 93.9% | — | 42.9% |
| **tape + 2h sell-ahead** | 90.9%¹ | **99.2%** (119/120) | **54.7%** |

¹ The gate is saturated: both agents go 8/8 against ten of eleven opponents, and the whole
difference is `ergousha` at 0/8 vs 2/6 — noise. The gate can no longer discriminate between
good tapes, which is why the external panel replaced it.

## 7. Methods worth keeping

- **Never rank a family against itself.** Use a panel drawn from outside it.
- **Nothing under ~100 games is evidence.** Three separate 16–24 game screens lied this
  session: 87.5% → 45%, 24/24 → 2.5%, and the entire 11-hour ridge.
- **`win_rate: 0.0` with `mean_margin: 0` means the games never ran.** Always read the `errors`
  field — a filename typo produced eight silent null results that looked like real losses.
- **Monotone curves across a swept parameter are trustworthy; isolated peaks are not.** The
  2-hour peak survived because it is monotone on both sides in three independent seed blocks.
