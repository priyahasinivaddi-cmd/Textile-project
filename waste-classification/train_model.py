"""Train a fabric-composition regression model with MobileNetV2."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import tensorflow as tf


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CSV = SCRIPT_DIR / "dataset" / "annotations.csv"
DEFAULT_IMAGE_ROOT = (
    SCRIPT_DIR / "dataset" / "FabricsCompositionDataset" / "FabricsCompositionDataset"
)
IMAGE_SIZE = (224, 224)
SEED = 42


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test", action="store_true", help="Use a small subset and train for one epoch.")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="Annotation CSV path.")
    parser.add_argument("--image-root", type=Path, default=DEFAULT_IMAGE_ROOT, help="Fabric folder root.")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--seed", type=int, default=SEED)
    return parser.parse_args()


def discover_fabrics(
    csv_path: Path, image_root: Path, test_mode: bool, seed: int
) -> tuple[list[tuple[Path, list[float]]], list[str]]:
    annotations = pd.read_csv(csv_path, sep=";")
    if "relative_path" not in annotations.columns:
        raise ValueError("annotations.csv must contain a 'relative_path' column")

    target_columns = [str(column) for column in annotations.columns if str(column).endswith("_pct")]
    if not target_columns:
        raise ValueError("No target columns ending in '_pct' were found")
    annotations[target_columns] = annotations[target_columns].apply(
        pd.to_numeric, errors="coerce"
    ).fillna(0.0)

    fabrics: list[tuple[Path, list[float]]] = []
    missing_folders = 0
    for _, row in annotations.iterrows():
        relative = str(row["relative_path"]).replace("\\", "/")
        if relative.startswith("dataset_root/"):
            relative = relative[len("dataset_root/") :]
        folder = image_root / Path(relative)
        if not folder.is_dir():
            missing_folders += 1
            continue
        images = sorted(path for path in folder.rglob("*") if path.is_file() and path.suffix.lower() == ".png")
        if images:
            fabrics.append((folder, row[target_columns].astype(float).tolist()))

    if len(fabrics) < 3:
        raise ValueError(f"At least 3 valid fabric folders with PNG images are required; found {len(fabrics)}")

    rng = random.Random(seed)
    rng.shuffle(fabrics)
    if test_mode:
        fabrics = fabrics[: min(12, len(fabrics))]

    print(f"Found {len(fabrics)} usable fabric folders; ignored {missing_folders} missing folders.")
    print(f"Targets ({len(target_columns)}): {', '.join(target_columns)}")
    return fabrics, target_columns


def split_fabrics(
    fabrics: list[tuple[Path, list[float]]],
) -> tuple[list, list, list]:
    """Split 70/15/15 while keeping every fabric folder in exactly one split."""
    count = len(fabrics)
    validation_count = max(1, int(round(count * 0.15)))
    test_count = max(1, int(round(count * 0.15)))
    train_count = count - validation_count - test_count
    if train_count < 1:
        train_count, validation_count, test_count = count - 2, 1, 1
    return (
        fabrics[:train_count],
        fabrics[train_count : train_count + validation_count],
        fabrics[train_count + validation_count :],
    )


def expand_images(
    fabrics: list[tuple[Path, list[float]]], test_mode: bool
) -> tuple[list[str], list[list[float]]]:
    paths: list[str] = []
    targets: list[list[float]] = []
    for folder, target in fabrics:
        folder_images = sorted(
            path for path in folder.rglob("*") if path.is_file() and path.suffix.lower() == ".png"
        )
        if test_mode:
            folder_images = folder_images[:20]
        paths.extend(str(path) for path in folder_images)
        targets.extend([target] * len(folder_images))
    return paths, targets


def load_image(path: tf.Tensor, target: tf.Tensor) -> tuple[tf.Tensor, tf.Tensor]:
    image = tf.io.decode_png(tf.io.read_file(path), channels=3)
    image = tf.image.resize(image, IMAGE_SIZE)
    image = tf.cast(image, tf.float32)
    # MobileNetV2's normalization maps RGB values from [0, 255] to [-1, 1].
    image = tf.keras.applications.mobilenet_v2.preprocess_input(image)
    return image, tf.cast(target, tf.float32)


def make_dataset(
    paths: list[str], targets: list[list[float]], batch_size: int, training: bool, seed: int
) -> tf.data.Dataset:
    dataset = tf.data.Dataset.from_tensor_slices((paths, targets))
    if training:
        dataset = dataset.shuffle(len(paths), seed=seed, reshuffle_each_iteration=True)
    dataset = dataset.map(load_image, num_parallel_calls=tf.data.AUTOTUNE)
    return dataset.batch(batch_size).prefetch(tf.data.AUTOTUNE)


def build_model(output_count: int) -> tf.keras.Model:
    augmentation = tf.keras.Sequential(
        [
            tf.keras.layers.RandomFlip("horizontal"),
            tf.keras.layers.RandomRotation(0.08),
            tf.keras.layers.RandomZoom(0.1),
            tf.keras.layers.RandomContrast(0.1),
        ],
        name="training_augmentation",
    )
    base = tf.keras.applications.MobileNetV2(
        input_shape=(*IMAGE_SIZE, 3), include_top=False, weights="imagenet"
    )
    base.trainable = False

    inputs = tf.keras.Input(shape=(*IMAGE_SIZE, 3))
    x = augmentation(inputs)
    x = base(x, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dropout(0.25)(x)
    x = tf.keras.layers.Dense(256, activation="relu")(x)
    outputs = tf.keras.layers.Dense(output_count, name="composition_percentages")(x)
    model = tf.keras.Model(inputs, outputs)
    model.compile(optimizer=tf.keras.optimizers.Adam(1e-3), loss="mse", metrics=["mae"])
    return model


def save_plots(history: dict[str, list[float]], output_dir: Path) -> None:
    for metric, filename, label in (("loss", "loss.png", "Loss (MSE)"), ("mae", "mae.png", "MAE")):
        plt.figure(figsize=(8, 5))
        plt.plot(history[metric], label=f"Training {label}")
        validation_key = f"val_{metric}"
        if validation_key in history:
            plt.plot(history[validation_key], label=f"Validation {label}")
        plt.xlabel("Epoch")
        plt.ylabel(label)
        plt.title(f"Training and validation {label}")
        plt.legend()
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_dir / filename, dpi=150)
        plt.close()


def main() -> None:
    args = parse_args()
    tf.keras.utils.set_random_seed(args.seed)
    output_dir = SCRIPT_DIR

    fabrics, target_columns = discover_fabrics(args.csv, args.image_root, args.test, args.seed)
    train_fabrics, validation_fabrics, test_fabrics = split_fabrics(fabrics)
    splits = [expand_images(split, args.test) for split in (train_fabrics, validation_fabrics, test_fabrics)]
    for name, fabric_split, (paths, _) in zip(
        ("Train", "Validation", "Test"),
        (train_fabrics, validation_fabrics, test_fabrics),
        splits,
    ):
        print(f"{name}: {len(fabric_split)} folders, {len(paths)} images")

    batch_size = min(args.batch_size, 8) if args.test else args.batch_size
    train_dataset = make_dataset(*splits[0], batch_size, True, args.seed)
    validation_dataset = make_dataset(*splits[1], batch_size, False, args.seed)
    test_dataset = make_dataset(*splits[2], batch_size, False, args.seed)

    with (output_dir / "target_columns.json").open("w", encoding="utf-8") as file:
        json.dump(target_columns, file, indent=2)

    model = build_model(len(target_columns))
    checkpoint_path = output_dir / "fabric_composition_model.keras"
    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=7, restore_best_weights=True
        ),
        tf.keras.callbacks.ModelCheckpoint(
            checkpoint_path, monitor="val_loss", save_best_only=True
        ),
    ]
    history = model.fit(
        train_dataset,
        validation_data=validation_dataset,
        epochs=1 if args.test else args.epochs,
        callbacks=callbacks,
    )
    pd.DataFrame(history.history).to_csv(output_dir / "training_history.csv", index_label="epoch")
    save_plots(history.history, output_dir)

    test_loss, test_mae = model.evaluate(test_dataset, verbose=1)
    print(f"Test MSE: {test_loss:.4f} | Test MAE: {test_mae:.4f}")
    print(f"Best model and training artifacts saved in: {output_dir}")


if __name__ == "__main__":
    main()
