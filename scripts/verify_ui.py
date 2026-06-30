"""启动前检查 UI 代码是否为 v1.6 布局。"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import gui.copy as copy_mod  # noqa: E402
import gui.widgets as widgets_mod  # noqa: E402
from config.settings import SETTINGS  # noqa: E402


def main() -> int:
    doc = widgets_mod.ImageZone.__doc__ or ""
    checks = [
        ("ImageZone 文档含 v1.6", "v1.6" in doc),
        ("上传底片按钮文案", copy_mod.COPY.get("plate.pick") == "上传底片"),
        ("空态提示文案", "plate.idle_hint" in copy_mod.COPY),
        ("UI 版本配置", SETTINGS.ui_version == "1.6.0"),
        ("已移除 PlateControlCard", not hasattr(widgets_mod, "PlateControlCard")),
        ("widgets 路径在项目内", str(ROOT) in str(Path(widgets_mod.__file__).resolve())),
    ]
    ok = True
    for name, passed in checks:
        status = "OK" if passed else "FAIL"
        print(f"  [{status}] {name}")
        ok = ok and passed
    print(f"widgets: {widgets_mod.__file__}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
