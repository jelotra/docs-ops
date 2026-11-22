# tools/

本目录由脚手架维护（`scaffold.py tests`），不属于业务代码。

## run_tests.py

并行测试入口。优先用 `pytest-xdist`（`-n <jobs>`）；没有 xdist 时自动退化为串行，
并在摘要里写明原因——不会静默降速。

`auto` = **CPU 数的一半**：Python 测试常常再派子进程（git、kubectl、CLI），满核并发
会过度订阅。实测 workloop（957 用例）串行 255s、4 进程 99s、8 进程 216s。

```powershell
python tools/run_tests.py                  # 自动并发（半核数）
python tools/run_tests.py --jobs 8         # 自己指定
python tools/run_tests.py --jobs 1         # 子进程重型套件可用串行对照
python tools/run_tests.py --json           # 末尾一行机器可读摘要
python tools/run_tests.py -- -x -k "not slow"
```

## 更新方式

模板的唯一真值在 `skills/scaffold/scaffolding/test_runner.py`。升级后重新应用：

```powershell
python skills/workloop/scripts/scaffold.py tests --target <skill 根> --write
python skills/workloop/scripts/scaffold.py tests --target <skill 根> --check   # 漂移门禁
```
