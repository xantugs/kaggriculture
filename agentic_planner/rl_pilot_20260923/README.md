# Private continuation-learning pilot

User authorized running this experiment on their existing Kaggle account.
Project located at `kaggriculture_review/kaggriculture`; the alternate typed path
`kaggriculture/_review` does not exist on this machine.

The experiment is isolated from Claude's `moon` files. `snapshot` contains the
frozen model encoding, common rollout/greedy decoder, official-engine runner and
incumbent. `source_manifest.json` identifies the source hashes. No competition
submission is performed by any script here.

Incumbent: `arena/cand/omw_v13f.py`, SHA-256
`84aa3a851f8f7a6f391a0c794dba2fed5df2d1334fdb14b00072ac4a352842e8`.
The copied incumbent file retains the legacy filename `snapshot/v12.py` for
compatibility. Likewise, inherited log labels saying `v12` refer to **this v13
snapshot**, not the older v12 agent.

## Run design

- Initial weights from the user's completed `offhand/kaggriculture-bc-train`.
- Exact Kaggriculture engine version 1.32.7.
- Incumbent self-play until step 672 or 696; policy takes over the last 47 or 23
  transitions. Opponent continues to run the incumbent and reacts normally.
- Warm-up on both seats of 32 incumbent self-play seeds, eight imitation epochs.
- Sixty RL iterations maximum, eight seed/seat groups per iteration, three
  sampled continuations per start, joint-action clipped probability ratios and
  KL regularization toward the warmed policy. No learned value function; the
  pilot uses group-relative terminal advantages.
- Up to 3,600 seconds before stopping training. Final testing has additional
  overhead. CPU only; no GPU quota allocated.
- Validation after warm-up and every five RL iterations, both seats of four
  fixed seeds at both starting steps. Selection prioritizes win/draw points,
  then mean paired margin improvement.
- Final selected checkpoint and initial model tested on 16 untouched seeds,
  both seats, both starting steps. These final seeds exclude the smoke-test seed.
- Model state and hidden future randomness are not provided to the policy.
  Forked simulator states are used only by the offline evaluator.

## Preflight and limitations

`test_policy.py` checks quantity support at available-stock boundaries, including
the previous train/deploy mismatch. Rollout and evaluation now call the same
`policy.policy_act` function. Observations are recorded in float32 so behavior
and learner probabilities agree. Remote assertions compare NumPy and Torch
conditional log probabilities for actions, quantities and all market heads.

The first smoke test completed two actual optimization iterations and post-update
evaluations in 62 seconds. No rollout errors or lost children occurred. Maximum
checked log-probability discrepancies were below 0.00004. Its four-game test was
only a wiring check and was not used as evidence of playing strength.

The codec still has the previously documented bounded quantities and fixed market
ordering. This is an experimental learning pilot, not a declaration of a lossless
interface. `codec_control.py` separately measures the effect of applying the
codec to incumbent decisions in late continuations. No claim of a gold-level
agent follows from improved imitation or training scores.

## Outputs

Private preflight: https://www.kaggle.com/code/offhand/kaggriculture-codex-rl-smoke-0923

Private pilot: https://www.kaggle.com/code/offhand/kaggriculture-codex-rl-pilot-0923

`kaggle_job.py` reads the existing token without printing it. It supports private
push, status, progress and selective artifact download. Downloads do not forward
the API credential to storage URLs. `outputs/<slug>` holds logs and results.

`analyze.py` computes paired results and uncertainty clustered by independent
seed, keeping the two seats together. Validation selects checkpoints; final test
results must not be reused for tuning this experiment.
