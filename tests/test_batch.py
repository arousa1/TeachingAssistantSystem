"""
批量入口端到端测试
"""
import subprocess
import tempfile
import zipfile
from pathlib import Path

# 1. 拿到 7z.exe 的绝对路径（相对于本测试文件）
_7Z = Path(__file__).resolve().parent.parent / "src" / "tools" / "bin" / "7z.exe"

import os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent   # 项目根
sys.path.insert(0, str(ROOT))                   # 把根加入路径



# ---------- 辅助：生成内存压缩包 ----------
def _build_folder_of_archives(folder: Path):
    """
    在 folder 里生成 2 个压缩包：
      1.zip ： hello.py  + readme.pdf
      2.rar ： main.cpp  + manual.pdf
    """
    # 1. ZIP-1
    with zipfile.ZipFile(folder / "1.zip", "w") as z:
        z.writestr("hello.py", "print('hello')")
        z.writestr("readme.pdf", b"%PDF-1.4 fake pdf")

    # 2. ZIP-2 （同样纯 Python，不再调用 7z）
    with zipfile.ZipFile(folder / "2.zip", "w") as z:
        z.writestr("main.cpp", "#include <iostream>\nint main(){}")
        z.writestr("manual.pdf", b"%PDF-1.7 fake pdf")



# ---------- pytest 用例 ----------
def test_batch_end_to_end():
    tmp = Path(tempfile.mkdtemp())
    _build_folder_of_archives(tmp)          # 生成测试压缩包

    # 调用批量入口
    # 现在可以正常导入
    proc = subprocess.run(
        [sys.executable, "-m", "src.batch_main", "--dir", str(tmp)],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT)},  # 显式传给子进程
        text=True,
    )

    assert proc.returncode == 0 == 0, f"批量脚本异常退出: {proc}"

    # 简单日志断言（可自行扩展）
    out = proc.stdout
    assert "扫描到 2 个压缩包" in out
    assert "code" in out and "doc" in out   # 分类关键词出现