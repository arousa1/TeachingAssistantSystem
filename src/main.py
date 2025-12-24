"""
一键启动入口
"""
import argparse
import os
import sys
from dotenv import load_dotenv

# 把 src 加入路径（双击 main.py 时也能找到模块）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.graph import graph
from agent.state import AgentState

load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="AI 自动解压 + 文件分类 Agent")
    parser.add_argument("--zip", required=True, help="zip/rar 压缩包路径")
    args = parser.parse_args()

    state: AgentState = {
        "archive_path": os.path.abspath(args.zip),
        "extract_to": os.path.join(os.getcwd(), "tmp"),
        "files": [],
        "classified": [],
        "report": "",
    }

    final_state = graph.invoke(state)
    print(final_state["report"])
    return 0

if __name__ == "__main__":
    raise SystemExit(main())