from langgraph.graph import StateGraph, END
from .nodes import node_extract, node_classify, node_dispatch, node_post_code, node_post_doc
from .state import AgentState

# 创建图
workflow = StateGraph(AgentState)

# 添加节点
workflow.add_node("extract",   node_extract)
workflow.add_node("classify",  node_classify)
workflow.add_node("dispatch",  node_dispatch)
workflow.add_node("post_code", node_post_code)
workflow.add_node("post_doc",  node_post_doc)

# 连接
workflow.add_edge("extract", "classify")
workflow.add_edge("classify", "dispatch")

# 条件边：按类型分发
workflow.add_conditional_edges(
    "dispatch",
    lambda s: s["group_keys"][0] if s.get("group_keys") else "end",
    {
        "code": "post_code",
        "doc":  "post_doc",
        "end":  END,
    }
)

workflow.add_edge("post_code", END)
workflow.add_edge("post_doc",  END)

workflow.set_entry_point("extract")

graph = workflow.compile()