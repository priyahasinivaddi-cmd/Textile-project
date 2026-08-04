"""Train the production TextileNet fibre classifier with EfficientNetB0."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tensorflow as tf


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_ROOT = SCRIPT_DIR / "dataset" / "fiber"
DEFAULT_SPLIT_REPORT = SCRIPT_DIR / "dataset_split_report.csv"
DEFAULT_AUDIT_REPORT = SCRIPT_DIR / "fibre_cleaning_audit.csv"
TEXTILENET_FIBRE_ROOT = SCRIPT_DIR / "dataset" / "fiber"
IMAGE_SIZE = (224, 224)
SEED = 42
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"}

TARGET_FOLDERS = {
    "cotton": "cotton",
    "polyester": "polyester",
    "wool": "wool",
    "silk": "silk",
    "linen": "flax_linen",
    "nylon": "nylon",
    "rayon": "viscose_rayon",
    "acrylic": "acrylic",
}
GROUP_NAMES = list(TARGET_FOLDERS)
LIVE_PROGRESS_PATH = SCRIPT_DIR / "training_progress.txt"


class TextProgressLogger(tf.keras.callbacks.Callback):
    """Append compact, human-readable metrics after every completed epoch."""

    def __init__(self, stage: str) -> None:
        super().__init__()
        self.stage = stage
        self.current_epoch = 0

    def on_train_begin(self, logs=None) -> None:
        with LIVE_PROGRESS_PATH.open("a", encoding="utf-8") as handle:
            handle.write(f"\nStage started: {self.stage}\n")

    def on_epoch_begin(self, epoch, logs=None) -> None:
        self.current_epoch = epoch + 1
        total = self.params.get("steps", "?")
        with LIVE_PROGRESS_PATH.open("a", encoding="utf-8") as handle:
            handle.write(
                f"{datetime.now():%Y-%m-%d %H:%M:%S} | {self.stage} | "
                f"epoch {self.current_epoch} started | 0/{total} batches\n"
            )

    def on_train_batch_end(self, batch, logs=None) -> None:
        total = self.params.get("steps")
        completed = batch + 1
        if completed != total and completed % 10 != 0:
            return
        values = logs or {}
        progress = f"{completed}/{total}" if total else str(completed)
        percent = f" ({completed / total:.1%})" if total else ""
        with LIVE_PROGRESS_PATH.open("a", encoding="utf-8") as handle:
            handle.write(
                f"{datetime.now():%Y-%m-%d %H:%M:%S} | {self.stage} | "
                f"epoch {self.current_epoch} | batches {progress}{percent} | "
                f"running_accuracy {values.get('accuracy', 0):.4%} | "
                f"running_loss {values.get('loss', 0):.4f}\n"
            )

    def on_epoch_end(self, epoch, logs=None) -> None:
        values = logs or {}
        line = (
            f"{datetime.now():%Y-%m-%d %H:%M:%S} | {self.stage} | "
            f"epoch {epoch + 1} | accuracy {values.get('accuracy', 0):.4%} | "
            f"validation_accuracy {values.get('val_accuracy', 0):.4%} | "
            f"loss {values.get('loss', 0):.4f} | "
            f"validation_loss {values.get('val_loss', 0):.4f}\n"
        )
        with LIVE_PROGRESS_PATH.open("a", encoding="utf-8") as handle:
            handle.write(line)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--split-report", type=Path, default=DEFAULT_SPLIT_REPORT)
    parser.add_argument("--audit-report", type=Path, default=DEFAULT_AUDIT_REPORT)
    parser.add_argument("--max-train-per-class", type=int, default=4000)
    parser.add_argument("--max-test-per-class", type=int, default=250)
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--fine-epochs", type=int, default=15)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--validation-split", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument(
        "--min-accuracy", type=float, default=0.90,
        help="Minimum test accuracy required before replacing the production model.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from best_fabric_model.keras instead of building a new model.",
    )
    parser.add_argument(
        "--initial-epoch",
        type=int,
        default=0,
        help="Number of already completed main-training epochs.",
    )
    parser.add_argument(
        "--resume-from",
        type=Path,
        help="Checkpoint to load; defaults to best_fabric_model.keras.",
    )
    parser.add_argument(
        "--fine-tune-only",
        action="store_true",
        help="Skip main training and run only the fine-tuning phase.",
    )
    parser.add_argument(
        "--fine-initial-epoch",
        type=int,
        default=0,
        help="Number of already completed fine-tuning epochs.",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run one epoch with a small sample to verify the complete pipeline.",
    )
    return parser.parse_args()


def image_count(folder: Path) -> int:
    return sum(
        path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
        for path in folder.rglob("*")
    )


def validate_dataset(data_root: Path) -> list[str]:
    train_root = data_root / "train"
    test_root = data_root / "test"
    if not train_root.is_dir() or not test_root.is_dir():
        raise ValueError(f"Expected train and test folders below {data_root}")

    class_names = sorted(path.name for path in train_root.iterdir() if path.is_dir())
    if len(class_names) < 2:
        raise ValueError("At least two training class folders are required")

    missing_test_classes = [name for name in class_names if not (test_root / name).is_dir()]
    empty_train_classes = [name for name in class_names if image_count(train_root / name) == 0]
    if missing_test_classes:
        raise ValueError(f"Test folders are missing for: {', '.join(missing_test_classes)}")
    if empty_train_classes:
        raise ValueError(f"Training folders have no images: {', '.join(empty_train_classes)}")

    print(f"Validated {len(class_names)} classes")
    print(f"Training images: {image_count(train_root):,}")
    print(f"Test images: {image_count(test_root):,}")
    return class_names


def load_target_report(args: argparse.Namespace) -> pd.DataFrame:
    rng = np.random.default_rng(args.seed)
    rows: list[dict[str, object]] = []
    allowed_paths: set[Path] | None = None
    if args.audit_report.is_file():
        audit = pd.read_csv(args.audit_report)
        allowed_paths = {
            Path(path).resolve()
            for path in audit.loc[audit["status"] == "ok", "path"].astype(str)
        }
        print(f"Using cleaned audit allowlist: {len(allowed_paths):,} verified images")
    for label, class_name in enumerate(GROUP_NAMES):
        folder_name = TARGET_FOLDERS[class_name]
        train_files = sorted(
            path for path in (TEXTILENET_FIBRE_ROOT / "train" / folder_name).iterdir()
            if path.is_file()
            and path.suffix.lower() in SUPPORTED_EXTENSIONS
            and (allowed_paths is None or path.resolve() in allowed_paths)
        )
        test_files = sorted(
            path for path in (TEXTILENET_FIBRE_ROOT / "test" / folder_name).iterdir()
            if path.is_file()
            and path.suffix.lower() in SUPPORTED_EXTENSIONS
            and (allowed_paths is None or path.resolve() in allowed_paths)
        )
        rng.shuffle(train_files)
        rng.shuffle(test_files)
        selected_train = train_files[: args.max_train_per_class]
        validation_count = max(1, round(len(selected_train) * args.validation_split))
        for image_path in selected_train[:validation_count]:
            rows.append({"split": "validation", "absolute_path": str(image_path), "label": label})
        for image_path in selected_train[validation_count:]:
            rows.append({"split": "train", "absolute_path": str(image_path), "label": label})
        for image_path in test_files[: args.max_test_per_class]:
            rows.append({"split": "test", "absolute_path": str(image_path), "label": label})
    report = pd.DataFrame(rows)
    print("Selected target images:", len(report))
    print(report.groupby(["split", "label"]).size().unstack(fill_value=0))
    return report


def load_datasets(args: argparse.Namespace, report: pd.DataFrame):
    batch_size = min(args.batch_size, 8) if args.test else args.batch_size
    autotune = tf.data.AUTOTUNE

    def decode(path, label):
        image = tf.io.decode_image(
            tf.io.read_file(path), channels=3, expand_animations=False
        )
        image.set_shape((None, None, 3))
        return tf.image.resize(image, IMAGE_SIZE), label

    datasets = []
    for split in ("train", "validation", "test"):
        rows = report.loc[report["split"] == split]
        dataset = tf.data.Dataset.from_tensor_slices(
            (rows["absolute_path"].tolist(), rows["label"].tolist())
        )
        if split == "train":
            # Rows are assembled class-by-class, so the complete training set
            # must be shuffled to prevent long class-biased batch sequences.
            dataset = dataset.shuffle(
                len(rows), seed=args.seed, reshuffle_each_iteration=True
            )
        dataset = dataset.map(decode, num_parallel_calls=autotune).batch(batch_size)
        if args.test:
            dataset = dataset.take(12 if split == "train" else 4)
        datasets.append(dataset.prefetch(autotune))
    return tuple(datasets)


def grouped_class_weights(report: pd.DataFrame) -> dict[int, float]:
    counts = np.zeros(len(GROUP_NAMES), dtype=np.float64)
    training_counts = report.loc[report["split"] == "train", "label"].value_counts()
    for index, count in training_counts.items():
        counts[int(index)] = int(count)
    if np.any(counts == 0):
        empty = [GROUP_NAMES[index] for index in np.flatnonzero(counts == 0)]
        raise ValueError(f"Grouped classes have no training images: {', '.join(empty)}")
    # Square-root weighting corrects the large imbalance without allowing a
    # small class to dominate every update.
    weights = np.sqrt(counts.max() / counts)
    weights /= weights.mean()
    print("Training counts:", dict(zip(GROUP_NAMES, counts.astype(int))))
    print("Class weights:", dict(zip(GROUP_NAMES, weights.round(3))))
    return {index: float(value) for index, value in enumerate(weights)}


def build_model(class_count: int) -> tuple[tf.keras.Model, tf.keras.Model]:
    augmentation = tf.keras.Sequential(
        [
            tf.keras.layers.RandomFlip("horizontal_and_vertical"),
            tf.keras.layers.RandomRotation(0.08),
            tf.keras.layers.RandomZoom(0.15),
            tf.keras.layers.RandomTranslation(0.05, 0.05),
            tf.keras.layers.RandomContrast(0.15),
            tf.keras.layers.RandomBrightness(0.12, value_range=(0, 255)),
        ],
        name="training_augmentation",
    )
    base = tf.keras.applications.EfficientNetB0(
        input_shape=(*IMAGE_SIZE, 3), include_top=False, weights="imagenet"
    )
    base.trainable = False

    inputs = tf.keras.Input(shape=(*IMAGE_SIZE, 3))
    x = augmentation(inputs)
    x = base(x, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    
    # Enhanced Classification Head
    x = tf.keras.layers.Dense(
        128, activation="relu", kernel_regularizer=tf.keras.regularizers.l2(1e-4)
    )(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Dropout(0.3)(x)
    
    outputs = tf.keras.layers.Dense(
        class_count,
        activation="softmax",
        kernel_regularizer=tf.keras.regularizers.l2(1e-4),
        name="fibre_class",
    )(x)
    model = tf.keras.Model(inputs, outputs)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model, base


def save_plots(history: dict[str, list[float]], output_dir: Path, prefix: str = "") -> None:
    for metric in ("loss", "accuracy"):
        plt.figure(figsize=(8, 5))
        plt.plot(history.get(metric, []), label=f"Training {metric}")
        validation_metric = f"val_{metric}"
        if validation_metric in history:
            plt.plot(history[validation_metric], label=f"Validation {metric}")
        plt.xlabel("Epoch")
        plt.ylabel(metric.title())
        plt.title(f"Training and validation {metric}")
        plt.legend()
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_dir / f"{prefix}{metric}.png", dpi=150)
        plt.close()


def main() -> None:
    args = parse_args()
    LIVE_PROGRESS_PATH.write_text(
        "Textile fibre model training progress\n"
        f"Started: {datetime.now():%Y-%m-%d %H:%M:%S}\n"
        "Model: EfficientNetB0\n"
        f"Target production accuracy: {args.min_accuracy:.2%}\n",
        encoding="utf-8",
    )
    if args.initial_epoch < 0 or args.initial_epoch >= args.epochs:
        raise ValueError("--initial-epoch must be between 0 and epochs - 1")
    if args.initial_epoch and not args.resume:
        raise ValueError("--initial-epoch requires --resume")
    if args.test and args.resume:
        raise ValueError("--test and --resume cannot be used together")
    fine_epochs = args.fine_epochs
    if fine_epochs < 1:
        raise ValueError("--fine-epochs must be at least 1")
    if args.fine_tune_only and not args.resume:
        raise ValueError("--fine-tune-only requires --resume")
    if args.fine_initial_epoch < 0 or args.fine_initial_epoch >= fine_epochs:
        raise ValueError(f"--fine-initial-epoch must be between 0 and {fine_epochs - 1}")

    tf.keras.utils.set_random_seed(args.seed)
    report = load_target_report(args)
    train, validation, test = load_datasets(args, report)

    production_model_path = SCRIPT_DIR / "best_fabric_model.keras"
    model_path = SCRIPT_DIR / ("test_fabric_model.keras" if args.test else "candidate_fabric_model.keras")
    fine_model_path = SCRIPT_DIR / "candidate_fine_tuned_model.keras"
    latest_model_path = SCRIPT_DIR / "latest_fabric_model.keras"
    if args.resume:
        resume_path = args.resume_from or model_path
        if not resume_path.is_file():
            raise FileNotFoundError(f"Resume checkpoint is missing: {resume_path}")
        model = tf.keras.models.load_model(resume_path)
        if int(model.output_shape[-1]) != len(GROUP_NAMES):
            raise ValueError("Checkpoint output count does not match the grouped classes")
        base = next(
            layer for layer in model.layers
            if isinstance(layer, tf.keras.Model) and "efficientnet" in layer.name
        )
        print(f"Loading resume checkpoint: {resume_path}")
    else:
        model, base = build_model(len(GROUP_NAMES))

    callbacks = [
        TextProgressLogger("frozen_backbone"),
        tf.keras.callbacks.ModelCheckpoint(
            model_path, monitor="val_loss", save_best_only=True
        ),
        tf.keras.callbacks.ModelCheckpoint(latest_model_path, save_best_only=False),
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=4, restore_best_weights=True
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.3, patience=2, min_lr=1e-7
        ),
    ]
    class_weights = grouped_class_weights(report)

    history_data: dict[str, list[float]] = {}
    if not args.fine_tune_only:
        history = model.fit(
            train,
            validation_data=validation,
            epochs=1 if args.test else args.epochs,
            initial_epoch=args.initial_epoch,
            callbacks=callbacks,
            class_weight=class_weights,
        )
        history_data = history.history

    # Fine-tune the last EfficientNetB0 layers after the classification head settles.
    if not args.test and args.epochs > 1:
        base.trainable = True
        for layer in base.layers[:-50]:
            layer.trainable = False
        model.compile(
            optimizer=tf.keras.optimizers.Adam(1e-5),
            loss="sparse_categorical_crossentropy",
            metrics=["accuracy"],
        )
        
        # Fresh callbacks for fine-tuning to reset early stopping and plateau tracking
        fine_callbacks = [
            TextProgressLogger("fine_tuning"),
            tf.keras.callbacks.ModelCheckpoint(
                fine_model_path, monitor="val_loss", save_best_only=True
            ),
            tf.keras.callbacks.ModelCheckpoint(latest_model_path, save_best_only=False),
            tf.keras.callbacks.EarlyStopping(
                monitor="val_loss", patience=5, restore_best_weights=True
            ),
            tf.keras.callbacks.ReduceLROnPlateau(
                monitor="val_loss", factor=0.3, patience=2, min_lr=1e-7
            ),
        ]
        
        fine_history = model.fit(
            train,
            validation_data=validation,
            epochs=fine_epochs,
            initial_epoch=args.fine_initial_epoch,
            callbacks=fine_callbacks,
            class_weight=class_weights,
        )
        for key, values in fine_history.history.items():
            history_data.setdefault(key, []).extend(values)

    # Fine-tuning is not automatically better. Preserve whichever stage has
    # the lowest validation loss before evaluating once on the test set.
    stage_paths = (model_path,) if args.test else (model_path, fine_model_path)
    candidate_paths = [path for path in stage_paths if path.is_file()]
    scored_candidates = []
    for candidate_path in candidate_paths:
        candidate = tf.keras.models.load_model(candidate_path, compile=False)
        candidate.compile(loss="sparse_categorical_crossentropy", metrics=["accuracy"])
        val_loss, val_accuracy = candidate.evaluate(validation, verbose=0)
        scored_candidates.append((val_loss, -val_accuracy, candidate_path))
        print(
            f"Validation checkpoint {candidate_path.name}: "
            f"loss={val_loss:.4f}, accuracy={val_accuracy:.2%}"
        )
    _, _, selected_path = min(scored_candidates)
    model = tf.keras.models.load_model(selected_path, compile=False)
    if selected_path != model_path:
        model.save(model_path)
    print(f"Selected checkpoint: {selected_path.name}")
    model.compile(loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    test_loss, test_accuracy = model.evaluate(test, verbose=1)

    if not args.test:
        candidate_labels = SCRIPT_DIR / "candidate_class_names.json"
        candidate_labels.write_text(json.dumps(GROUP_NAMES, indent=2), encoding="utf-8")
        if test_accuracy >= args.min_accuracy:
            os.replace(model_path, production_model_path)
            os.replace(candidate_labels, SCRIPT_DIR / "class_names.json")
            print(f"Promoted candidate model (accuracy {test_accuracy:.2%}) to production")
        else:
            print(
                f"Candidate retained but not promoted: {test_accuracy:.2%} is below "
                f"the required {args.min_accuracy:.2%}"
            )
    pd.DataFrame(history_data).to_csv(
        SCRIPT_DIR / ("test_training_history.csv" if args.test else "training_history.csv"),
        index_label="epoch",
    )
    save_plots(history_data, SCRIPT_DIR, prefix="test_" if args.test else "")
    print(f"Test loss: {test_loss:.4f} | Test accuracy: {test_accuracy:.4%}")
    print(f"Evaluated model: {model_path if model_path.exists() else production_model_path}")


if __name__ == "__main__":
    main()
