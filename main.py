"""
Lightroom 预设生成器 — 程序入口
--------------------------------
Windows 运行方式:
  1. pip install -r requirements.txt
  2. python main.py
  或双击 run.bat
"""

from __future__ import annotations

import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中（便于各模块 import）
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gui.main_window import run_app  # noqa: E402


def main() -> int:
    return run_app()


if __name__ == "__main__":
    raise SystemExit(main())
