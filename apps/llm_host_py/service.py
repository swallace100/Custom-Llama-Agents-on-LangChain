# apps/llm_host_py/service.py (snippet)
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Literal, Optional, Any, Dict
from model_loader import generate

app = FastAPI(title="LLM Host (Phi-3 + LoRA)")


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    model: str = "microsoft/phi-3-mini-4k-instruct"
    messages: List[ChatMessage]
    temperature: float = 0.7
    max_tokens: int = 256
    adapter: Optional[str] = None  # <-- add this


def join_messages(msgs: List[ChatMessage]) -> str:
    lines = []
    for m in msgs:
        prefix = {"system": "System", "user": "User", "assistant": "Assistant"}[m.role]
        lines.append(f"{prefix}: {m.content}")
    lines.append("Assistant:")
    return "\n".join(lines)


@app.post("/v1/chat/completions")
def chat_completions(body: ChatRequest) -> Dict[str, Any]:
    prompt = join_messages(body.messages)
    text = generate(
        prompt,
        adapter=body.adapter,  # <-- switch per request
        max_new_tokens=body.max_tokens,
        temperature=body.temperature,
    )
    import time

    return {
        "id": "chatcmpl-local-phi3",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": body.model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": None,
            "completion_tokens": None,
            "total_tokens": None,
        },
    }
