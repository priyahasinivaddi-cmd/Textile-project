"""Parse verified care-label composition text into material evidence."""

from __future__ import annotations

import re


ALIASES = {
    "cotton": "Cotton",
    "polyester": "Polyester",
    "wool": "Wool",
    "silk": "Silk",
    "linen": "Linen",
    "flax": "Linen",
    "nylon": "Nylon",
    "polyamide": "Nylon",
    "rayon": "Rayon",
    "viscose": "Rayon",
    "acrylic": "Acrylic",
    "elastane": "Elastane",
    "spandex": "Elastane",
}


def parse_label_composition(text: str | None) -> dict | None:
    value = (text or "").strip()
    if not value:
        return None

    matches = re.findall(r"(\d+(?:\.\d+)?)\s*%\s*([A-Za-z][A-Za-z /_-]*)", value)
    composition: dict[str, float] = {}
    unsupported: list[str] = []
    for raw_percentage, raw_name in matches:
        token = re.split(r"[/,_-]|\band\b", raw_name, maxsplit=1, flags=re.IGNORECASE)[0]
        token = token.strip().lower()
        name = next((display for alias, display in ALIASES.items() if alias in token), None)
        if name is None:
            unsupported.append(token)
            continue
        composition[name] = composition.get(name, 0.0) + float(raw_percentage)

    if not composition:
        raise ValueError("Enter composition like '80% Cotton, 20% Polyester'.")
    if unsupported:
        raise ValueError(f"Unsupported fibre name: {unsupported[0]}")
    total = sum(composition.values())
    if not 95.0 <= total <= 105.0:
        raise ValueError(f"Care-label percentages must total about 100% (received {total:g}%).")

    normalized = {name: percentage * 100.0 / total for name, percentage in composition.items()}
    ordered = sorted(normalized.items(), key=lambda item: item[1], reverse=True)
    meaningful = [(name, percentage) for name, percentage in ordered if percentage >= 5.0]
    mixed = len(meaningful) > 1
    return {
        "fabric_type": "Mixed Fabrics" if mixed else ordered[0][0],
        "confidence": 1.0,
        "fiber_composition": " / ".join(f"{percentage:.1f}% {name}" for name, percentage in ordered),
        "blend_type": "mixed" if mixed else "single",
        "evidence_source": "care_label",
    }
