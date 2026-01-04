"""
批量处理入口
python batch_main.py --dir D:\downloads\pkgs
"""
import argparse, os, dotenv
from src.agent.batch_graph import batch_graph
from src.agent.state import AgentState

dotenv.load_dotenv()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", required=True, help="包含压缩包的文件夹")
    args = parser.parse_args()

    state: AgentState = {
        "scan_dir": os.path.abspath(args.dir),
        "pkg_queue": [],
        "current_pkg": "",
        # 其余字段初始空
        "archive_path": "",
        "extract_to": "",
        "files": [],
        "classified": [],
        "report": "",
        "grouped": {},
        "group_keys": [],
    }

    final = batch_graph.invoke(state)
    print(f"处理完成！共识别 {len(final['classified'])} 个文件")
    for item in final["classified"]:
        print(f"  {item['file_path']} -> {item['type']}")

if __name__ == "__main__":
    main()