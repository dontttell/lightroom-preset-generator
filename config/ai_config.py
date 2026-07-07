"""
AI 配置读写
-----------
默认全部留空；未配置时 is_ready() 为 False，程序其余功能正常运行。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

from config.provider_presets import get_preset, infer_preset_id

ROOT = Path(__file__).resolve().parent.parent
LOCAL_CONFIG = ROOT / "config" / "ai_config.local.yaml"
EXAMPLE_CONFIG = ROOT / "config" / "ai_config.example.yaml"
DEFAULT_PROMPT_ZH = "config/prompts/style_analysis.txt"
DEFAULT_PROMPT_EN = "config/prompts/style_analysis.en.txt"
DEFAULT_CLASSIFY_PROMPT = "config/prompts/style_classify.txt"
DEFAULT_REFINE_PROMPT = "config/prompts/style_analysis_refine.txt"


@dataclass
class AnalysisSettings:
    """AI 分析行为（prompt、校验阈值、重试）。"""

    language: str = "zh-CN"
    prompt_file: str = ""
    lut_min_confidence: float = 0.35
    xmp_min_confidence: float = 0.25
    use_json_mode: bool = True
    max_retries: int = 2


@dataclass
class AiConfig:
    provider: str = ""
    provider_preset: str = ""
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    language: str = "zh-CN"
    prompt_file: str = ""

    # 高级项（可由 yaml 覆盖；部分在设置页暴露）
    lut_min_confidence: float = 0.35
    xmp_min_confidence: float = 0.25
    use_json_mode: bool = True
    max_retries: int = 2
    use_recipe_pipeline: bool = True
    classify_prompt_file: str = ""
    refine_prompt_file: str = ""

    def is_ready(self) -> bool:
        """API 是否已足够发起分析（UI 不设「服务商」字段，仅需 Key + 模型）。"""
        key = (self.api_key or os.environ.get("OPENAI_API_KEY", "")).strip()
        model = self.model.strip()
        return bool(key and model)

    def resolved_provider_preset(self) -> str:
        return infer_preset_id(
            base_url=self.base_url,
            provider=self.provider,
            provider_preset=self.provider_preset,
        )

    def effective_provider(self) -> str:
        """HTTP 适配器类型；各预设均走 OpenAI 兼容 Vision API。"""
        p = self.provider.strip().lower()
        if p in ("openai", "openai_compatible", "custom", "volcengine"):
            return "openai_compatible"
        return "openai_compatible"

    def resolved_api_key(self) -> str:
        return (self.api_key or os.environ.get("OPENAI_API_KEY", "")).strip()

    def resolved_base_url(self) -> str:
        url = self.base_url.strip()
        if url:
            return url.rstrip("/")
        preset = get_preset(self.resolved_provider_preset())
        if preset and preset.default_base_url:
            return preset.default_base_url.rstrip("/")
        return "https://api.openai.com/v1"

    def analysis_settings(self) -> AnalysisSettings:
        return AnalysisSettings(
            language=self.language,
            prompt_file=self.resolved_prompt_path(),
            lut_min_confidence=self.lut_min_confidence,
            xmp_min_confidence=self.xmp_min_confidence,
            use_json_mode=self.use_json_mode,
            max_retries=self.max_retries,
        )

    def resolved_prompt_path(self) -> str:
        """返回 legacy 单次分析 prompt 路径（相对项目根）。"""
        if self.prompt_file.strip():
            return self.prompt_file.strip()
        lang = self.language.lower()
        if lang.startswith("en"):
            return DEFAULT_PROMPT_EN
        return DEFAULT_PROMPT_ZH

    def resolved_classify_prompt_path(self) -> str:
        if self.classify_prompt_file.strip():
            return self.classify_prompt_file.strip()
        return DEFAULT_CLASSIFY_PROMPT

    def resolved_refine_prompt_path(self) -> str:
        if self.refine_prompt_file.strip():
            return self.refine_prompt_file.strip()
        return DEFAULT_REFINE_PROMPT

    def classify_user_message_text(self) -> str:
        lang = self.language.lower()
        if lang.startswith("en"):
            return "Classify this image. Output style_classify.v1 JSON only. Do not output LR slider values."
        return "请对这张图片进行场景分类，仅输出 style_classify.v1 JSON，不要输出任何 LR 滑块数值。"

    def refine_user_message_text(self, context_json: str) -> str:
        lang = self.language.lower()
        if lang.startswith("en"):
            return (
                f"Context (classification + matched recipe baseline):\n{context_json}\n\n"
                "Analyze the image and output refine JSON with parameter_adjustments as deltas only."
            )
        return (
            f"上下文（分类结果 + 已匹配配方基准）：\n{context_json}\n\n"
            "请结合图片输出微调 JSON；参数须使用 parameter_adjustments（delta 模式），勿输出完整 parameters。"
        )

    def user_message_text(self) -> str:
        lang = self.language.lower()
        if lang.startswith("en"):
            return (
                "Analyze this image. Classify scene type and subtype first (portrait/landscape/mixed and lighting), "
                "then output style_analysis.v1.1 JSON using that category's reference ranges; §7a core parameters must be non-zero and plausible; §7b color extension only when style warrants (sparse)."
            )
        return "请分析这张图片。先识别场景大类与子类（人像/风光/混合及光线环境），再按该类别参考区间输出 style_analysis.v1.1 JSON；§7a 基础项须非零且合理；§7b 色彩扩展仅在有明显风格特征时稀疏输出。"

    def status_message(self) -> str:
        if self.is_ready():
            preset = get_preset(self.resolved_provider_preset())
            preset_label = preset.label if preset else self.resolved_provider_preset()
            url_hint = self.base_url.strip() or self.resolved_base_url()
            mode = "配方库双次" if self.use_recipe_pipeline else "单次分析"
            return f"已配置 · {preset_label} · {self.model} · {mode} · {url_hint}"
        return "未配置 — 请在设置中填写 API Key 与模型"


def load_ai_config() -> AiConfig:
    path = LOCAL_CONFIG if LOCAL_CONFIG.exists() else EXAMPLE_CONFIG
    if not path.exists():
        return AiConfig()
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    analysis = data.get("analysis") or {}
    provider = str(data.get("provider") or "")
    base_url = str(data.get("base_url") or "")
    provider_preset = str(data.get("provider_preset") or "")
    if not provider_preset:
        provider_preset = infer_preset_id(
            base_url=base_url,
            provider=provider,
            provider_preset="",
        )
    return AiConfig(
        provider=provider,
        provider_preset=provider_preset,
        api_key=str(data.get("api_key") or ""),
        base_url=base_url,
        model=str(data.get("model") or ""),
        language=str(analysis.get("language") or "zh-CN"),
        prompt_file=str(analysis.get("prompt_file") or ""),
        lut_min_confidence=float(analysis.get("lut_min_confidence", 0.35)),
        xmp_min_confidence=float(analysis.get("xmp_min_confidence", 0.25)),
        use_json_mode=bool(analysis.get("use_json_mode", True)),
        max_retries=int(analysis.get("max_retries", 2)),
        use_recipe_pipeline=bool(analysis.get("use_recipe_pipeline", True)),
        classify_prompt_file=str(analysis.get("classify_prompt_file") or ""),
        refine_prompt_file=str(analysis.get("refine_prompt_file") or ""),
    )


def save_ai_config(cfg: AiConfig) -> None:
    LOCAL_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    preset_id = cfg.resolved_provider_preset()
    provider = cfg.provider.strip() or cfg.effective_provider()
    payload = {
        "provider": provider,
        "provider_preset": preset_id,
        "api_key": cfg.api_key,
        "base_url": cfg.base_url,
        "model": cfg.model,
        "analysis": {
            "language": cfg.language,
            "prompt_file": cfg.prompt_file,
            "lut_min_confidence": cfg.lut_min_confidence,
            "xmp_min_confidence": cfg.xmp_min_confidence,
            "use_json_mode": cfg.use_json_mode,
            "max_retries": cfg.max_retries,
            "use_recipe_pipeline": cfg.use_recipe_pipeline,
            "classify_prompt_file": cfg.classify_prompt_file,
            "refine_prompt_file": cfg.refine_prompt_file,
        },
    }
    with open(LOCAL_CONFIG, "w", encoding="utf-8") as f:
        yaml.dump(payload, f, allow_unicode=True, default_flow_style=False)
