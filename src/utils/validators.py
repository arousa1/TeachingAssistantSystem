"""
预留：参数校验、路径白名单等
"""
import os

def safe_path(path: str, base: str) -> bool:
    """简单防目录穿越"""
    return os.path.abspath(path).startswith(os.path.abspath(base))