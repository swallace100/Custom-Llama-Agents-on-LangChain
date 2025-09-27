from fastapi import FastAPI

app = FastAPI(title="Custom Llama Agents API")


@app.get("/health")
def health():
    return {"ok": True}
