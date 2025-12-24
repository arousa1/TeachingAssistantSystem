"""
示例后续处理节点
"""
import subprocess
import os
from ..utils.logger import get_logger

logger = get_logger(__name__)

def format_code_batch(files: list[str]):
    """black 格式化 Python；其它语言可扩展"""
    py_files = [f for f in files if f.endswith(".py")]
    if py_files:
        try:
            subprocess.run(["black"] + py_files, check=True)
            logger.info("black formatted %d files", len(py_files))
        except FileNotFoundError:
            logger.warning("black not found, skip")

def doc_to_txt_batch(files: list[str]):
    """pdf→txt 简单示例；生产可用 pdfplumber 等"""
    for f in files:
        if f.lower().endswith(".pdf"):
            txt = f[:-4] + ".txt"
            try:
                subprocess.run(["pdftotext", f, txt], check=True)
            except FileNotFoundError:
                logger.warning("pdftotext not found, skip %s", f)