---
name: ml-model-selection-playbook
description: Select candidate ML models based on task type, data size, feature characteristics, latency constraints, interpretability requirements, and objective metric.
---

# ML Model Selection Playbook

Use this skill when the user asks which model family to choose.

## Workflow
1. Clarify task:
- classification/regression/ranking
- offline metric and business metric
- constraints: latency, memory, explainability
2. Build candidate set:
- strong baseline
- tree-based model
- linear/interpretable model
- optional advanced model
3. Define comparison protocol:
- CV strategy
- fixed split and seed
- consistent preprocessing
4. Rank models with trade-offs:
- performance
- stability
- complexity
- serving cost
5. Output recommendation with fallback options.

## Output Template
- Problem framing
- Candidate models and rationale
- Evaluation protocol
- Recommended model and why
- Deployment considerations
