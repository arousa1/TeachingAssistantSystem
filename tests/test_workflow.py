"""
pytest 直接跑：uv run pytest tests/
"""
import os
import tempfile
import zipfile
from src.agent.graph import graph
from src.agent.state import AgentState

def _make_zip() -> str:
    tmp = tempfile.mktemp(suffix=".zip")
    with zipfile.ZipFile(tmp, "w") as z:
        z.writestr("hello.py", "print('hi')")
        z.writestr("doc.pdf", b"%PDF-1.4 fake pdf content")
    return tmp

def test_end_to_end():
    z = _make_zip()
    state: AgentState = {
        "archive_path": z,
        "extract_to": tempfile.mkdtemp(),
        "files": [],
        "classified": [],
        "report": "",
    }
    final = graph.invoke(state)
    # 查看分类结果
    for item in final["classified"]:
        print("[test] file:", item["file_path"], "-> type:", item["type"])

    assert len(final["files"]) == 2
    assert len(final["classified"]) == 2
    types = {c["type"] for c in final["classified"]}
    assert "code" in types
    assert "doc" in types
    os.unlink(z)
