"""Download the pinned CC BY 4.0 dataset snapshot reproducibly."""
import argparse
from pathlib import Path
from huggingface_hub import snapshot_download

DATASET = "fnauman/fashion-second-hand-front-only-rgb"
REVISION = "b2559ac0157ea9b6913a65062877f487952e690b"
DEFAULT_DIR = Path(__file__).resolve().parent / "raw" / "fashion-second-hand-front-only-rgb"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_DIR)
    args = parser.parse_args()
    location = snapshot_download(DATASET, repo_type="dataset", revision=REVISION, local_dir=args.output)
    print(location)


if __name__ == "__main__":
    main()
