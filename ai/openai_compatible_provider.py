"""OpenAI-compatible Chat Completions Vision API adapter."""

from __future__ import annotations

import base64
import json
import time
from pathlib import Path
from typing import Callable

import httpx

from ai.base import AiAnalysisError, BaseAiProvider
from ai.capabilities import OPENAI_COMPATIBLE
from ai.http_errors import format_api_http_error
from ai.response_parser import parse_json_content
from ai.schema import StyleAnalysisResult
from ai.style_classify import parse_classify_response
from ai.style_recipes import (
    ClassifyResult,
    match_recipe,
    merge_recipe_with_refine,
    recipe_context_for_prompt,
)
from ai.style_refine import parse_refine_response
from ai.validator import normalize_style_analysis
from config.ai_config import AiConfig
from config.provider_presets import resolve_openai_chat_url

ROOT = Path(__file__).resolve().parent.parent


class OpenAiCompatibleProvider(BaseAiProvider):
    """
    任意 OpenAI 兼容 Vision API 的 HTTP 客户端。

    文件名历史原因见 openai_provider.py；实际绑定的是协议形态，非 OpenAI 独家。
    """

    capabilities = OPENAI_COMPATIBLE

    def __init__(self, cfg: AiConfig):
        self.cfg = cfg

    def analyze(self, image_path: str) -> StyleAnalysisResult:
        url_warn = self._base_url_protocol_warning()
        if url_warn:
            raise AiAnalysisError(url_warn)
        if self.cfg.use_recipe_pipeline:
            return self.analyze_recipe_pipeline(image_path)
        return self.analyze_legacy(image_path)

    def analyze_legacy(self, image_path: str) -> StyleAnalysisResult:
        settings = self.cfg.analysis_settings()
        prompt = self._load_prompt(self.cfg.resolved_prompt_path())
        user_text = self.cfg.user_message_text()
        return self._run_json_pipeline(
            image_path=image_path,
            system_prompt=prompt,
            user_text=user_text,
            settings=settings,
            retry_hint="Return ONLY a JSON object matching style_analysis.v1.1. No markdown.",
            normalize=lambda parsed: normalize_style_analysis(parsed, self.cfg),
        )

    def analyze_recipe_pipeline(self, image_path: str) -> StyleAnalysisResult:
        settings = self.cfg.analysis_settings()
        image_b64, mime = _encode_image(image_path)

        classify_prompt = self._load_prompt(self.cfg.resolved_classify_prompt_path())
        classify_user = self.cfg.classify_user_message_text()
        classify_raw = self._call_json_with_retries(
            image_b64=image_b64,
            mime=mime,
            system_prompt=classify_prompt,
            user_text=classify_user,
            settings=settings,
            retry_hint="Return ONLY style_classify.v1 JSON. No LR slider values. No markdown.",
            parse=parse_classify_response,
            max_tokens=800,
        )
        assert isinstance(classify_raw, ClassifyResult)
        classify = classify_raw

        recipe = match_recipe(classify)
        context = {
            "classify": {
                "category": classify.category,
                "subtype": classify.subtype,
                "light": classify.light,
                "pre_graded": classify.pre_graded,
                "local_mask_likely": classify.local_mask_likely,
                "scene_keywords": classify.scene_keywords,
                "style_hints": classify.style_hints,
                "subtype_confidence": classify.subtype_confidence,
            },
            "recipe": recipe_context_for_prompt(recipe),
        }
        context_json = json.dumps(context, ensure_ascii=False, indent=2)

        refine_prompt = self._load_prompt(self.cfg.resolved_refine_prompt_path())
        refine_user = self.cfg.refine_user_message_text(context_json)
        refine_parsed = self._call_json_with_retries(
            image_b64=image_b64,
            mime=mime,
            system_prompt=refine_prompt,
            user_text=refine_user,
            settings=settings,
            retry_hint=(
                "Return refine JSON with parameter_adjustments (delta only). "
                "Do not output full parameters absolute values. No markdown."
            ),
            parse=parse_refine_response,
            max_tokens=2000,
        )

        merged = merge_recipe_with_refine(
            recipe,
            refine_parsed,
            pre_graded=classify.pre_graded,
            subtype_confidence=classify.subtype_confidence,
        )
        meta = merged.pop("_meta", {})
        meta["pipeline"] = "recipe"
        meta["classify"] = context["classify"]

        result, _, warnings = normalize_style_analysis(merged, self.cfg)
        result.raw["_recipe_pipeline"] = meta
        if warnings:
            result.raw["_normalize_warnings"] = warnings
        return result

    def _run_json_pipeline(
        self,
        *,
        image_path: str,
        system_prompt: str,
        user_text: str,
        settings,
        retry_hint: str,
        normalize: Callable[[dict], tuple],
    ) -> StyleAnalysisResult:
        image_b64, mime = _encode_image(image_path)
        last_error: Exception | None = None
        attempts = max(1, settings.max_retries + 1)

        for attempt in range(attempts):
            extra_user = user_text
            if attempt > 0:
                extra_user += f"\n\nYour previous response was invalid. {retry_hint}"
            try:
                content = self._request_completion(
                    system_prompt,
                    extra_user,
                    image_b64,
                    mime,
                    settings.use_json_mode,
                )
                parsed = parse_json_content(content)
                result, _, warnings = normalize(parsed)
                if warnings and attempt == attempts - 1:
                    result.raw["_normalize_warnings"] = warnings
                return result
            except (AiAnalysisError, ValueError) as exc:
                last_error = exc
                if attempt < attempts - 1:
                    time.sleep(0.8 * (attempt + 1))
                    continue
                raise AiAnalysisError(str(exc)) from exc

        raise AiAnalysisError(str(last_error or "AI 分析失败"))

    def _call_json_with_retries(
        self,
        *,
        image_b64: str,
        mime: str,
        system_prompt: str,
        user_text: str,
        settings,
        retry_hint: str,
        parse: Callable[[dict], object],
        max_tokens: int = 2000,
    ) -> object:
        last_error: Exception | None = None
        attempts = max(1, settings.max_retries + 1)

        for attempt in range(attempts):
            extra_user = user_text
            if attempt > 0:
                extra_user += f"\n\nYour previous response was invalid. {retry_hint}"
            try:
                content = self._request_completion(
                    system_prompt,
                    extra_user,
                    image_b64,
                    mime,
                    settings.use_json_mode,
                    max_tokens=max_tokens,
                )
                parsed = parse_json_content(content)
                return parse(parsed)
            except (AiAnalysisError, ValueError) as exc:
                last_error = exc
                if attempt < attempts - 1:
                    time.sleep(0.8 * (attempt + 1))
                    continue
                raise AiAnalysisError(str(exc)) from exc

        raise AiAnalysisError(str(last_error or "AI 分析失败"))

    def test_connection(self) -> str:
        url_warn = self._base_url_protocol_warning()
        if url_warn:
            raise AiAnalysisError(url_warn)

        try:
            self._request_completion(
                "You are a connectivity test.",
                "Reply with OK only.",
                "",
                "image/jpeg",
                use_json_mode=False,
                include_image=False,
            )
            mode = "recipe pipeline" if self.cfg.use_recipe_pipeline else "legacy"
            return f"连接成功（{self.capabilities.name} / {self.cfg.model} / {mode}）"
        except AiAnalysisError:
            raise
        except Exception as exc:
            raise AiAnalysisError(f"连接测试失败: {exc}") from exc

    def _base_url_protocol_warning(self) -> str:
        from config.provider_presets import openai_compatible_base_url_warning

        return openai_compatible_base_url_warning(self.cfg.resolved_base_url()) or ""

    def _request_completion(
        self,
        system_prompt: str,
        user_text: str,
        image_b64: str,
        mime: str,
        use_json_mode: bool,
        *,
        include_image: bool = True,
        max_tokens: int = 2000,
    ) -> str:
        user_content: list | str
        if include_image and image_b64:
            user_content = [
                {"type": "text", "text": user_text},
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{image_b64}"}},
            ]
        else:
            user_content = user_text

        payload: dict = {
            "model": self.cfg.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "max_tokens": max_tokens,
        }
        if use_json_mode:
            payload["response_format"] = {"type": "json_object"}

        url = resolve_openai_chat_url(
            self.cfg.resolved_base_url(),
            self.capabilities.chat_completions_path,
        )
        headers = {
            "Authorization": f"Bearer {self.cfg.resolved_api_key()}",
            "Content-Type": "application/json",
        }
        try:
            with httpx.Client(timeout=120.0) as client:
                resp = client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as exc:
            raise AiAnalysisError(
                format_api_http_error(
                    exc,
                    preset_id=self.cfg.resolved_provider_preset(),
                    model=self.cfg.model,
                    base_url=self.cfg.resolved_base_url(),
                )
            ) from exc
        except httpx.HTTPError as exc:
            raise AiAnalysisError(f"API 请求失败: {exc}") from exc

        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AiAnalysisError(f"API 响应格式异常: {repr(data)[:300]}") from exc

    def _load_prompt(self, rel: str) -> str:
        path = Path(rel)
        if not path.is_absolute():
            path = ROOT / rel
        if path.is_file():
            return path.read_text(encoding="utf-8")
        return "Analyze photo color grading. Output JSON only."


def _encode_image(image_path: str) -> tuple[str, str]:
    path = Path(image_path)
    suffix = path.suffix.lower()
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}.get(
        suffix, "image/jpeg"
    )
    data = path.read_bytes()
    return base64.b64encode(data).decode("ascii"), mime
