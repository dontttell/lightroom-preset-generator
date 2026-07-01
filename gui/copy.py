"""
界面文案 — 与 UI_UX_DESIGN.md §11 对齐。
修改措辞请优先改文档 §11，再同步此文件。
"""

from __future__ import annotations

from typing import Any, Dict

# fmt: off
COPY: Dict[str, str] = {
    # 11.3.1
    "toolbar.open": "打开图片",
    "toolbar.ai_analyze": "开始 AI 分析",
    "toolbar.export": "导出…",
    "menu.settings_ai": "AI 服务…",
    "menu.about": "关于",
    # 11.3.2
    "image.empty": "拖入图片，或点击「打开图片」",
    "image.reference": "参考风格图",
    "plate.label_before": "底片",
    "plate.label_after": "试看效果",
    "plate.placeholder_before": "点击「上传底片」或将图片拖入此区域",
    "plate.placeholder_after": "点击上方「应用 LUT 预览」查看效果",
    # 11.3.3（v1.6 左栏唯一入口）
    "plate.section_title": "在自己的底片上试看",
    "plate.pick": "上传底片",
    "plate.pick_replace": "更换底片",
    "plate.apply_lut": "应用 LUT 预览",
    "plate.no_plate": "尚未选择底片 — 请上传或拖入一张未修图",
    "plate.drop_hint": "支持拖入 JPG / PNG / WebP 到底片预览区",
    "plate.pick_panel_hint": "将未修底片拖入下方区域，或点击「上传底片」",
    "plate.idle_hint": "打开参考风格图并完成 AI 分析后，可上传底片试看 LUT 效果",
    "plate.wait_lut": "请先完成 AI 分析，再上传底片并试看 LUT 效果",
    "plate.selected": "已选：{filename}",
    "plate.footnote": "由 AI 参考参数本地渲染，与 Lightroom 效果可能有差异，仅供试看。",
    # 11.3.4 StatusCard
    "status.welcome.title": "欢迎使用",
    "status.welcome.subtitle": "打开图片后，将自动尝试精确识别 Lightroom 编辑数据。",
    "status.precise.title": "已精确识别 Lightroom 编辑数据",
    "status.precise.subtitle": "以下为 Camera Raw 真实参数。可在 Lightroom 中对照学习，并导出 XMP 预设。",
    "status.precise.detail_sidecar": "已从配套 XMP 文件读取真实调色参数",
    "status.precise.detail_embedded": "已从图片内嵌数据读取真实调色参数",
    "status.no_meta_unconfigured.title": "未能精确识别 · 可使用 AI 辅助学习",
    "status.no_meta_unconfigured.subtitle": (
        "需先配置 AI 服务才能分析此图。请打开「设置 → AI 服务」填写 API Key 与模型。"
    ),
    "status.no_meta_ready.title": "未能精确识别 · 可使用 AI 辅助学习",
    "status.no_meta_ready.subtitle": "点击「开始 AI 分析」，获取风格解读与参考参数。",
    "status.ai_analyzing.title": "正在分析…",
    "status.ai_analyzing.subtitle": "请稍候，图片将上传至您配置的 AI 服务。",
    "status.ai_done.title": "AI 参考分析完成",
    "status.ai_done.subtitle": "以下为学习思路与参考参数，请在 Lightroom 中验证、微调。",
    # 11.3.5
    "ai.chip_unconfigured": "● AI 未配置",
    "ai.chip_configured": "● AI 已配置",
    "ai.chip_tooltip_ready": "AI 服务已就绪",
    "ai.chip_tooltip_setup": "点击打开 AI 服务设置",
    "ai.banner": "AI 服务未配置 — 未能精确识别的图片需先配置 API 才能进行 AI 分析",
    "ai.banner_action": "前往设置",
    "ai.inline_title": "AI 服务未配置",
    "ai.inline_body": "当前图片未能精确识别 Lightroom 编辑数据。配置 API 后可进行 AI 风格分析。",
    "ai.tooltip_disabled": "请先在「设置 → AI 服务」中配置 API Key 与模型",
    "ai.tooltip_path_a": "当前图片已精确识别并提取参数，无需 AI 分析",
    "ai.tooltip_no_image": "请先打开未能精确识别的参考图",
    # 11.3.6
    "learn.welcome_ready": (
        "【欢迎使用】\n\n"
        "打开一张 Lightroom 导出的 JPG / TIFF，\n"
        "自动尝试精确识别 Lightroom 编辑数据。\n\n"
        "● 已精确识别 → 直接读取真实调色参数，无需 AI\n"
        "● 未能精确识别 → 点击「开始 AI 分析」获取风格解读"
    ),
    "learn.welcome_unconfigured": (
        "【欢迎使用】\n\n"
        "打开一张 Lightroom 导出的 JPG / TIFF，\n"
        "自动尝试精确识别 Lightroom 编辑数据。\n\n"
        "● 已精确识别 → 直接读取真实调色参数，无需 AI\n"
        "● 未能精确识别 → 需配置 AI 服务后分析风格\n\n"
        "⚠ AI 服务尚未配置 — 请点击「前往设置」\n"
        "  或菜单「设置 → AI 服务」填写 API Key 与模型。"
    ),
    "learn.path_b_ready": (
        "此图未能精确识别 Lightroom 编辑数据。\n\n"
        "点击「开始 AI 分析」获取风格解读，以及参考 XMP / LUT。"
    ),
    "learn.path_b_unconfigured": (
        "此图未能精确识别 Lightroom 编辑数据。\n\n"
        "配置 AI 服务后，可分析风格并生成参考参数。"
    ),
    # 11.3.7
    "error.read_image": "无法读取图像：{path}",
    "error.read_plate": "无法读取底片",
    "error.metadata": "精确识别失败：{reason}",
    "error.ai_not_configured": "请先在设置中配置 API Key 与模型名称。",
    "error.ai_failed": "AI 分析失败：{reason}",
    "error.preview_failed": "预览失败",
    "info.export_need_session": "请先完成精确识别或 AI 分析。",
    "info.export_need_ai": "请先完成 AI 分析。",
    "info.export_ok": "已保存至：\n{paths}",
    "status.ready": "就绪",
    "status.detecting": "正在精确识别…",
    "status.ai_running": "AI 分析中…",
    "status.lut_preview_ok": "试看效果已更新（本地渲染）",
    "status.export_done": "导出完成",
    "status.detect_failed": "精确识别失败",
    "status.ai_failed": "AI 分析失败",
    "status.bar_precise": "精确识别 · {filename} · {ms:.0f} ms",
    "status.bar_ai_pending": "待 AI 分析 · {filename}",
    "status.bar_ai_done": "AI 参考分析 · {filename} · {ms:.0f} ms",
    # 11.3.8
    "export.title": "导出",
    "export.preset_name": "预设名称",
    "export.xmp_check": "导出 XMP 预设",
    "export.lut_check": "同时导出 LUT (.cube)",
    "export.lut_hint": "由参数本地烘焙；学习调色请以 XMP 为准。",
    "settings.title": "设置 — AI 服务",
    "settings.provider": "服务商",
    "settings.api_key_placeholder": "留空则尝试读取环境变量 OPENAI_API_KEY",
    "settings.base_url_placeholder": "OpenAI 兼容接口根地址（含 /v3 等版本路径）",
    "settings.test_connection": "测试连接",
    "settings.test_connection_failed": "测试连接失败",
    "settings.error_missing_fields": "请先填写 API Key 与模型 ID / 名称。",
    "settings.error_custom_url": "自定义服务商须填写 API Base URL。",
    "settings.volcengine_test_hint": (
        "火山方舟若此处失败，仍可用一张参考图点击「开始 AI 分析」验证；"
        "部分账号对 /models 列表接口支持不完整。"
    ),
    "settings.privacy": (
        "选择服务商后 Base URL 将自动填充。填写 API Key 与模型 ID 后，"
        "未能精确识别的图片可发起 AI 分析。图片将上传至对应接口，请遵守服务商隐私政策。"
    ),
    "about.title_app": "Lightroom 预设学习器",
    "about.body": (
        "<p>已精确识别：直接读取真实调色参数并导出 XMP 预设。<br>"
        "未能精确识别：配置 AI 后分析风格，导出参考 XMP / LUT。</p>"
        "<p>精确识别路径无需 API；AI 辅助学习需在设置中自行配置。</p>"
    ),
}
# fmt: on


def t(key: str, **kwargs: Any) -> str:
    template = COPY[key]
    return template.format(**kwargs) if kwargs else template
