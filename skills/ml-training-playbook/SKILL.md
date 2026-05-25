---
name: ml-training-playbook
description: Run reproducible model training with baseline first, controlled experiments, hyperparameter tuning strategy, experiment tracking, and convergence diagnostics.
---

# ML Training Playbook

Use this skill when the user asks to train models or optimize training runs.

## Workflow
1. Establish baseline run first.
2. Define experiment matrix:
- model config
- hyperparameters
- budget
- stopping criteria
3. Train with reproducibility controls:
- random seeds
- versioned data snapshot
- logged config
4. Track metrics and artifacts per run.
5. Select best checkpoint using validation policy.
6. Document reproducible recipe for rerun.

## Guardrails
- Avoid over-tuning on validation repeatedly.
- Keep training budget and stopping logic explicit.
