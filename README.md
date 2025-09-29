# Custom-Phi-3-Agents-on-LangChain

Monorepo for Phi-3-trained specialist agents orchestrated by LangChain.
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
- `apps/llm_host_py`: Base LLM model and LoRA adapters
- `infra/`: Dockerfiles & compose

### Reproducible installs

- Edit `*.in`, then run `make lock` to update the pinned `requirements.txt`.
- Install exact versions with `make sync` (or `make install-all` on a fresh clone).

## 🚀 Running with LLMs

### Option A: Local (Phi-3 mini 3.8B, 4-bit)

1. Ensure NVIDIA drivers + nvidia-container-toolkit are installed (for GPU in Docker).
   If you’d rather skip Docker for now, see “Run without Docker” below.
2. Copy .env.example → .env and keep the Local Phi-3 block:

   ```env
   LLM_PROVIDER=phi3
   LLM_BASE_URL=http://localhost:7001
   LLM_MODEL=microsoft/phi-3-mini-4k-instruct
   LLM_TEMPERATURE=0.2
   LLM_CONTEXT=4096

   ```

3. Start the Phi-3 host (loads base once; switch LoRA adapters as needed):

   ```bash
      # with docker-compose (recommended)
      docker compose up -d llm

   ```

4. Run the API (and demo if you use it):

   ```bash
      make api
      # optionally
      make demo

   ```

#### Run without Docker (dev mode):

```bash
cd apps/llm_host_py
pip install -r requirements.txt
uvicorn service:app --host 0.0.0.0 --port 7001
# in another terminal:
make api

```

#### Notes:

- This works comfortably with 8 GB VRAM: Phi-3 mini in 4-bit is the target.

- LoRA adapters live in apps/llm_host_py/adapters/\* and can be hot-swapped without changing .env.

- Keep requests sequential (batch size 1, modest max_new_tokens) for smooth VRAM usage.

### Cloud (OpenAI )

1. Copy `.env.example` → `.env`.
2. Uncomment the Cloud section and set your API key.
3. Run:

```bash
   make api
```
