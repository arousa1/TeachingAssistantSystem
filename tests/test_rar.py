"""
RAR 端到端测试
与 test_workflow.py 逻辑相同，只是把压缩格式换成 RAR。
"""
import os
import tempfile
import rarfile                      #  pip install rarfile
from src.agent.graph import graph
from src.agent.state import AgentState

# ------------------------------------------------------------------
#  辅助：生成内存 RAR 文件（两个样本）
# ------------------------------------------------------------------
def _make_rar() -> str:
    """
    创建内存 RAR，返回临时文件路径
    内容：
      1. main.cpp  -> code
      2. manual.pdf -> doc
    """
    tmp = tempfile.mktemp(suffix=".rar")

    # 需要系统里有 rar 命令；没有就用 rarfile 纯 Python 方案
    with rarfile.RarFile(tmp, 'w') as rf:
        rf.writestr("main.cpp", "#include <iostream>\nint main(){}\n")
        rf.writestr("manual.pdf", b"%PDF-1.7 fake pdf content")
    return tmp

# ------------------------------------------------------------------
#  测试用例
# ------------------------------------------------------------------
def test_rar_end_to_end():
    # rar_path = _make_rar()
    state: AgentState = {
        "archive_path": r"D:\Code\Python\tmp\yu-ai-code-mother-frontend.rar",
        "extract_to": tempfile.mkdtemp(),
        "files": [],
        "classified": [],
        "report": "",
        "grouped": {},
        "group_keys": [],
    }

    # 跑完整图
    final = graph.invoke(state)

    # 基础断言
    assert len(final["files"]) == 2, "应解压出 2 个文件"
    assert len(final["classified"]) == 2, "应完成 2 次分类"
    types = {c["type"] for c in final["classified"]}
    assert "code" in types, "期望识别出 code"
    assert "doc" in types, "期望识别出 doc"

    # 可选：验证分组
    assert "code" in final["group_keys"]
    assert "doc" in final["group_keys"]

    # os.unlink(rar_path)