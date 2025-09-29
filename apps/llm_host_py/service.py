from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Literal
from router import pick_adapter
from model_loader import generate

app = FastAPI(title="LLM Host (Phi-3 + LoRA)", version="0.2.0")


# --- OpenAI-compatible /v1/chat/completions ---
class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    model: str = "microsoft/phi-3-mini-4k-instruct"  # accepted but ignored for now
    messages: List[ChatMessage]
    temperature: float = 0.7
    max_tokens: int = 256


def join_messages(msgs: List[ChatMessage]) -> str:
    # Simple chat-to-prompt conversion; keep it minimal
    lines = []
    for m in msgs:
        prefix = {"system": "System", "user": "User", "assistant": "Assistant"}[m.role]
        lines.append(f"{prefix}: {m.content}")
    lines.append("Assistant:")
    return "\n".join(lines)


@app.post("/v1/chat/completions")
def chat_completions(body: ChatRequest):
    # Optional: route adapters by a simple heuristic on the last user message
    last_user = next(
        (m.content for m in reversed(body.messages) if m.role == "user"), ""
    )
    adapter = pick_adapter(
        last_user
    )  # or parse body.model suffix for adapter selection
    prompt = join_messages(body.messages)
    text = generate(
        prompt,
        adapter=adapter,
        max_new_tokens=body.max_tokens,
        temperature=body.temperature,
    )

    return {
        "id": "chatcmpl-local-phi3",
        "object": "chat.completion",
        "created": __import__("time").int(time := __import__("time").time()),
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


# Keep your simple health too
@app.get("/health")
def health():
    return {"ok": True}
