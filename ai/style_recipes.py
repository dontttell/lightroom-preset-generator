"""
风格配方库：加载、匹配、与 AI 微调结果合并。
见 docs/STYLE_RECIPE_SYSTEM.md
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, Union

import yaml

from ai.parameter_registry import (
    COLOR_MODULE_KEYS,
    CORE_PARAMETER_KEYS,
    PARAMETER_SPECS,
)

ROOT = Path(__file__).resolve().parent.parent
RECIPES_DIR = ROOT / "config" / "style_recipes"
FALLBACK_RECIPE_ID = "generic-daylight-landscape"
MATCH_THRESHOLD = 30


@dataclass
class StyleRecipe:
    id: str
    version: int
    name_zh: str
    description: str = ""
    match: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Union[int, float]] = field(default_factory=dict)
    default_confidence: float = 0.72
    optional_7b: Dict[str, Union[int, float]] = field(default_factory=dict)
    tweak_limits: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    priority_adjustments: List[str] = field(default_factory=list)
    editing_hints: List[str] = field(default_factory=list)


@dataclass
class ClassifyResult:
    """Call① style_classify.v1 解析结果（宽松）。"""

    category: str
    subtype: str = ""
    light: str = ""
    pre_graded: bool = False
    local_mask_likely: bool = False
    scene_keywords: List[str] = field(default_factory=list)
    style_hints: List[str] = field(default_factory=list)
    subtype_confidence: float = 0.0
    candidate_recipe_ids: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ClassifyResult":
        return cls(
            category=str(data.get("category", "")).strip(),
            subtype=str(data.get("subtype", "")).strip(),
            light=str(data.get("light", "")).strip(),
            pre_graded=bool(data.get("pre_graded", False)),
            local_mask_likely=bool(data.get("local_mask_likely", False)),
            scene_keywords=_as_str_list(data.get("scene_keywords")),
            style_hints=_as_str_list(data.get("style_hints")),
            subtype_confidence=float(data.get("subtype_confidence", 0.0) or 0.0),
            candidate_recipe_ids=_as_str_list(data.get("candidate_recipe_ids")),
        )


def _as_str_list(value: Any) -> List[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    return [str(x).strip() for x in value if str(x).strip()]


def _parse_tweak_limits(raw: Any) -> Dict[str, Tuple[float, float]]:
    out: Dict[str, Tuple[float, float]] = {}
    if not isinstance(raw, dict):
        return out
    for key, pair in raw.items():
        if isinstance(pair, (list, tuple)) and len(pair) == 2:
            out[str(key)] = (float(pair[0]), float(pair[1]))
    return out


def _recipe_from_yaml(data: Mapping[str, Any]) -> StyleRecipe:
    recipe_id = str(data.get("id", "")).strip()
    if not recipe_id:
        raise ValueError("recipe missing id")
    params = data.get("parameters") or {}
    opt = data.get("optional_7b") or {}
    return StyleRecipe(
        id=recipe_id,
        version=int(data.get("version", 1)),
        name_zh=str(data.get("name_zh", recipe_id)),
        description=str(data.get("description", "")),
        match=dict(data.get("match") or {}),
        parameters={k: v for k, v in params.items()},
        default_confidence=float(data.get("default_confidence", 0.72)),
        optional_7b={k: v for k, v in opt.items()},
        tweak_limits=_parse_tweak_limits(data.get("tweak_limits")),
        priority_adjustments=list(data.get("priority_adjustments") or []),
        editing_hints=list(data.get("editing_hints") or []),
    )


def load_all_recipes(recipes_dir: Optional[Path] = None) -> Dict[str, StyleRecipe]:
    base = recipes_dir or RECIPES_DIR
    recipes: Dict[str, StyleRecipe] = {}
    if not base.is_dir():
        return recipes
    for path in sorted(base.glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        recipe = _recipe_from_yaml(data)
        recipes[recipe.id] = recipe
    return recipes


def get_recipe(recipe_id: str, recipes: Optional[Mapping[str, StyleRecipe]] = None) -> Optional[StyleRecipe]:
    catalog = recipes if recipes is not None else load_all_recipes()
    return catalog.get(recipe_id)


def _keyword_hits(keywords: Sequence[str], haystack: Sequence[str]) -> int:
    if not keywords or not haystack:
        return 0
    joined = " ".join(haystack).lower()
    hits = 0
    for kw in keywords:
        if kw and kw.lower() in joined:
            hits += 1
    return hits


def score_recipe(recipe: StyleRecipe, classify: ClassifyResult) -> int:
    match = recipe.match
    categories = [str(c).strip() for c in (match.get("categories") or [])]
    if categories and classify.category and classify.category not in categories:
        return 0

    score = 0
    subtypes = [str(s).strip() for s in (match.get("subtypes") or [])]
    if classify.subtype and classify.subtype in subtypes:
        score += 40

    kw_zh = match.get("keywords_zh") or []
    kw_en = match.get("keywords_en") or []
    all_hints = classify.scene_keywords + classify.style_hints
    score += _keyword_hits(kw_zh, all_hints) * 15
    score += _keyword_hits(kw_en, all_hints) * 15

    if recipe.id in classify.candidate_recipe_ids:
        score += 20

    return score


def match_recipe(
    classify: ClassifyResult,
    recipes: Optional[Mapping[str, StyleRecipe]] = None,
) -> StyleRecipe:
    catalog = recipes if recipes is not None else load_all_recipes()
    if not catalog:
        raise FileNotFoundError(f"no recipes in {RECIPES_DIR}")

    best_id = FALLBACK_RECIPE_ID
    best_score = -1
    for rid, recipe in catalog.items():
        s = score_recipe(recipe, classify)
        if s > best_score:
            best_score = s
            best_id = rid

    if best_score < MATCH_THRESHOLD:
        best_id = FALLBACK_RECIPE_ID

    recipe = catalog.get(best_id) or catalog.get(FALLBACK_RECIPE_ID)
    if recipe is None:
        recipe = next(iter(catalog.values()))
    return recipe


def _clamp_value(key: str, value: Union[int, float]) -> Union[int, float]:
    spec = PARAMETER_SPECS.get(key)
    if spec is None:
        return value
    clamped = max(spec.min_val, min(spec.max_val, value))
    if spec.value_type is int:
        return int(round(clamped))
    return float(clamped)


def _apply_delta(
    key: str,
    base: Union[int, float],
    delta: float,
    tweak_limits: Mapping[str, Tuple[float, float]],
    pre_graded_scale: float,
) -> Union[int, float]:
    lo, hi = tweak_limits.get(key, (-9999.0, 9999.0))
    scaled_delta = delta * pre_graded_scale
    scaled_delta = max(lo, min(hi, scaled_delta))
    return _clamp_value(key, base + scaled_delta)


def merge_recipe_with_refine(
    recipe: StyleRecipe,
    refine: Mapping[str, Any],
    *,
    pre_graded: bool = False,
    subtype_confidence: float = 1.0,
) -> Dict[str, Any]:
    """
    将配方基准与 Call② 的 parameter_adjustments 合并为 style_analysis 形 JSON。

    refine 期望字段：
    - overall_impression, editing_steps, priority_adjustments
    - parameter_adjustments: { key: { delta, confidence?, reason? } }
    - optional_7b: { key: { value, confidence? } } 或裸 value
    """
    pre_scale = 0.4 if pre_graded else 1.0
    conf_penalty = 0.12 if subtype_confidence < 0.55 else 0.0

    parameters: Dict[str, Dict[str, Any]] = {}
    for key in CORE_PARAMETER_KEYS:
        base = recipe.parameters.get(key, PARAMETER_SPECS[key].default)
        adj = (refine.get("parameter_adjustments") or {}).get(key) or {}
        delta = float(adj.get("delta", 0) or 0)
        value = _apply_delta(key, base, delta, recipe.tweak_limits, pre_scale)
        conf = float(adj.get("confidence", recipe.default_confidence))
        conf = min(conf, recipe.default_confidence)
        conf = max(0.0, conf - conf_penalty)
        if pre_graded:
            conf = min(conf, 0.50)
        entry: Dict[str, Any] = {"value": value, "confidence": round(conf, 3)}
        if adj.get("reason"):
            entry["reason"] = str(adj["reason"])
        parameters[key] = entry

    # 合并 §7b
    base_7b = dict(recipe.optional_7b)
    refine_7b = refine.get("optional_7b") or {}
    merged_7b: Dict[str, Union[int, float]] = dict(base_7b)
    for key, raw in refine_7b.items():
        if key not in COLOR_MODULE_KEYS:
            continue
        if isinstance(raw, dict):
            val = raw.get("value", 0)
        else:
            val = raw
        merged_7b[key] = _clamp_value(key, val)

    for key, val in merged_7b.items():
        if val == 0 and key not in refine_7b:
            continue
        raw = refine_7b.get(key)
        conf = 0.52
        if isinstance(raw, dict) and "confidence" in raw:
            conf = float(raw["confidence"])
        else:
            conf = min(recipe.default_confidence, 0.55)
        if pre_graded:
            conf = min(conf, 0.50)
        parameters[key] = {"value": val, "confidence": round(conf, 3)}

    priority = list(refine.get("priority_adjustments") or recipe.priority_adjustments)
    impression = str(
        refine.get("overall_impression")
        or f"【{recipe.name_zh}】基于配方库起点，结合画面微调。"
    )
    steps = refine.get("editing_steps") or _default_editing_steps(recipe, pre_graded)

    return {
        "overall_impression": impression,
        "editing_steps": steps,
        "priority_adjustments": priority[:5],
        "parameters": parameters,
        "_meta": {
            "recipe_id": recipe.id,
            "recipe_version": recipe.version,
            "pre_graded": pre_graded,
        },
    }


def _default_editing_steps(recipe: StyleRecipe, pre_graded: bool) -> List[Dict[str, Any]]:
    note = "原图可能已后期，以下为学习性微调方向。" if pre_graded else ""
    hints = recipe.editing_hints[:3]
    steps = [
        {
            "step": 1,
            "title": "场景识别",
            "description": f"匹配配方「{recipe.name_zh}」。{note}".strip(),
        }
    ]
    for i, hint in enumerate(hints, start=2):
        steps.append({"step": i, "title": f"调整要点 {i - 1}", "description": hint})
    return steps


def recipe_context_for_prompt(recipe: StyleRecipe) -> Dict[str, Any]:
    """供 Call② user message 附带的配方摘要。"""
    return {
        "id": recipe.id,
        "name_zh": recipe.name_zh,
        "parameters": recipe.parameters,
        "optional_7b": recipe.optional_7b,
        "tweak_limits": {k: list(v) for k, v in recipe.tweak_limits.items()},
        "priority_adjustments": recipe.priority_adjustments,
        "editing_hints": recipe.editing_hints,
    }
