"""Train a shared EfficientNet-B0/B2 textile model on the verified HF dataset."""
from __future__ import annotations

import argparse
import json
import os
import random
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import tensorflow as tf
from datasets import load_dataset
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "ml" / "configs" / "multitask.json"
RAW = ROOT / "ml" / "data" / "raw" / "fashion-second-hand-front-only-rgb" / "data"
OUT = ROOT / "ml" / "artifacts" / "multitask"
CACHE = ROOT / ".hf-cache" / "datasets"


def primary_material(value: object) -> str:
    text = str(value or "unknown").lower()
    aliases = {"poly": "polyester", "elastan": "elastane", "acryl": "acrylic", "ull": "wool", "viscose": "viscose"}
    candidates = []
    import re
    for percent, name in re.findall(r"(\d+(?:\.\d+)?)\s*%\s*([a-z]+)", text):
        normalized = aliases.get(name, name)
        candidates.append((float(percent), normalized))
    return max(candidates, default=(0.0, "unknown"))[1]


def normalized(row: dict, key: str) -> str:
    if key == "condition":
        return str(max(1, min(5, int(row.get(key) or 1))))
    if key == "material":
        return primary_material(row.get(key))
    value = str(row.get(key) or "unknown").strip().lower()
    if key == "usage":
        return {"rcycle": "recycle"}.get(value, value)
    return value


def normalize_value(value: object, key: str) -> str:
    return normalized({key: value}, key)


class Batches(tf.keras.utils.PyDataset):
    def __init__(self, data, indices, mappings, weights, size, batch, shuffle):
        super().__init__()
        self.data, self.indices, self.mappings = data, np.asarray(indices), mappings
        self.weights, self.size, self.batch, self.shuffle = weights, size, batch, shuffle
        self.on_epoch_end()

    def __len__(self):
        return int(np.ceil(len(self.indices) / self.batch))

    def on_epoch_end(self):
        if self.shuffle:
            np.random.shuffle(self.indices)

    def __getitem__(self, index):
        selected = self.indices[index * self.batch:(index + 1) * self.batch]
        images, labels = [], {key: [] for key in self.mappings}
        sample_weights = {key: [] for key in self.mappings}
        for row_index in selected:
            row = self.data[int(row_index)]
            image = row["image"].convert("RGB").resize((self.size, self.size))
            images.append(np.asarray(image, dtype=np.float32))
            for key, mapping in self.mappings.items():
                value = normalized(row, key)
                label = mapping.get(value, mapping.get("other", 0))
                labels[key].append(label)
                sample_weights[key].append(self.weights[key].get(label, 1.0))
        return np.asarray(images), {k: np.asarray(v) for k, v in labels.items()}, {k: np.asarray(v, dtype=np.float32) for k, v in sample_weights.items()}


def make_mapping(data, indices, key, minimum):
    values_for_key = data[key]
    counts = Counter(normalize_value(values_for_key[int(i)], key) for i in indices)
    values = sorted(value for value, count in counts.items() if count >= minimum)
    if len(values) < len(counts):
        values.append("other")
    return {value: index for index, value in enumerate(values)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--allow-cpu", action="store_true", help="Explicitly permit slow CPU training.")
    parser.add_argument("--epochs", type=int)
    parser.add_argument("--batch-size", type=int)
    parser.add_argument("--backbone", choices=("b0", "b2"))
    parser.add_argument("--max-train-samples", type=int, help="Reproducible smoke-test cap; omit for full training.")
    parser.add_argument("--max-test-samples", type=int, help="Reproducible evaluation cap for smoke tests only.")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    if args.epochs:
        config["epochs"] = args.epochs
    if args.batch_size:
        config["batch_size"] = args.batch_size
    if args.backbone:
        config["backbone"] = args.backbone
    random.seed(config["seed"]); np.random.seed(config["seed"]); tf.random.set_seed(config["seed"])
    gpus = tf.config.list_physical_devices("GPU")
    if not gpus and not args.allow_cpu:
        raise SystemExit("No TensorFlow GPU detected. Refusing accidental CPU training; use --allow-cpu only intentionally.")
    if gpus:
        tf.keras.mixed_precision.set_global_policy("mixed_float16")

    train_files = sorted(str(path) for path in RAW.glob("train-*.parquet"))
    test_files = sorted(str(path) for path in RAW.glob("test-*.parquet"))
    if not train_files or not test_files:
        raise SystemExit("Dataset files are missing. Run ml/data/download_dataset.py first.")
    data = load_dataset("parquet", data_files={"train": train_files, "test": test_files}, cache_dir=str(CACHE))
    train_metadata = data["train"].remove_columns("image").to_pandas()
    test_metadata = data["test"].remove_columns("image").to_pandas()
    indices = np.arange(len(data["train"]))
    usage_values = train_metadata["usage"]
    stratify = [normalize_value(usage_values[int(i)], "usage") for i in indices]
    train_idx, val_idx = train_test_split(indices, test_size=config["validation_fraction"], random_state=config["seed"], stratify=stratify)
    mapping_indices = train_idx.copy()

    mappings = {key: make_mapping(train_metadata, mapping_indices, key, config["minimum_class_count"]) for key in config["heads"]}
    weights = {}
    for key, mapping in mappings.items():
        values_for_key = train_metadata[key]
        encoded = [mapping.get(normalize_value(values_for_key[int(i)], key), mapping.get("other", 0)) for i in mapping_indices]
        counts = Counter(encoded); total = len(encoded); classes = len(mapping)
        weights[key] = {label: total / (classes * count) for label, count in counts.items()}

    if args.max_train_samples:
        rng = np.random.default_rng(config["seed"])
        train_idx = rng.choice(train_idx, min(args.max_train_samples, len(train_idx)), replace=False)
        val_idx = rng.choice(val_idx, min(max(32, args.max_train_samples // 5), len(val_idx)), replace=False)

    train_batches = Batches(data["train"], train_idx, mappings, weights, config["image_size"], config["batch_size"], True)
    val_batches = Batches(data["train"], val_idx, mappings, weights, config["image_size"], config["batch_size"], False)
    backbone_class = tf.keras.applications.EfficientNetB0 if config["backbone"] == "b0" else tf.keras.applications.EfficientNetB2
    backbone = backbone_class(include_top=False, weights="imagenet", input_shape=(config["image_size"], config["image_size"], 3))
    backbone.trainable = False
    inputs = tf.keras.Input((config["image_size"], config["image_size"], 3), name="image")
    x = tf.keras.layers.RandomFlip("horizontal")(inputs)
    x = tf.keras.layers.RandomRotation(0.04)(x)
    x = tf.keras.layers.RandomZoom(0.08)(x)
    x = tf.keras.layers.RandomContrast(0.10)(x)
    x = backbone(x, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dropout(0.25)(x)
    outputs = {key: tf.keras.layers.Dense(len(mapping), activation="softmax", dtype="float32", name=key)(x) for key, mapping in mappings.items()}
    model = tf.keras.Model(inputs, outputs)
    model.compile(optimizer=tf.keras.optimizers.Adam(config["learning_rate"]), loss={key: "sparse_categorical_crossentropy" for key in mappings}, metrics={key: ["accuracy"] for key in mappings})
    output_dir = OUT / config["backbone"]
    output_dir.mkdir(parents=True, exist_ok=True)
    callbacks = [
        tf.keras.callbacks.ModelCheckpoint(output_dir / "best_model.keras", monitor="val_loss", save_best_only=True),
        tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=3, restore_best_weights=True),
        tf.keras.callbacks.CSVLogger(output_dir / "training_history.csv"),
    ]
    history = model.fit(train_batches, validation_data=val_batches, epochs=config["epochs"], callbacks=callbacks)
    model.save(output_dir / "last_model.keras")

    test_indices = np.arange(len(data["test"]))
    if args.max_test_samples:
        rng = np.random.default_rng(config["seed"])
        test_indices = rng.choice(test_indices, min(args.max_test_samples, len(test_indices)), replace=False)
    test_batches = Batches(data["test"], test_indices, mappings, weights, config["image_size"], config["batch_size"], False)
    predictions = model.predict(test_batches)
    reports = {}
    for key, mapping in mappings.items():
        reverse = {index: label for label, index in mapping.items()}
        values_for_key = test_metadata[key]
        truth = [mapping.get(normalize_value(values_for_key[int(i)], key), mapping.get("other", 0)) for i in test_indices]
        predicted = np.argmax(predictions[key], axis=1)[:len(truth)]
        reports[key] = classification_report(truth, predicted, labels=list(reverse), target_names=[reverse[i] for i in reverse], output_dict=True, zero_division=0)
    metadata = {"trained_at": datetime.now(timezone.utc).isoformat(), "device": "GPU" if gpus else "CPU", "backbone": f"efficientnet_{config['backbone']}", "dataset_revision": config["dataset_revision"], "train_rows": len(train_idx), "validation_rows": len(val_idx), "test_rows": len(test_indices), "mappings": mappings, "metrics": reports, "history": history.history, "split_strategy": "official test split plus seeded stratified validation split; dataset has no item identifier"}
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    (output_dir / "label_mapping.json").write_text(json.dumps(mappings, indent=2), encoding="utf-8")
    (output_dir / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
