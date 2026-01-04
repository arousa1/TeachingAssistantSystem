"""
解压工具封装

支持 zip/rar/7z/tar 等，底层用 pyunpack + patool，
Windows 需提前安装 7-Zip 或 WinRAR 并加入 PATH。
"""
# import os
# import uuid
# from pyunpack import Archive
#
# def extract_archive(file_path: str, dest_parent: str) -> str:
#     """
#     :param file_path: 压缩包绝对路径
#     :param dest_parent: 解压到哪个目录
#     :return: 实际解压目录（含随机子目录，防冲突）
#     """
#     dest = os.path.join(dest_parent, uuid.uuid4().hex)
#     os.makedirs(dest, exist_ok=True)
#     Archive(file_path).extractall(dest)
#     return dest

"""
解压工具（内嵌 7-Zip，不依赖系统 PATH）
"""
import subprocess
import uuid
from pathlib import Path

# 1. 先拿到本文件所在目录
_HERE = Path(__file__).parent.resolve()
# 2. 再拼 bin 子目录
_7Z_EXE = _HERE / "bin" / "7z.exe"

def extract_archive(file_path: str, dest_parent: str) -> str:
    dest = Path(dest_parent) / uuid.uuid4().hex
    dest.mkdir(parents=True, exist_ok=True)

    cmd = [
        str(_7Z_EXE),      # 绝对路径调用
        "x",
        f"-o{dest}",
        "-y",
        file_path,
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"7-Zip 解压失败: {e.stderr}") from e

    return str(dest)