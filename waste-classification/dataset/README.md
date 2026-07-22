# Annotated Textile Fabric Image Dataset for Visual, Composition, and Material Property Analysis

## About this dataset

The **Annotated Textile Fabric Image Dataset for Visual, Composition, and Material Property Analysis** is a curated dataset of textile fabric sample images with structured metadata annotations.

The dataset contains **12,724 images** representing **44 unique textile fabric samples**. Each fabric sample is described by metadata such as fiber composition, thickness, fabric weight, number of colors, pattern type, number of images, and supplier or curator notes.

The dataset is intended for textile image analysis, computer vision research, image retrieval, visual similarity analysis, metadata-aware analysis, and future machine learning experiments related to fabric composition and material properties.

The metadata include normalized fiber-composition fields such as polyester, polyamide, acrylic, elastane, cotton, and other fiber percentages. Supplier abbreviations were interpreted according to the dataset-specific normalization rules described in `fiber_codebook.csv`.

No machine learning models are trained or included in this dataset release. This release focuses on dataset structure, annotation quality, image quality statistics, and readiness for future reproducible research.

Users should note that multiple images belong to the same fabric sample. Therefore, any future train/validation/test split should be performed by fabric sample rather than by individual image to avoid data leakage.

## Dataset contents

Recommended file structure:

```text
dataset/
├── images/ or fabric sample folders
├── annotations.csv
├── data_dictionary.csv
├── fiber_codebook.csv
└── README.md
```

## Metadata file

The main annotation file should be named:

```text
annotations.csv
```

Each row describes one textile fabric sample. The `relative_path` field links the metadata record to the corresponding image folder or image path in the dataset.

## Important columns

- `relative_path`: relative path to the image folder or image file.
- `id`: stable fabric sample identifier.
- `num_colors`: number of visible colors in the fabric sample.
- `notes`: raw supplier or curator notes.
- `weight_gsm`: fabric weight in grams per square meter.
- `pattern`: pattern or layout category, when available.
- `composition`: normalized human-readable fiber composition.
- `*_pct`: numeric fiber-percentage columns.
- `thickness_mm`: measured fabric thickness in millimeters.
- `images`: number of images associated with the fabric sample.

See `data_dictionary.csv` for the full column-level description.

## Fiber-code normalization

Supplier abbreviations were interpreted according to the dataset-specific rules:

- `PA` -> acrylic / polyacrylic
- `NY` / `Nylon` -> polyamide / nylon
- `EA` / `EL` / `Lycra` -> elastane
- `PES` / `PL` -> polyester

See `fiber_codebook.csv` for the full mapping.

## Intended use

This dataset can be used for:

- textile image analysis;
- fabric visual similarity search;
- image retrieval;
- metadata-aware textile analysis;
- dominant-fiber prediction;
- multi-label fiber-composition analysis;
- exploratory material-property prediction;
- dataset validation and reproducible machine learning workflows.

## Limitations

- Some metadata fields are derived from supplier notes and may require manual review.
- Some pattern labels are missing.
- Several images belong to the same fabric sample, so image-level random splitting can cause data leakage.
- The dataset should not be used for claims about real-world textile performance without additional laboratory validation.

## Recommended split strategy

For future machine learning experiments, split the dataset by `id` / fabric sample, not by individual image. This prevents images from the same textile sample appearing in both training and test sets.

## License

If all images were created by the dataset authors, a suitable open-data license is **CC BY 4.0**, which allows reuse with attribution. If a more restrictive research-only release is desired, **CC BY-NC 4.0** can be considered, but it limits commercial reuse.

