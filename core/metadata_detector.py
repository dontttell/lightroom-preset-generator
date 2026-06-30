"""
Metadata 检测
-------------
从 JPG/PNG 内嵌 XMP 或同目录 sidecar 检测 Lightroom Camera Raw 设置。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Literal, Optional

CRS_NS = "http://ns.adobe.com/camera-raw-settings/1.0/"
CRS_PREFIX = "{" + CRS_NS + "}"

# 至少存在若干核心字段才视为有效 LR metadata
CORE_CRS_KEYS = {
    "Exposure2012",
    "Contrast2012",
    "Temperature",
    "Highlights2012",
    "Shadows2012",
    "Saturation",
    "HasSettings",
}


@dataclass
class MetadataScanResult:
    has_lightroom_metadata: bool
    source: Literal["embedded_xmp", "sidecar_xmp", "none"]
    crs_fields: Dict[str, Any] = field(default_factory=dict)
    message: str = ""


def scan_image_metadata(image_path: str) -> MetadataScanResult:
    path = Path(image_path)
    sidecar = path.with_suffix(".xmp")
    if sidecar.is_file():
        fields = _parse_xmp_file(sidecar)
        if _is_valid_crs(fields):
            return MetadataScanResult(
                has_lightroom_metadata=True,
                source="sidecar_xmp",
                crs_fields=fields,
                message=f"已从配套 XMP 文件读取（{sidecar.name}）",
            )

    embedded = _read_embedded_xmp(path)
    if embedded:
        fields = _parse_xmp_string(embedded)
        if _is_valid_crs(fields):
            return MetadataScanResult(
                has_lightroom_metadata=True,
                source="embedded_xmp",
                crs_fields=fields,
                message="已从图片内嵌数据读取",
            )

    return MetadataScanResult(
        has_lightroom_metadata=False,
        source="none",
        message="未能精确识别 Lightroom 编辑数据",
    )


def _is_valid_crs(fields: Dict[str, Any]) -> bool:
    if not fields:
        return False
    if fields.get("HasSettings") in (True, "True", "true", "1"):
        return True
    return bool(CORE_CRS_KEYS.intersection(fields.keys()))


def _read_embedded_xmp(path: Path) -> Optional[str]:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    # XMP 包通常以 x:xmpmeta 或 xmpmeta 开始
    for marker in (b"<x:xmpmeta", b"<xmpmeta", b"<?xpacket"):
        idx = data.find(marker)
        if idx != -1:
            end = data.find(b"</x:xmpmeta>", idx)
            if end == -1:
                end = data.find(b"</xmpmeta>", idx)
            if end != -1:
                chunk = data[idx : end + 20]
                return chunk.decode("utf-8", errors="ignore")
    return None


def _parse_xmp_file(path: Path) -> Dict[str, Any]:
    try:
        return _parse_xmp_string(path.read_text(encoding="utf-8", errors="ignore"))
    except OSError:
        return {}


def _parse_xmp_string(xmp: str) -> Dict[str, Any]:
    fields: Dict[str, Any] = {}
    # crs:Attribute="value" 或 crs:Attribute='value'
    for m in re.finditer(r'crs:(\w+)=["\']([^"\']*)["\']', xmp):
        key, val = m.group(1), m.group(2)
        fields[key] = _coerce_value(val)
    # rdf:Description 上的 xmlns:crs 属性（ElementTree 备选）
    if not fields:
        fields = _parse_xmp_etree(xmp)
    return fields


def _parse_xmp_etree(xmp: str) -> Dict[str, Any]:
    import xml.etree.ElementTree as ET

    fields: Dict[str, Any] = {}
    try:
        # 清理非法字符
        clean = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", xmp)
        root = ET.fromstring(clean)
    except ET.ParseError:
        return fields
    for elem in root.iter():
        tag = elem.tag
        if tag.startswith(CRS_PREFIX):
            key = tag[len(CRS_PREFIX) :]
            if elem.text:
                fields[key] = _coerce_value(elem.text)
        for attr_key, attr_val in elem.attrib.items():
            if "camera-raw-settings" in attr_key or attr_key.startswith("crs:"):
                local = attr_key.split("}")[-1].replace("crs:", "")
                fields[local] = _coerce_value(attr_val)
    return fields


def _coerce_value(text: str) -> Any:
    t = text.strip()
    if t.lower() == "true":
        return True
    if t.lower() == "false":
        return False
    try:
        if "." in t:
            return float(t)
        return int(t)
    except ValueError:
        return t
