import dotenv
import os
from langchain_openai import ChatOpenAI

dotenv.load_dotenv()   # 把 .env 灌进环境变量

def get_llm(provider: str = "deepseek"):
    """
    provider: deepseek | qwen
    返回 LangChain BaseChatModel 实例，接口跟 ChatOpenAI 100% 一致
    """
    if provider == "deepseek":
        return ChatOpenAI(
            model="deepseek-chat",          # 或者 deepseek-coder
            base_url="https://api.deepseek.com/v1",
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            temperature=0,
            max_tokens=256,
        )
    if provider == "qwen":
        # 需要 DASHSCOPE_API_KEY
        return ChatOpenAI(
            model="qwen-max",        # 也可 qwen-max / qwen-long
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            temperature=0,
        )
    raise ValueError(f"unknown provider {provider}")