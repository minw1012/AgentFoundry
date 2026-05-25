---
name: ml-evaluation-playbook
description: Evaluate ML models comprehensively with metric fit-to-goal, slice analysis, calibration/error analysis, robustness checks, and clear go/no-go recommendation.
---

# ML Evaluation Playbook

Use this skill when the user asks for model evaluation quality, not just a single metric.

## Workflow
1. Confirm metric-goal alignment.
2. Compute core metrics and confidence intervals where feasible.
3. Perform slice-level analysis:
- key segments
- imbalance sensitivity
- failure hotspots
4. Run robustness checks:
- drift sensitivity
- threshold sensitivity
- calibration behavior
5. Produce go/no-go recommendation with risk register.

## Output Template
- Evaluation Setup
- Overall Metrics
- Slice Diagnostics
- Error Analysis
- Risks
- Go/No-Go + Next Actions
