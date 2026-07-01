"""离线校验 AI schema 与归一化逻辑（无需 API）。"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.ai_config import AiConfig  # noqa: E402
from ai.validator import normalize_style_analysis  # noqa: E402


SAMPLE = {
    "overall_impression": "偏暖、略降对比",
    "editing_steps": [{"step": 1, "title": "白平衡", "description": "整体偏暖"}],
    "priority_adjustments": ["Temperature"],
    "parameters": {
        "Exposure2012": {"value": 0.4, "confidence": 0.7},
        "Contrast2012": {"value": -15, "confidence": 0.6},
        "Temperature": {"value": 6200, "confidence": 0.8},
        "Tint": {"value": 5, "confidence": 0.75},
        "Saturation": {"value": 10, "confidence": 0.55},
        "UnknownKey": {"value": 1, "confidence": 0.9},
        "Highlights2012": {"value": 999, "confidence": 0.2},
    },
}


def main() -> int:
    cfg = AiConfig()
    result, params, warnings = normalize_style_analysis(SAMPLE, cfg)
    checks = [
        ("schema version in raw", result.raw.get("_schema_version") == "style_analysis.v1.1"),
        ("unknown key dropped", "UnknownKey" not in result.parameters),
        ("highlights clamped", result.parameters["Highlights2012"]["value"] == 100),
        ("low conf skips lut", not result.parameters["Highlights2012"]["include_in_lut"]),
        ("low conf skips xmp", not result.parameters["Highlights2012"]["include_in_xmp"],
        ),
        ("temperature in lut", result.parameters["Temperature"]["include_in_lut"]),
        ("param count", len(params) == 6),
    ]
    ok = True
    for name, passed in checks:
        status = "OK" if passed else "FAIL"
        print(f"  [{status}] {name}")
        ok = ok and passed
    print(f"  warnings: {len(warnings)}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
