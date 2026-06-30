"""后台任务线程。"""

from __future__ import annotations

import time

from PyQt6.QtCore import QThread, pyqtSignal

from ai.base import AiNotConfiguredError, AiAnalysisError
from ai.factory import create_analyzer
from ai.service import build_lut_for_report, style_result_to_report
from config.ai_config import load_ai_config
from core.inference_result import ImageSession, AnalysisMode
from core.metadata_detector import scan_image_metadata
from core.metadata_parser import crs_fields_to_parameters, group_parameters


class MetadataWorker(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, image_path: str):
        super().__init__()
        self.image_path = image_path

    def run(self) -> None:
        try:
            t0 = time.perf_counter()
            scan = scan_image_metadata(self.image_path)
            ms = (time.perf_counter() - t0) * 1000
            session = ImageSession(image_path=self.image_path, scan_ms=ms, metadata_message=scan.message)
            if scan.has_lightroom_metadata:
                params = crs_fields_to_parameters(scan.crs_fields)
                session.mode = AnalysisMode.PRECISE
                session.parameters = params
                session.parameter_groups = group_parameters(params)
            else:
                session.mode = AnalysisMode.AI_LEARNING
            self.finished.emit(session)
        except Exception as exc:
            self.error.emit(str(exc))


class AiAnalysisWorker(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, image_path: str):
        super().__init__()
        self.image_path = image_path

    def run(self) -> None:
        try:
            cfg = load_ai_config()
            if not cfg.is_ready():
                raise AiNotConfiguredError("AI 服务未配置")
            analyzer = create_analyzer(cfg)
            t0 = time.perf_counter()
            style = analyzer.analyze(self.image_path)
            ms = (time.perf_counter() - t0) * 1000
            report = style_result_to_report(style, ms)
            lut = build_lut_for_report(report)
            session = ImageSession(
                image_path=self.image_path,
                mode=AnalysisMode.AI_LEARNING,
                metadata_message="AI 参考分析",
                parameters=report.parameters,
                parameter_groups=group_parameters(report.parameters),
                ai_report=report,
                scan_ms=ms,
                lut_cube=lut,
            )
            self.finished.emit(session)
        except (AiNotConfiguredError, AiAnalysisError) as exc:
            self.error.emit(str(exc))
        except Exception as exc:
            self.error.emit(f"AI 分析失败: {exc}")
