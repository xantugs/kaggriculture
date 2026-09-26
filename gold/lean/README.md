# gold/lean — the m5 submission, shortened (27 Sep)

`gold/submit/main_ctl_mkt5_lean.py` plays exactly like `gold/submit/main_ctl_mkt5_m7.py` (m5): 9,260 lines and
1.19 MB instead of 11,216 lines and 1.21 MB. Every step's action stream was compared on 19 games against m4 (seeds
6000-6017) and on 36 repaired elite seats in their towns (`harness/same_play.py`): identical on all 55.

How it was made (all exact transformations):
- `shrink.py ctl.py cfg_m5.json ctl_lean.py`: the controller's 106 switches that m5 never changes (63 never set and
  falsy, 40 set once by the configuration, 3 overrides that never change a value) become constants; the branches
  behind them, the functions nothing references any more (opening mode, tape patches, annex workers, arbitrage,
  copy forecasts, ...) and the telemetry writes go; m5's configuration is baked into `GC_P`: 4,244 -> 2,678 lines.
- `strip_chassis.py`: comments and docstrings out of the public chassis, the Apache notice kept once at the top
  (7,668 -> 7,205).
- `bisect_layers.py`: of the chassis's 54 stacked `agent` layers, 5 never change play on 11 games (seeds and elite
  seats); those 367 lines go. The other 49 all act somewhere, so the chassis stays long.
- write-only telemetry dicts' updates go (46 dicts); `fold_chassis.py`: 66 module-level constant flags fold.
  No function is removed from the chassis: it picks its entry point positionally
  (`_V11_ENTRY = [v for v in globals().values() if callable(v)][-1]`), so a deleted definition re-points it.

What stays: the 41-route tape (one 553 KB line), two exec'd planners, and the 49 live layers. A shorter agent means
re-deriving those layers by hand, which changes play; the elite gate (13 minutes a run) is the judge for that.
