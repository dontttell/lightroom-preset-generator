"""
OpenAI-compatible provider（向后兼容导入路径）。

实际实现见 openai_compatible_provider.py。
本模块名指「OpenAI Chat Completions 兼容协议」，非绑定 OpenAI 官方服务。
用户通过 Base URL + Key + 模型配置任意兼容服务商（如智谱 OpenAI 兼容端点）。
"""

from ai.openai_compatible_provider import OpenAiCompatibleProvider, _encode_image
from ai.response_parser import parse_json_content

__all__ = ["OpenAiCompatibleProvider", "_encode_image", "parse_json_content"]
