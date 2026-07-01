"""
Adobe Lightroom XMP 预设生成器
------------------------------
按 Camera Raw Settings (crs) 命名空间输出 .xmp 文件。
仅写入成功推测的参数；缺失参数不会出现在 XMP 中。
"""

from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from xml.dom import minidom

from config.settings import SETTINGS
from core.inference_result import ParameterResult


# XMP 命名空间
NS = {
    "x": "adobe:ns:meta/",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "crs": "http://ns.adobe.com/camera-raw-settings/1.0/",
    "xmp": "http://ns.adobe.com/xap/1.0/",
    "dc": "http://purl.org/dc/elements/1.1/",
}

ET.register_namespace("crs", NS["crs"])
ET.register_namespace("xmp", NS["xmp"])
ET.register_namespace("dc", NS["dc"])
ET.register_namespace("rdf", NS["rdf"])


def _format_value(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.2f}".rstrip("0").rstrip(".")
    if isinstance(value, bool):
        return "True" if value else "False"
    return str(value)


class XMPGenerator:
    """将 ParameterResult 列表写入 Lightroom 兼容 XMP。"""

    def __init__(
        self,
        preset_name: str = "Generated Preset",
        preset_group: Optional[str] = None,
    ):
        self.preset_name = preset_name
        self.preset_group = preset_group or SETTINGS.preset_group

    def generate(self, params: List[ParameterResult]) -> str:
        available = {p.key: p.value for p in params if p.is_available and p.include_in_xmp}

        root = ET.Element(
            "x:xmpmeta",
            {"xmlns:x": NS["x"], "x:xmptk": "Lightroom Preset Generator"},
        )
        rdf_desc = ET.SubElement(
            ET.SubElement(root, "rdf:RDF", {"xmlns:rdf": NS["rdf"]}),
            "rdf:Description",
            {
                "rdf:about": "",
                "xmlns:crs": NS["crs"],
                "xmlns:xmp": NS["xmp"],
                "xmlns:dc": NS["dc"],
            },
        )

        # 元数据
        self._set_attr(rdf_desc, "crs:HasSettings", "True")
        self._set_attr(rdf_desc, "crs:ProcessVersion", SETTINGS.process_version)
        self._set_attr(rdf_desc, "crs:Version", SETTINGS.camera_raw_version)
        self._set_attr(rdf_desc, "crs:PresetType", "Normal")
        self._set_attr(rdf_desc, "crs:SupportsAmount2", "True")
        self._set_attr(rdf_desc, "crs:SupportsAmount", "True")
        self._set_attr(rdf_desc, "crs:SupportsColor", "True")
        self._set_attr(rdf_desc, "crs:SupportsMonochrome", "True")
        self._set_attr(rdf_desc, "crs:SupportsHighDynamicRange", "True")
        self._set_attr(rdf_desc, "crs:SupportsNormalDynamicRange", "True")
        self._set_attr(rdf_desc, "crs:SupportsSceneReferred", "True")
        self._set_attr(rdf_desc, "crs:SupportsOutputReferred", "True")
        self._set_attr(rdf_desc, "crs:UUID", str(uuid.uuid4()))

        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self._set_attr(rdf_desc, "xmp:ModifyDate", now)
        self._set_attr(rdf_desc, "xmp:MetadataDate", now)

        # Group / Name 使用 Lightroom 常见的 rdf:Alt 嵌套结构
        self._append_rdf_alt(rdf_desc, "crs:Group", self.preset_group)
        self._append_rdf_alt(rdf_desc, "crs:Name", self.preset_name)

        dc_title = ET.SubElement(rdf_desc, "dc:title")
        li = ET.SubElement(
            ET.SubElement(dc_title, "rdf:Alt"), "rdf:li", {"xml:lang": "x-default"}
        )
        li.text = self.preset_name

        # 推测参数（扁平 crs 属性）
        if "Temperature" in available:
            self._set_attr(rdf_desc, "crs:WhiteBalance", "Custom")

        for key, value in available.items():
            self._set_attr(rdf_desc, f"crs:{key}", _format_value(value))

        return self._prettify(root)

    def save(self, params: List[ParameterResult], output_path: str) -> str:
        xml_str = self.generate(params)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(xml_str)
        return output_path

    @staticmethod
    def _append_rdf_alt(parent: ET.Element, tag: str, text: str) -> None:
        elem = ET.SubElement(parent, tag)
        alt = ET.SubElement(elem, "rdf:Alt")
        li = ET.SubElement(alt, "rdf:li", {"xml:lang": "x-default"})
        li.text = text

    @staticmethod
    def _set_attr(element: ET.Element, qname: str, value: str) -> None:
        element.set(qname, value)

    @staticmethod
    def _prettify(root: ET.Element) -> str:
        rough = ET.tostring(root, encoding="unicode")
        parsed = minidom.parseString(rough)
        return parsed.toprettyxml(indent="  ", encoding=None)

    @staticmethod
    def missing_summary(params: List[ParameterResult]) -> List[str]:
        """返回缺失参数的提示列表，供 GUI 展示。"""
        lines = []
        for p in params:
            if not p.is_available:
                lines.append(p.to_display_line())
        return lines
