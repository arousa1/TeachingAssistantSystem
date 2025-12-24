import base64
import os
from langchain_core.messages import SystemMessage, HumanMessage

from ..agent.llm import get_llm
from ..agent.prompts import CLASSIFY_PROMPT

model = get_llm()

def classify_file(file_path: str) -> dict:
    name = os.path.basename(file_path)
    header = b""
    try:
        with open(file_path, "rb") as f:
            header = f.read(512)
    except Exception:
        pass
    header_b64 = base64.b64encode(header).decode() if header else ""
    messages = [
        SystemMessage(content=CLASSIFY_PROMPT),
        HumanMessage(content=f"filename:{name}\nheader_base64:{header_b64}")
    ]
    # 强制 JSON
    content = model.invoke(messages).content
    import json
    return json.loads(content)