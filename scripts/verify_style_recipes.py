#!/usr/bin/env python3
"""校验 config/style_recipes/*.yaml 结构与参数范围。"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ai.parameter_registry import CORE_PARAMETER_KEYS, PARAMETER_SPECS
from ai.style_recipes import FALLBACK_RECIPE_ID, load_all_recipes, match_recipe, ClassifyResult


def main() -> int:
    recipes = load_all_recipes()
    if not recipes:
        print("FAIL: no recipes found")
        return 1

    errors: list[str] = []

    if FALLBACK_RECIPE_ID not in recipes:
        errors.append(f"missing fallback recipe: {FALLBACK_RECIPE_ID}")

    for rid, recipe in recipes.items():
        if rid != recipe.id:
            errors.append(f"{rid}: id mismatch in yaml")
        for key in CORE_PARAMETER_KEYS:
            if key not in recipe.parameters:
                errors.append(f"{rid}: missing core parameter {key}")
            else:
                val = recipe.parameters[key]
                spec = PARAMETER_SPECS[key]
                if not (spec.min_val <= val <= spec.max_val):
                    errors.append(f"{rid}: {key}={val} out of [{spec.min_val}, {spec.max_val}]")
        for key, (lo, hi) in recipe.tweak_limits.items():
            if key not in PARAMETER_SPECS:
                errors.append(f"{rid}: unknown tweak_limits key {key}")
            if lo > hi:
                errors.append(f"{rid}: tweak_limits {key} min>max")

    # 烟雾测试：草原关键词应命中 film-lowsat-meadow
    meadow = match_recipe(
        ClassifyResult(
            category="L",
            subtype="L-自然通用",
            scene_keywords=["草原", "牛群"],
            style_hints=["胶片", "低饱和"],
            candidate_recipe_ids=["film-lowsat-meadow"],
        ),
        recipes,
    )
    if meadow.id != "film-lowsat-meadow":
        errors.append(f"match smoke test failed: got {meadow.id}")

    if errors:
        print("FAIL:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"OK: {len(recipes)} recipes validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
