# Final candidates, frozen 29 Sep 2026 15:00 UTC

Upload these exact bytes (a copy with the same hashes is in `../../../kaggriculture_FINAL_20260929/`):

| file | sha256 | what it is |
|---|---|---|
| FWt_final.py | 42196f53ee5585bde4ed63e24ee830e7ee75faf7e8b2fe9ec3d9aaab9f3bf553 | tape: v29 TP_A31g + phase forecast (milk, strawberry, wool, tomato), controller from day 16 |
| T8fcWt_final.py | bf1da4485f17bfb81fdf33ca10b4bd133d06ed010870e117787c3eec3d966c3e | tape: T8 + the same forecast, controller from day 20 |
| c2tr_final.py | fb1b68e2b2581c2ecd4d7f06878f8207835c2c8869da72e284dfaac6639bad9e | controller: T8fcWt, except vs herd-first rivals (about 11% of ladder games), where the p1e opening controller plays |

Each is byte-identical (`cmp`) to `gold/submit/main_ctl_{FWt,T8fcWt,c2tr}.py` and to the gated builds in `gold/top10/cands/`.

## Elite gates (goldg 111 + top10g 270 seats, all opponent-stable), exact bytes

| | FWt | T8fcWt | c2tr | live v29fc | live PFcfc |
|---|---|---|---|---|---|
| wins goldg / top10g | 56 / 75 | 57 / 77 | 57 / 76 | 55 / 71 | 50 / 68 |
| total wins of 381 | 131 | 134 | 133 | | |

A rerun on the exact bytes reproduced every seat of all three files (identical result and margin, 381/381 each).

Wins by rival class (FWt / T8fcWt / c2tr; shared losses; FW-only / T8-only):
chassis 20: 10/11/11, 9, 0/1. C2S3 230: 86/86/86, 143, 1/1. herdpoor 41: 21/22/22, 18, 1/2.
herdfirst 60: 6/7/6, 53, 0/1. majkel 22: 5/5/5, 16, 1/1. other 8: 3/3/3, 5, 0/0.
At least one of the two tapes wins 137 of 381.

## Preflight (exact bytes)

- `py_compile` passes. Imports are stdlib only (base64, copy, itertools, json, math, random, time, zlib).
- No network, subprocess, ctypes, os/sys or file I/O. The one `open()` sits behind `path = None`.
- No team, username or episode-id reads. The only game-seed read is in dead code (`_ALT_MODE = 'HybridOpening'`).
- Official kaggle_environments validation episode (self-play), seeds 6042 and 8500: DONE/DONE, 720 steps, for all three.
- Smoke (both seats, 12 opponents, seeds 8200-8211 and 8600-8619), 0 exceptions, NaN or controller errors:
  - FWt: 528 games, 458 W 42 T 28 L.
  - T8fcWt: 528 games, 468 W 60 L.
  - c2tr: 288 games, 266 W 22 L.
  - Nearly every loss or tie is against our own tapes (T8, FW). The exception is 2 of 64 FWt games against the public omw_v15a copy.
- Determinism: two fresh loads give identical action traces and results.
- State reset: game B after game A in the same process equals a fresh game B.
- stdout: 0 chars. Memory is flat over 6 games.
- Step time on an idle machine: max 0.56 s (FWt), 0.62 s (T8fcWt), 0.64 s (c2tr), always at step 480, with zero overage used. Under a 36-process load FWt reached 4.45 s; the overage bank is 60 s per game.
- Live: 185 ladder games of v29fc + PFcfc (same code paths), every status DONE.

## Choice (the owner decides)

- For pure rank: FWt + T8fcWt (ChatGPT round 4 and 5).
- For one tape + one controller: FWt + c2tr. It costs 1 observed elite win in 381, on herd-first seats.
- Submit the tape first, check it is live, then the second file. Only the latest 2 submissions count.

## Known weakness (not fixable safely before the deadline)

- Towns with no yarn store (34% of seats): FWt wins 26% there vs 41% with one yarn store, and the gap vs the elite grows to -$5.8k.
- The elite shifts to wheat, eggs and carrots and buys fewer animals in those towns.
- Shops unlock one at a time from day 3, so the opening cannot see the town.
