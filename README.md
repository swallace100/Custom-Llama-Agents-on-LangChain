# Custom-Llama-Agents-on-LangChain

Monorepo for Llama-trained specialist agents orchestrated by LangChain.
See `/packages` for Python libraries, `/apps/api` for the FastAPI service, and `/apps/demo` for the UI.

## Quickstart

1. Copy `.env.example` to `.env` and fill keys as needed.
2. Install deps:
   - Python: `uv sync -p apps/api` etc. or `make setup`
   - JS: `pnpm install --recursive`
3. Run API: `make py-dev` (http://localhost:8080/health)
4. Run Demo: `make js-dev` (http://localhost:5173 or 8085 preview)

## Structure

- `packages/agents`: Agent roles + prompts + typed I/O
- `packages/tools`: Tool adapters (web, repo, shell)
- `packages/memory`: Short/long memory & vector store
- `packages/evals`: Evaluation tasks & test harness
- `apps/api`: Orchestration service
- `apps/demo`: React/Vite demo UI
- `infra/`: Dockerfiles & compose

### Reproducible installs

- Edit `*.in`, then run `make lock` to update the pinned `requirements.txt`.
- Install exact versions with `make sync` (or `make install-all` on a fresh clone).

## 🚀 Running with LLMs

### Option A: Local (Ollama + Llama 3 8B)

1. Install [Ollama](https://ollama.ai).
2. Pull the model:
   ```bash
   ollama pull llama3:8b-instruct-q4_K_M
   ```
3. Copy `.env.example` → `.env` and leave the Ollama block uncommented.

4. Run:

```bash
   make api
```

### Cloud (OpenAI / hosted LLaMA)

1. Copy `.env.example` → `.env`.
2. Uncomment the Cloud section and set your API key.
3. Run:

```bash
   make api
```
