import os
from typing import Dict, List

from .state import AgentState
from ..tools.archive import extract_archive
from ..tools.classify import classify_file
from ..utils.logger import get_logger

logger = get_logger(__name__)

# ---------- 节点函数 ----------
def node_extract(state: AgentState) -> AgentState:
    """解压"""
    arch = state["archive_path"]
    dest = state["extract_to"]
    logger.info("Start extracting %s", arch)
    extract_dir = extract_archive(arch, dest)
    # 递归列出所有文件
    files = []
    for root, _, fs in os.walk(extract_dir):
        for f in fs:
            files.append(os.path.join(root, f))
    logger.info("Extracted %d files -> %s", len(files), extract_dir)
    return {**state,
            "files": files,
            "extract_to": extract_dir,
            "grouped": {},      # 空字典占位
            "group_keys": [],}

def node_classify(state: AgentState) -> AgentState:
    """批量 LLM 分类"""
    files = state["files"]
    logger.info("Classifying %d files", len(files))
    classified = []
    for f in files:
        try:
            res = classify_file(f)
            res["file_path"] = f
            classified.append(res)
        except Exception as e:
            logger.exception("classify failed: %s", f)
            classified.append({"type": "unknown", "language": "", "confidence": 0, "file_path": f})
    logger.info("Classified done")
    return {**state, "classified": classified}

def node_dispatch(state: AgentState) -> AgentState:
    grouped: Dict[str, List[str]] = {}
    for item in state["classified"]:
        t = item["type"]
        grouped.setdefault(t, []).append(item["file_path"])
    logger.info("Dispatch groups: %s", list(grouped.keys()))
    return {**state, "grouped": grouped, "group_keys": list(grouped.keys())}

def node_post_code(state: AgentState) -> AgentState:
    """示例：代码格式化"""
    from ..tools.post_process import format_code_batch
    files = state["grouped"].get("code", [])
    if files:
        logger.info("Post-process %d code files", len(files))
        format_code_batch(files)
    return state

def node_post_doc(state: AgentState) -> AgentState:
    """示例：doc 转 txt"""
    from ..tools.post_process import doc_to_txt_batch
    files = state["grouped"].get("doc", [])
    if files:
        logger.info("Post-process %d doc files", len(files))
        doc_to_txt_batch(files)
    return state
