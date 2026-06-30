"""AI 分析结果 schema。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class StyleAnalysisResult:
    overall_impression: str = ""
    editing_steps: List[Dict[str, Any]] = field(default_factory=list)
    priority_adjustments: List[str] = field(default_factory=list)
    parameters: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    raw: Dict[str, Any] = field(default_factory=dict)
