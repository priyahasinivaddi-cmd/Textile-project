"""Print the top three production-model predictions for one image."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError
import tensorflow as tf


SCRIPT_DIR = Path(__file__).resolve().parent
IMAGE_SIZE = (224, 224)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=SCRIPT_DIR / "best_fabric_model.keras")
    parser.add_argument("--classes", type=Path, default=SCRIPT_DIR / "class_names.json")
    parser.add_argument("--actual", help="Optional actual class name for correctness reporting.")
    parser.add_argument("--split-report", type=Path, default=SCRIPT_DIR / "dataset_split_report.csv")
    return parser.parse_args()


def preprocess(path: Path):
    try:
        with Image.open(path) as image:
            image = ImageOps.exif_transpose(image).convert("RGB").resize(IMAGE_SIZE, Image.Resampling.BILINEAR)
            pixels = np.asarray(image, dtype=np.float32)
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise SystemExit(f"Invalid image: {exc}") from exc
    return np.expand_dims(tf.keras.applications.mobilenet_v2.preprocess_input(pixels), axis=0)


def main():
    args = parse_args()
    class_names = json.loads(args.classes.read_text(encoding="utf-8"))
    model = tf.keras.models.load_model(args.model, compile=False)
    probabilities = np.asarray(model.predict(preprocess(args.image), verbose=0)).reshape(-1)
    if len(probabilities) != len(class_names):
        raise SystemExit("Model output count does not match class_names.json")
    probabilities = np.maximum(probabilities, 0)
    probabilities /= probabilities.sum()
    actual = args.actual
    if actual is None and args.split_report.is_file():
        resolved_image = str(args.image.resolve()).lower()
        with args.split_report.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                try:
                    if str(Path(row["image_path"]).resolve()).lower() == resolved_image:
                        index = int(row["dominant_class_index"])
                        if 0 <= index < len(class_names):
                            actual = class_names[index]
                        break
                except (KeyError, TypeError, ValueError):
                    continue
    predicted_index = int(np.argmax(probabilities))
    print(f"Image: {args.image.resolve()}")
    print(f"Actual label: {actual.replace('_', ' ').title() if actual else 'unknown'}")
    print(f"Predicted label: {class_names[predicted_index].replace('_', ' ').title()}")
    print(f"Confidence: {probabilities[predicted_index] * 100:.2f}%")
    print(f"Correct: {class_names[predicted_index].lower() == actual.lower() if actual else 'unknown'}")
    print("Top three predictions:")
    for rank, index in enumerate(np.argsort(probabilities)[::-1][:3], start=1):
        print(f"{rank}. {class_names[index].replace('_', ' ').title()}: {probabilities[index] * 100:.2f}%")


if __name__ == "__main__":
    main()
