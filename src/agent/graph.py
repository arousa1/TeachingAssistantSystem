"""
LangGraph 工作流定义文件

拓扑： extract → classify → dispatch ─┬─→ post_code
                                     └─→ post_doc
条件边根据 group_keys 决定走向，支持后续无限扩展。
"""
from langgraph.graph import StateGraph, END
from .nodes import (
    node_extract, node_classify, node_dispatch,
    node_post_code, node_post_doc
)
from .state import AgentState

# 1. 创建状态图实例
workflow = StateGraph(AgentState)

# 2. 添加节点（名字随意，但后续映射要保持一致）
workflow.add_node("extract",   node_extract)   # 解压
workflow.add_node("classify",  node_classify)  # LLM 识别
workflow.add_node("dispatch",  node_dispatch)  # 分组
workflow.add_node("post_code", node_post_code) # 代码后处理
workflow.add_node("post_doc",  node_post_doc)  # 文档后处理

# 3. 普通边：顺序执行
workflow.add_edge("extract", "classify")
workflow.add_edge("classify", "dispatch")

# 4. 条件边：根据分组键并行触发
#    函数返回 str，必须在映射字典里存在
workflow.add_conditional_edges(
    "dispatch",
    lambda s: s["group_keys"][0] if s.get("group_keys") else "end",
    {
        "code": "post_code",
        "doc":  "post_doc",
        "end":  END,      # 兜底，无文件时直接结束
    }
)

# 5. 各后处理节点统一回到 END
workflow.add_edge("post_code", END)
workflow.add_edge("post_doc",  END)

# 6. 设定入口
workflow.set_entry_point("extract")

# 7. 编译成可执行对象
graph = workflow.compile()

# from IPython.display import Image,display
# display(Image(graph.get_graph().draw_mermaid_png()))