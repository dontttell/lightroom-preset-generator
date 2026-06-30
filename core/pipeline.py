"""
分析流水线
----------
协调图像加载、各独立分析器执行、结果汇总。
单个模块失败不会中断整体流程。
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional

import cv2
import numpy as np

from analyzers import EXPANDERS, build_analyzers
from analyzers.base import BaseAnalyzer, ImageContext
from config.settings import SETTINGS
from core.inference_result import AnalysisReport, ParameterResult, ParameterStatus


class AnalysisPipeline:
    """图像 → 参数推测 的主流程。"""

    def __init__(self, enabled_modules: Optional[Dict[str, bool]] = None):
        self.enabled_modules = enabled_modules or SETTINGS.enabled_modules.copy()
        self._analyzers: List[BaseAnalyzer] = build_analyzers(self.enabled_modules)

    def reload_analyzers(self) -> None:
        """配置变更后重新加载分析器列表。"""
        self._analyzers = build_analyzers(self.enabled_modules)

    def analyze_file(self, image_path: str) -> AnalysisReport:
        bgr = cv2.imread(image_path, cv2.IMREAD_COLOR)
        if bgr is None:
            raise ValueError(f"无法读取图像: {image_path}")
        return self.analyze_array(bgr, image_path)

    def analyze_array(self, bgr: np.ndarray, image_path: str = "") -> AnalysisReport:
        t0 = time.perf_counter()
        ctx = ImageContext(bgr, max_size=SETTINGS.analysis_max_size)

        results: List[ParameterResult] = []

        # 对已禁用的模块插入 MISSING 占位（便于 GUI 统一展示）
        from analyzers import ANALYZER_REGISTRY

        for cls in ANALYZER_REGISTRY:
            if not self.enabled_modules.get(cls.module_id, True):
                inst = cls()
                results.append(inst._missing(cls.module_id, inst.display_name))

        for analyzer in self._analyzers:
            try:
                result = analyzer.analyze(ctx)
            except Exception as exc:
                result = analyzer._failed(
                    getattr(analyzer, "module_id", "unknown"),
                    analyzer.display_name,
                    str(exc),
                )
            results.append(result)

        elapsed_ms = (time.perf_counter() - t0) * 1000
        return AnalysisReport(
            image_path=image_path,
            parameters=results,
            analysis_ms=elapsed_ms,
            image_stats=ctx.stats,
        )

    @staticmethod
    def flatten_for_xmp(report: AnalysisReport) -> List[ParameterResult]:
        """展开复合参数，供 XMP 生成器使用。"""
        flat: List[ParameterResult] = []
        for param in report.parameters:
            expander = EXPANDERS.get(param.key)
            if expander and param.is_available:
                flat.extend(expander(param))
            else:
                flat.append(param)
        return flat
