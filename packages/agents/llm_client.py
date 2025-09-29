# llm_client.py (no phi3 branch needed)
from langchain_openai import ChatOpenAI
import os


def make_chat_llm():
    return ChatOpenAI(
        model=os.getenv("LLM_MODEL", "microsoft/phi-3-mini-4k-instruct"),
        base_url=os.getenv(
            "LLM_BASE_URL", "http://localhost:7001"
        ),  # points to local Phi-3 host or OpenAI
        api_key=os.getenv("LLM_API_KEY", "none"),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.2")),
        max_tokens=int(os.getenv("LLM_CONTEXT", "4096")),
    )
