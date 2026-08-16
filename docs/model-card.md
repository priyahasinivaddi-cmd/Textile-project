# Textile Waste Multitask Model Card

## Model

- Name: Textile Waste EfficientNet Multitask
- Version: `2026-08-15T10:18:41.519637+00:00`
- Status: Development model; manual review required
- Selected architecture: EfficientNet-B0 with a shared ImageNet-pretrained backbone
- Alternative evaluated: EfficientNet-B2
- Input: Front-facing RGB garment image resized to 224 × 224
- Outputs: waste usage/destination, garment type, condition score, and primary material probabilities

## Dataset

- Dataset: Clothing Dataset for Second-Hand Fashion
- Identifier: `fnauman/fashion-second-hand-front-only-rgb`
- Pinned revision: `b2559ac0157ea9b6913a65062877f487952e690b`
- License: CC BY 4.0
- Training rows: 24,010
- Validation rows: 4,238
- Official test rows: 3,390
- Split strategy: official test split plus a seeded, usage-stratified validation split

The source dataset has no item or garment identifier. Item-level leakage therefore cannot be proven from the available metadata. This limitation must not be omitted from evaluation reports.

## Test results

| Head | Accuracy | Macro F1 | Weighted F1 |
|---|---:|---:|---:|
| Usage/destination | 0.206 | 0.124 | 0.280 |
| Garment type | 0.581 | 0.392 | 0.595 |
| Condition | 0.231 | 0.205 | 0.238 |
| Primary material | 0.171 | 0.087 | 0.216 |

EfficientNet-B0 was selected because it exceeded B2 on usage, garment-type, and material macro F1. These results do not meet production quality gates for autonomous sorting.

## Intended use

- Operator decision support
- Human-reviewed garment triage
- Workflow prototyping and future model evaluation
- Collection of corrected labels for retraining

## Not intended for

- Autonomous recycling or disposal decisions
- Laboratory-grade fibre identification
- Safety or hazardous-material determinations
- Environmental impact measurement
- Decisions without qualified human review

## Limitations and bias

- Destination classes are severely imbalanced. Reuse and Export dominate, while Repair, Remake, and Energy Recovery have very few examples.
- Visually similar materials are difficult to distinguish from RGB imagery.
- Material strings in the source contain spelling variants and multilingual labels; aliases are consolidated during inference.
- Condition and destination performance is low.
- Sparse damage, stain, hole, smell, and pilling annotations were not promoted as model heads.
- Probabilities are not calibrated and must not be interpreted as measured certainty.

## Operational controls

- A 70% confidence threshold is applied to every head.
- Any head below the threshold sets `manual_review_required=true`.
- The API labels the checkpoint as a development model and reports that quality gates failed.
- Deterministic recommendations remain separate from the advisory model predictions.

AI-generated assessment. Predictions are probabilistic and should be reviewed by qualified personnel for operational recycling decisions.
