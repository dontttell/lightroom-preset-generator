"""AI Provider 基类与异常。"""

from __future__ import annotations

import abc
from typing import Protocol

from ai.schema import StyleAnalysisResult


class AiNotConfiguredError(Exception):
    """API 未配置。"""


class AiAnalysisError(Exception):
    """AI 分析失败。"""


class AiStyleAnalyzer(Protocol):
    def analyze(self, image_path: str) -> StyleAnalysisResult: ...


class BaseAiProvider(abc.ABC):
    @abc.abstractmethod
    def analyze(self, image_path: str) -> StyleAnalysisResult:
        pass

    @abc.abstractmethod
    def test_connection(self) -> str:
        """返回成功消息或抛出异常。"""
