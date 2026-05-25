---
name: data-preprocessing-playbook
description: Design and execute robust preprocessing for tabular datasets: schema checks, missing values, outliers, leakage prevention, feature encoding/scaling, and train/valid/test protocol.
---

# Data Preprocessing Playbook

Use this skill when the user asks for data cleaning or preprocessing before ML.

## Workflow
1. Profile dataset:
- column types
- missingness
- unique cardinality
- obvious anomalies
2. Define target and split strategy first (prevent leakage).
3. Apply preprocessing plan by type:
- numeric: impute, cap/winsorize if needed, scale when needed
- categorical: clean labels, handle rare classes, encode
- datetime/text: derive features systematically
4. Validate transformations:
- no target leakage
- reproducibility with fixed random seed
- transformed schema checks
5. Produce preprocessing report:
- steps applied
- assumptions
- potential risks

## Guardrails
- Never fit transforms on test set.
- Keep preprocessing in pipeline objects for reproducibility.
