"""
全局状态结构声明

LangGraph 的每一个节点都会接收 & 返回这个 TypedDict，
因此所有字段必须提前声明，避免 KeyError。
"""
from typing import List, Dict, TypedDict

class AgentState(TypedDict):
    archive_path: str          # 原始压缩包绝对路径
    extract_to: str            # 解压后根目录
    files: List[str]           # 解压出的所有文件完整路径
    classified: List[dict]     # 每个文件的 LLM 分类结果
    report: str                # 给人看的简要报告（可扩展）
    grouped: Dict[str, List[str]]  # 按类型分组 {type: [path, ...]}
    group_keys: List[str]      # 分组键列表，供条件边使用