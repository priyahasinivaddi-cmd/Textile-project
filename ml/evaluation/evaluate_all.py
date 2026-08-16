"""Consolidate measured model metrics without manufacturing results."""
import json
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]


def main():
    models = {}
    sources = {"efficientnet_b0": ROOT / "ml/artifacts/multitask/b0/metadata.json", "efficientnet_b2": ROOT / "ml/artifacts/multitask/b2/metadata.json", "destination": ROOT / "ml/artifacts/destination/metadata.json"}
    for name, path in sources.items():
        if path.exists():
            metadata = json.loads(path.read_text(encoding="utf-8")); models[name] = {"trained_at": metadata.get("trained_at"), "metrics": metadata.get("metrics", {}), "quality_gate_passed": metadata.get("quality_gate_passed", False), "artifact": str(path.parent)}
    output = ROOT / "ml/evaluation/evaluation_summary.json"; output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"evaluated_at": datetime.now(timezone.utc).isoformat(), "models": models, "note": "Only persisted evaluation-run metrics are included."}, indent=2), encoding="utf-8"); print(output)


if __name__ == "__main__": main()
