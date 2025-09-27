from fastapi import FastAPI
from .config import settings

app = FastAPI(title="Custom Llama Agents API")


@app.get("/health")
def health():
    return {"ok": True, "env": settings.env, "llama_url": settings.llama_server_url}
