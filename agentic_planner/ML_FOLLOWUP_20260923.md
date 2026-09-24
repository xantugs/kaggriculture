# Follow-up: v13 improves; reinforcement learning is still unmeasured

Scope: supplied Claude transcript ending with the v13 comparison and the RL dry
run; current `moon` source and local results. Here v13 means
`arena/cand/omw_v13f.py`, not the unrelated older `versions/main_v13.py`.

## What the results establish

- v13 beats v12 in the supplied closed-loop result: 163/200, mean +$659.
- I independently recomputed the 188-game paired recorded-opponent comparison
  from `moon/v13_pin96.jsonl`: mean +$91.44, median +$121.50, eight losses changed
  to wins and two wins changed to losses. There are 188 unique games and no
  duplicate game/variant pairs in the 1,692 rows.
- These strong-opponent results use recorded actions after the candidate takes
  over. The official market reacts to changed supply, but the opponent policy
  does not choose new actions. They are useful counterfactual tests, not 188 live
  or closed-loop matches against those elite agents.
- The repaired imitation agent is currently much worse than v12. Fixing the
  earlier codec defects was necessary diagnostic work; it did not produce a
  competitive policy. Full-game and late-game evaluations both failed.
- The RL dry run is **not a learning result**. `rl_dry.py` has `ITERS = 1`,
  `GROUPS = 4`, `K_SAMPLES = 3`, starts 672/696. In `rl_body.py`, rollout scores
  and diagnostics are collected before the optimization loop; the weights are
  exported afterward, without a fresh evaluation. The reported 24 seconds and
  840 training transitions prove the pipeline can collect and update. They say
  nothing about the performance of the updated policy.

## Important differences from the previous review

The new codec fixes initial-shed sale sizing, most small pickup quantities and
deposit-by-product. The trainer now groups episodes and reports action plus
pickup-quantity accuracy and nonzero market metrics. Do not keep describing
87.1% as the old action-class-only metric. It is still per-unit encoded-command
accuracy, not complete joint farm/market action accuracy.

The remaining codec is not fully lossless. It still groups/reorders market
instructions, deposits all of a selected product and caps several quantities.
Claude reports much smaller perfect-label season discrepancies; I did not rerun
that revised season gate here. Its module docstring overstates exactness. Complete
transition fidelity remains desirable, but the remaining discrepancies are not
evidence that another decoder fix will recover the entire current policy gap.

Two concrete issues to resolve before a serious RL pilot:

1. **Training and deployment choose pickup amounts differently.** In
   `bc_layer.py:111`, deployment takes the highest-scoring quantity over all
   classes, then clamps it to available stock. In `rl_body.py:55`, training
   chooses only among quantities up to available stock. Example: three wheat
   available; quantity 13 has the highest score and quantity 1 is best among
   1–3. Deployment takes three, RL's greedy policy takes one. Use one shared
   decoder for rollout, evaluation and submission. Test action equality on real
   snapshots and quantity-boundary examples. This discrepancy's firing rate and
   cost have not been measured.

2. **The built training job does not include the later additions.** The saved
   `bc_v2.py` has only DSM/Vadim teachers and contains neither `SELFPLAY` nor the
   export parity check added to current `bc_body.py`. The transcript likewise
   places those edits after training was launched. Unless a different rebuilt
   job produced the weights, the current model has not been trained on those v12
   takeover states. Treat the feature as implemented, not yet demonstrated in
   the model. Record source and weight hashes with every run. The current export
   check also prints a discrepancy without an assertion and omits quantity
   logits; include them and fail the check on material mismatches.

## Where the imitation model is weak

Last epoch in `moon/bc_train_v3.log`:

| Decision | Nonzero recall | Exact class/quantity on teacher-positive cases |
|---|---:|---:|
| Buy carrot seeds | 56% | 52% |
| Buy tomato seeds | 48% | 47% |
| Sell strawberries | 63% | 52% |
| Sell milk | 69% | 55% |
| Sell wool | 61% | 55% |

These are held-out prediction metrics, not executed trade success rates or
estimated cash losses. They provide specific failures to inspect before choosing
more parameters or more data. Compare balanced/nonzero-weighted losses and
teacher/state coverage using held-out economic outcomes: raising recall alone
can also create costly false purchases or sales.

## Recommended next experiment

Keep the measured v13 improvement as the submission candidate track. In parallel
as a work plan, reserve a bounded 1–2-hour compute pilot for learning once its
preflight checks pass; this is a proposed experiment, not a forecast that two
hours will suffice for a competitive policy.

1. Build and verify one common policy decoder and exported-inference path.
2. Add late-game demonstrations from the actual incumbent v13, with whole seeds
   held out. Fine-tune the imitation policy to operate on those takeover states.
   Report incumbent-state and elite-state results separately. Keep the same
   grouped evaluation and representative elite demonstrations as appropriate.
3. Start RL on the last one or two days. Run repeated rollout/update cycles and
   evaluate **after** updates on a fixed held-out set, including iteration zero.
   Save intermediate checkpoints. Record both win rate and margin relative to
   the incumbent from the same starting state, failures, runtime and uncertainty
   grouped by seed. Use a separate untouched final test after selecting a model.
4. Continue earlier in the season only if fresh-state performance improves.
   A promising learning curve justifies more compute; beating the weak initial
   clone alone does not justify replacing the incumbent.
5. Before expanding the budget, check sampled action/log-probability parity and
   update behavior. The current update clips each action head separately; this
   is a design choice differing from a single joint-action PPO ratio, not by
   itself proof of a bug. It needs a measured learning curve and bounded policy
   change, not the label "PPO" as validation.

The old speed argument also needs updating: the supplied full-game evaluation
fell from 634 seconds to 51 seconds for 16 games, approximately a 12.4-fold
improvement in that setup. The reported new inference is around 4–5 ms per step.
Neither figure is steady-state training throughput. Measure continuation
transitions/second and total evaluation overhead during the pilot. There is no
measured basis here for declaring RL either impossible or certain to work.

## How to assess the tuning work

The fertilization-threshold change alone improves mean recorded-opponent margin
by $104.79; carrot timing by $69.98. Their combination is not guaranteed to equal
the sum, so test the combined candidate.

Do not automatically reject the GLUTH horizon change solely because its mean
margin falls $72.11: it gains six wins and loses three on this panel. Win rate is
the competition objective. This small result also does not establish that GLUTH
helps; compare with/without on fresh games and reacting opponents.

The 47 screening games come from the 188 games already inspected. Checking the
77 sweep winners on all 188 is useful regression coverage, but not independent
confirmation. Reserve previously unused seeds/replays and stop tuning on them.
Do not translate +$659 in v12 mirrors or +$91 in this selected recorded panel
into a promised leaderboard rating increase.

Primary algorithm reference: [Schulman et al., Proximal Policy Optimization
Algorithms](https://arxiv.org/abs/1707.06347). The paper describes repeated
sampling and optimization; it does not establish a Kaggriculture sample budget
or a gold-level outcome for this implementation.
