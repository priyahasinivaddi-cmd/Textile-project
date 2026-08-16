"""Create immutable local experiment records from trained artifacts."""
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; RECORDS = ROOT / "ml/experiments/records"


def main():
    paths = list((ROOT / "ml/artifacts").glob("**/metadata.json")); RECORDS.mkdir(parents=True, exist_ok=True)
    for path in paths:
        metadata = json.loads(path.read_text(encoding="utf-8")); identity = hashlib.sha256(f"{path}:{metadata.get('trained_at')}".encode()).hexdigest()[:16]
        record = {"experiment_id": identity, "model": path.parent.name, "dataset_version": metadata.get("dataset_revision", "fnauman/fashion-second-hand-front-only-rgb"), "parameters": metadata.get("config", {}), "metrics": metadata.get("metrics", {}), "timestamp": metadata.get("trained_at") or datetime.now(timezone.utc).isoformat(), "checkpoint": str(path.parent), "device": metadata.get("device", "CPU")}
        (RECORDS / f"{identity}.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(f"registered {len(paths)} experiment(s)")


if __name__ == "__main__": main()
