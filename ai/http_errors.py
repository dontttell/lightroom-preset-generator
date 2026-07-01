"""将 httpx HTTP 错误格式化为用户可读的 AI 分析失败信息。"""

from __future__ import annotations

import httpx

from config.provider_presets import openai_compatible_base_url_warning, volcengine_model_format_warning


def format_api_http_error(
    exc: httpx.HTTPStatusError,
    *,
    preset_id: str = "",
    model: str = "",
    base_url: str = "",
) -> str:
    parts = [f"API 请求失败: {exc}"]
    try:
        body = (exc.response.text or "").strip()
        if body:
            parts.append(f"服务端返回: {body[:600]}")
    except Exception:
        pass

    url_warn = openai_compatible_base_url_warning(base_url)
    if url_warn:
        parts.append(url_warn)

    if preset_id in ("volcengine", "custom") or "volces.com" in base_url.lower():
        model_warn = volcengine_model_format_warning(model)
        if model_warn:
            parts.append(model_warn)
        if exc.response.status_code == 404 and not url_warn:
            parts.append(
                "404 常见原因：Base URL 误填为 /api/compatible（Anthropic 协议）、"
                "Model ID 不正确、模型未开通，或 API Key 未勾选 Chat API 权限。"
            )

    return "\n\n".join(parts)
