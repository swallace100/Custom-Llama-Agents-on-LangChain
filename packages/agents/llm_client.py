from __future__ import annotations

import os

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

# Try to import ChatOllama from either langchain-ollama or langchain-community
try:
    from langchain_ollama import ChatOllama
except Exception:
    try:
        from langchain_community.chat_models import ChatOllama
    except Exception:
        ChatOllama = None


def make_chat_llm() -> BaseChatModel:
    """Return a Chat LLM based on env: OpenAI-compatible or Ollama."""
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    base_url = os.getenv("LLM_BASE_URL")
    api_key = os.getenv("LLM_API_KEY", "none")
    model = os.getenv("LLM_MODEL", "llama3:8b-instruct-q4_K_M")
    context = int(os.getenv("LLM_CONTEXT", "4096"))
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.2"))

    if provider == "openai":
        # Works with OpenAI or any OpenAI-compatible endpoint
        return ChatOpenAI(
            model=model,
            base_url=base_url,
            api_key=api_key,
            temperature=temperature,
            max_tokens=context,
        )

    if provider == "ollama":
        if ChatOllama is None:
            raise ImportError(
                "Ollama support requires 'langchain-ollama' (preferred) or "
                "'langchain-community'. Install with:\n"
                "  pip install langchain-ollama\n"
                "or\n"
                "  pip install langchain-community"
            )
        # ChatOllama params differ slightly from OpenAI’s
        return ChatOllama(model=model, temperature=temperature, num_ctx=context)

    raise ValueError(f"Unsupported LLM_PROVIDER={provider}")
