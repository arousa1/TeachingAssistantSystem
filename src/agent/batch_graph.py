"""
批量工作流：扫描 → 逐个处理 → 结束
复用原来的单包图作为子流程
"""
from langgraph.graph import StateGraph, END
from .nodes import node_scan_dir, node_process_one
from .state import AgentState

batch_workflow = StateGraph(AgentState)

batch_workflow.add_node("scan",      node_scan_dir)
batch_workflow.add_node("process",   node_process_one)

batch_workflow.add_edge("scan", "process")

# 只要队列还有就继续处理
batch_workflow.add_conditional_edges(
    "process",
    lambda s: "process" if s["pkg_queue"] else END,
    {"process": "process", END: END}
)

batch_workflow.set_entry_point("scan")
batch_graph = batch_workflow.compile()