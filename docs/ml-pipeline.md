# ML Pipeline

The dataset snapshot is pinned by revision. Inspection records actual columns, missingness, and class distributions. The official test split is preserved; a seeded stratified validation split is created from training data. The dataset has no item identifier, so item-level isolation cannot be proven and is documented as a limitation.

EfficientNet-B0 and B2 share a visual backbone with usage, type, condition, and primary-material heads. Training uses ImageNet transfer learning, mild textile-safe augmentation, per-head class weights, checkpoints, histories, mappings, and per-class reports. B0 is promoted because its macro F1 exceeded B2 for usage, garment type, and material.

Sparse damage, stain, hole, smell, and pilling labels are not automatically promoted. A target must meet configured coverage and class-support thresholds before training.
