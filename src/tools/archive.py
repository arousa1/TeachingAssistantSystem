import os
import uuid
from pyunpack import Archive

def extract_archive(file_path: str, dest_parent: str) -> str:
    """返回解压后根目录"""
    dest = os.path.join(dest_parent, uuid.uuid4().hex)
    os.makedirs(dest, exist_ok=True)
    Archive(file_path).extractall(dest)
    return dest