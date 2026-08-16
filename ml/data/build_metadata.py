"""Build the canonical combined metadata table used by downstream training."""
import json

import pandas as pd

from common import PROCESSED, REPORTS


def main():
    frames = []
    for split in ("train", "test"):
        path = PROCESSED / f"{split}_metadata.parquet"
        if not path.exists():
            raise SystemExit("Run clean_dataset.py first")
        frames.append(pd.read_parquet(path))
    combined = pd.concat(frames, ignore_index=True)
    output = PROCESSED / "metadata.parquet"
    combined.to_parquet(output, index=False)
    manifest = {"rows": len(combined), "columns": list(combined.columns), "source_splits": combined["split"].value_counts().to_dict()}
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "metadata_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
