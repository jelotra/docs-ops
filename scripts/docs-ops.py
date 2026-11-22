"""Entry point; provider selection and permissions belong to the host."""

import sys
from pathlib import Path

# 中文 Windows 默认控制台为 GBK，直接 print ✓/中文会抛 UnicodeEncodeError。
# 入口统一切到 UTF-8（errors=replace 保证任何字符都不崩），使 CLI 无需环境变量即可运行。
for _stream in (sys.stdout, sys.stderr):
    _reconfigure = getattr(_stream, "reconfigure", None)
    if _reconfigure is not None:
        try:
            _reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            pass  # 已被重定向为不支持 reconfigure 的流时保持原样

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jedocsops.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
