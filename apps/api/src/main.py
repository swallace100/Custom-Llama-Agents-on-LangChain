from fastapi import FastAPI
from .config import settings

app = FastAPI(title="Custom Phi-3 Agents API")


@app.get("/health")
def health():
    return {
        "ok": True,
        "env": settings.env,
        "llm_provider": settings.llm_provider,
        "llm_base_url": settings.llm_base_url,
        "llm_model": settings.llm_model,
    }
