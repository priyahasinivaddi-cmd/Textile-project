"""Send a local textile image to the running composition prediction API."""

import argparse
import json
from pathlib import Path

import requests


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path, help="Path to a PNG, JPG, or JPEG image")
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8000/api/model/predict-composition",
    )
    args = parser.parse_args()

    if not args.image.is_file():
        parser.error(f"Image does not exist: {args.image}")

    suffix_to_type = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
    content_type = suffix_to_type.get(args.image.suffix.lower())
    if content_type is None:
        parser.error("Image must use a .png, .jpg, or .jpeg extension")

    with args.image.open("rb") as image_file:
        response = requests.post(
            args.url,
            files={"file": (args.image.name, image_file, content_type)},
            timeout=120,
        )
    print(f"HTTP {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except requests.JSONDecodeError:
        print(response.text)
    response.raise_for_status()


if __name__ == "__main__":
    main()
