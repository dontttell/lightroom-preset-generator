"""
推测结果数据模型
----------------
每个参数模块返回统一的 ParameterResult，便于 GUI 展示与 XMP 生成。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ParameterStatus(str, Enum):
    """参数推测状态。"""

    OK = "ok"  # 成功推测或精确提取
    MISSING = "missing"  # 模块被禁用或未运行
    FAILED = "failed"  # 运行出错
    SKIPPED = "skipped"  # 数据不足，主动跳过
    INFERRED = "inferred"  # AI 参考推测


class AnalysisMode(str, Enum):
    """分析路径。"""

    PRECISE = "precise"  # metadata 精确提取
    AI_LEARNING = "ai_learning"  # AI 辅助学习
    PENDING = "pending"  # 已打开图片，尚未完成分析


@dataclass
class AiLearningReport:
    """AI 风格分析结果（路径 B）。"""

    overall_impression: str = ""
    editing_steps: List[Dict[str, Any]] = field(default_factory=list)
    priority_adjustments: List[str] = field(default_factory=list)
    parameters: List[ParameterResult] = field(default_factory=list)
    analysis_ms: float = 0.0
    raw_json: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ImageSession:
    """一次图片会话的完整状态。"""

    image_path: str
    mode: AnalysisMode = AnalysisMode.PENDING
    metadata_message: str = ""
    parameters: List[ParameterResult] = field(default_factory=list)
    parameter_groups: List[tuple] = field(default_factory=list)  # (name, [ParameterResult])
    ai_report: Optional[AiLearningReport] = None
    scan_ms: float = 0.0
    lut_cube: Any = None  # numpy ndarray，AI 分析后生成


@dataclass
class ParameterResult:
    """
    单个 Lightroom 参数的推测结果。

    Attributes:
        key: XMP 字段名（不含 crs: 前缀），如 Exposure
        display_name: GUI 显示名称
        value: 推测值（int/float/str/list），失败时为 None
        status: 推测状态
        confidence: 0~1 置信度（启发式，非 ML 概率）
        message: 给用户/Debug 的说明
        raw_stats: 分析阶段原始统计量，便于 debug
    """

    key: str
    display_name: str
    value: Any = None
    status: ParameterStatus = ParameterStatus.MISSING
    confidence: float = 0.0
    message: str = ""
    raw_stats: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_available(self) -> bool:
        return self.status in (ParameterStatus.OK, ParameterStatus.INFERRED) and self.value is not None

    def to_display_line(self) -> str:
        if self.is_available:
            tag = "精确" if self.confidence >= 1.0 else f"推测 {self.confidence:.0%}"
            return f"{self.display_name}: {self.value}  ({tag})"
        hint = self.message or "未推测"
        return f"{self.display_name}: [缺失] {hint}"


@dataclass
class AnalysisReport:
    """一次完整分析的汇总。"""

    image_path: str
    parameters: List[ParameterResult] = field(default_factory=list)
    analysis_ms: float = 0.0
    image_stats: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str) -> Optional[ParameterResult]:
        for p in self.parameters:
            if p.key == key:
                return p
        return None

    def available_params(self) -> Dict[str, Any]:
        return {p.key: p.value for p in self.parameters if p.is_available}

    def missing_params(self) -> List[ParameterResult]:
        return [p for p in self.parameters if not p.is_available]
