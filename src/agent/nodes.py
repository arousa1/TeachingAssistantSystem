"""
节点函数集合

每个函数签名：def node_xxx(state: AgentState) -> AgentState
返回值必须是 **完整状态字典**（或新增/覆盖字段），否则下游拿不到数据。
"""
import os
from typing import Dict, List
from pathlib import Path
import tempfile

from .state import AgentState
from ..tools.archive import extract_archive
from ..tools.classify import classify_file
from ..tools.post_process import format_code_batch, doc_to_txt_batch
from ..utils.logger import get_logger

logger = get_logger(__name__)

SUPPORT_SUFFIX = (".zip", ".rar", ".7z", ".tar", ".gz", ".tgz")

def node_scan_dir(state: AgentState) -> AgentState:
    """
    1. 扫描用户指定目录
    2. 把所有压缩包路径写进队列
    3. 后续会逐个弹出处理
    """
    scan_dir = Path(state["scan_dir"]).resolve()
    if not scan_dir.is_dir():
        raise ValueError(f"目录不存在: {scan_dir}")

    pkg_queue = [str(p) for p in scan_dir.iterdir()
                 if p.suffix.lower() in SUPPORT_SUFFIX]
    pkg_queue.sort()          # 固定顺序，方便测试
    logger.info("扫描到 %d 个压缩包", len(pkg_queue))

    return {**state, "pkg_queue": pkg_queue, "current_pkg": ""}

def node_process_one(state: AgentState) -> AgentState:
    """
    从队列 pop 出一个压缩包，调用**原来的单包图**完成
    解压-分类-后处理，然后把结果合并回主状态。
    """
    queue = state["pkg_queue"]
    if not queue:               # 队列空，直接返回
        return state

    current_pkg = queue.pop(0)
    logger.info(">>>> 开始处理 %s", current_pkg)

    # 构造子状态（复用原来的图）
    sub_state: AgentState = {
        "archive_path": current_pkg,
        "extract_to": tempfile.mkdtemp(),
        "files": [],
        "classified": [],
        "report": "",
        "grouped": {},
        "group_keys": [],
        # 下面 3 个字段主图用不到，但状态定义要求给空
        "scan_dir": "",
        "pkg_queue": [],
        "current_pkg": "",
    }

    from .graph import graph as single_graph  # 函数内部才拿实例，延迟导入
    sub_final = single_graph.invoke(sub_state)

    # 把子结果合并到主状态（简单示例：只累加分类结果）
    state["classified"].extend(sub_final["classified"])
    state["pkg_queue"] = queue          # 写回剩余队列
    state["current_pkg"] = current_pkg  # 记录当前包（调试用）
    return state

# ---------- 节点：解压 ----------
def node_extract(state: AgentState) -> AgentState:
    arch = state["archive_path"]
    dest_parent = state["extract_to"]
    logger.info("Start extracting %s", arch)
    extract_dir = extract_archive(arch, dest_parent)

    # 递归收集所有文件路径
    files = []
    for root, _, fs in os.walk(extract_dir):
        for f in fs:
            files.append(os.path.join(root, f))

    logger.info("Extracted %d files -> %s", len(files), extract_dir)
    # 初始化分组字段，避免后续 KeyError
    return {**state, "files": files, "extract_to": extract_dir,
            "grouped": {}, "group_keys": []}

# ---------- 节点：LLM 分类 ----------
def node_classify(state: AgentState) -> AgentState:
    files = state["files"]
    logger.info("Classifying %d files", len(files))
    classified = []
    for f in files:
        try:
            res = classify_file(f)        # 调用 LLM
            res["file_path"] = f
            classified.append(res)
        except Exception:
            logger.exception("classify failed: %s", f)
            classified.append({"type": "unknown", "language": "",
                               "confidence": 0, "file_path": f})
    logger.info("Classified done")
    return {**state, "classified": classified}

# ---------- 节点：分组 ----------
def node_dispatch(state: AgentState) -> AgentState:
    grouped: Dict[str, List[str]] = {}
    for item in state["classified"]:
        t = item["type"]
        grouped.setdefault(t, []).append(item["file_path"])
    logger.info("Dispatch groups: %s", list(grouped.keys()))
    return {**state, "grouped": grouped,
            "group_keys": list(grouped.keys())}

# ---------- 节点：代码后处理 ----------
def node_post_code(state: AgentState) -> AgentState:
    files = state.get("grouped", {}).get("code", [])
    if files:
        logger.info("Post-process %d code files", len(files))
        format_code_batch(files)
    return state

# ---------- 节点：文档后处理 ----------
def node_post_doc(state: AgentState) -> AgentState:
    files = state.get("grouped", {}).get("doc", [])
    if files:
        logger.info("Post-process %d doc files", len(files))
        doc_to_txt_batch(files)
    return state