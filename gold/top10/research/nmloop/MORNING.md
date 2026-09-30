# Overnight controller loop: morning report

Live pair: v33 c2tr (controller) + v32 PFcfc. Nothing was submitted overnight. Today's (30 Sep UTC) 5 slots are open; the deadline is 23:59 UTC.

Ladder ratings at 02:20 UTC: v33 2458.0, v32 2424.3 (older: v31 2466.0, v29 2523.8, v28 T8 2574.0). The final ranking is the 1-15 Oct tournament, so these ratings don't carry over.

The exact file list is in `gold/final/FINAL_MANIFEST.txt`.

A sentinel replays every new v33 ladder game with CGt, c2tr and NMp44Tr every 45 min and flags any game NMp44Tr loses that CGt or c2tr wins. Log: `gold/top10/research/nmloop/sentinel.log`.

## Recommendation (for your yes or no)

Replace both live submissions:

| Slot | File | sha256 |
|---|---|---|
| Tape | `gold/final/CGt_final.py` (frozen 29 Sep; = `gold/submit/main_ctl_CGt.py`) | d1eeea13… |
| Controller | `gold/final/NMp44Tr_final.py` (= `gold/submit/main_ctl_NMp44Tr.py`) | abbc3296… |

ChatGPT agrees with this pair (L20). The two differ only against the new-meta rivals (step-1 money 940-980, no hands). Those are now 66% of top-team seats (Sep 29).

## What NMp44Tr is

NMp44Tr = NMp44T (e746eb2f…) plus a reset-safe wrapper. If Kaggle ever reused the agent module for a second episode, it would restore the load-time settings. In a fresh process it is identical to NMp44T: all 115 ladder games identical, official self-play identical.

NMp44T itself:

- **Everyone except the new-meta band** gets c2tr's tape route. That is the same tape as CGt, except that CGt adds its strawberry spoiler against chassis copies of our own tape. This now includes the herd-first rivals (Boey, Fourth Quadrant). c2tr played its opening controller against them and lost wins to the tape: 16 vs 24 on fresh28, 10 vs 13 on fresh29.
- **New-meta rivals** get c2tr's p1e controller with the NM settings:
  - opening: melon cycle plus a day-10/11 melon cash-out;
  - the cash-out runs only when the cohort is under 12 melons at day 6;
  - once 3 strawberry buyers are visible on days 12-15, it plants strawberries up to 26 plots.

## Evidence (wins)

| Gate | CGt / tape | v33 c2tr | NMp44 | NMp44T |
|---|---|---|---|---|
| fresh28: 851 top-team seats, 27-28 Sep | 132 | 124 | 130 | **138** |
| fresh29: 656 seats, 29 Sep, held out | 25 | ~22 | 25 | **28** |
| old goldg + top10g: 381 seats (tape = T8fcWt) | 134 | 133 | 132 | 133 |
| blind: new-meta fork games in fresh towns, 320 (seeds 9500s + 9600s) | 250 | 250 | 253 | 253 |
| live ladder: all 115 v33 games, rival replayed in its own town | 66 | 66 (live v33: 65) | - | **69** |

- The first blind panel (seeds 9500s) showed +7. It did not replicate on new seeds 9600-9619 (−4); flips swing $20-50k both ways.
- In the live ladder gate, the c2tr replay matches the live outcome in 114 of 115 games. All of NMp44T's +3 comes from the 36 new-meta games. Two of its flips are huge swings, likely artifacts of the rival's recording desyncing.

Ladder mini-gate (the 5 real v33 losses plus azamat): NMp44 margins go from −15.7/−9.9/−23.2/−10.7/−7.8/+9.4k to −11.6/−1.9/−19.9/−6.6/−12.8/+4.5k. It keeps the azamat win and flips none of the losses.

Preflight:
- Kaggle's official self-play on seeds 6042 and 8500: DONE/DONE, 720 steps.
- Imports are identical to c2tr_final.
- 0 errors in 420 fresh960 games.
- Herd-first seats are verified identical to the tape (80 of 81).

## Honest limits

- Against the top teams we still lose most games. On fresh29 the median margin is about −$15.6k, and the new-meta branch gains wins only at the edges.
- The branch's own edge over the tape is +3 (fresh29) and +6 (fresh28). The rest of NMp44T's gain comes from the herd-first routing fix.

## Tried after the freeze and rejected (NMp44T is unchanged)

- **NMp65:** hold animal purchases for melons when the first shop buys milk or yarn.
  - In milk towns, delaying cows destroys big wins: fresh960 wins went 9 → 7, e.g. UMG +$42k → −$16k.
  - Yarn-only is margin-positive but changes no wins.
  - ChatGPT and I agree to keep it out.
- **Crew caps, feed outsourcing / wheat caps, early strawberry selling, earlier strawberries:** neutral or negative.

## Falsification checks
- **State reset:** in a reused module NMp44T's second game missed the day-15 strawberry flag (azamat: win → loss). NMp44Tr fixes this; tested with azamat played twice and after a tape game, both matching the fresh result. The live c2tr has the same class of issue unfixed.
- **Routing audit:** outside the new-meta band NMp44T plays exactly like c2tr (C2S3, chassis, herdpoor, majkel, other) and exactly like the tape against herd-first rivals (12/12 ladder, 80/81 fresh29).
- **Timing:** 0 errors on 420 fresh960 games. NMp44T's worst steps come from the tape route, the same code as CGt and the live v33.
- **Hygiene:** both final files are deterministic across fresh loads and silent on stdout. Replaying 30 games back to back in one module changes 1 game for NMp44Tr and 3 for CGt (copy/self games only). That's documented only; the bytes are unchanged.
- **Sentinel through pass 4 (04:24 UTC):** 140 live v33 games replayed (the 115 plus 25 new). Wins: CGt 81, c2tr 79, NMp44Tr 86.
  - The only flag is wally0593 (CGt +$196, NMp44Tr −$3.5k), already counted in the 115-game result.
  - Herd-first rivals routed to the tape keep improving: Excluding −$13.7k → −$5.9k; syouya tobita −$13.9k → a win.
  - elmo (live −$12.7k, replay +$14.1k for all three candidates) is a replay artifact: the recording needs 30 repaired steps. It isn't a live-code issue.

Nothing is submitted without your yes.
