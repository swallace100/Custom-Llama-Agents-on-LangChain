# LLM Choice & Inference Plan

## Goals

- Agents: Researcher / Writer / Editor (tool use, retrieval, planning)
- Constraints: <$X/day infra, single-GPU dev, easy local reproducibility
- Latency target: P50 <= 1.5s for 256-token outputs

## Deployment Modes (Provider Toggle)

We support both local Phi-3 inference and hosted APIs via a simple .env switch:

- Local (Phi-3 mini host, 4-bit QLoRA):

  - Reproducible offline dev.

  - Uses Microsoft Phi-3 mini 3.8B Instruct with quantization.

  - Best for hacking, testing LangChain agents, and demos without API costs.

- Cloud (OpenAI-compatible APIs):

  - Swap to OpenAI (e.g. gpt-4o-mini, gpt-4-turbo) or other hosted providers (Together, Fireworks, Groq).

  - Provides larger contexts, stronger guardrails, and scales without GPU management.

  - Costs $/token, but avoids infra overhead.

- Implementation:

  - All LangChain agents pull make_chat_llm() from packages/agents/llm_client.py.

  - Provider is chosen via .env:

    ```dotenv
    LLM_PROVIDER=openai   # or phi3
    ```

## Candidate Models

- Phi-3 mini 3.8B Instruct — default baseline (fast, cheap, MIT license)
- (Optional tiny) Phi-3 small (1.4B) — edge/CPU, ultra-lightweight, lower quality
- Cloud: GPT-4o-mini / GPT-4-turbo for higher quality

> Model cards + licenses will be tracked under `docs/licenses/`.

## Context Window

- Default: 4k (Phi-3 mini) is enough for most agent steps.
- Cloud mode: 8k–32k+ depending on model.
- Note: larger context ⇒ bigger KV cache ⇒ more VRAM and slower.

## Quantization & Memory Rough-cuts

Rule of thumb (params × bytes/param, excluding KV cache):

- BF16/FP16 ≈ 2 B/param → 3.8B ≈ ~8 GB
- 8-bit ≈ 1 B/param → 3.8B ≈ ~4 GB
- 4-bit ≈ 0.5 B/param → 3.8B ≈ ~2 GB

KV cache adds ~2× hidden size × layers × sequence length (per batch).
Long contexts or big batch sizes can dominate VRAM.

## Backends

- Dev (simple): Our own FastAPI `llm_host_py` service (Phi-3 mini + LoRA adapters, OpenAI-compatible endpoint).
- CPU (optional): `transformers` with 4-bit quantization.
- Prod GPU: vLLM (paged attention, high throughput) if scaling beyond a single GPU.
- Alt GPU: TGI (Hugging Face Text-Generation-Inference), TensorRT-LLM (NVIDIA).

## Our Choice (initial)

- Model: Model: Microsoft Phi-3 mini 3.8B Instruct (MIT license).
- Quantization:
  - Dev laptop (RTX 4070 8 GB): 4-bit QLoRA
  - GPU server: 8-bit or 4-bit via vLLM or TGI
- Context: 4k (default); revisit longer contexts only if required.
- Backend:
  - Local: FastAPI `llm_host_py` (OpenAI-compatible).
  - Cloud: OpenAI APIs for production-grade scaling.

## Inference Endpoints (reference)

### Local (Phi-3 mini host)

- Run via Docker Compose:
  - `ollama pull llama3:8b-instruct` # (exact tag per registry)

```bash
docker compose up -d llm
```

- Provides OpenAI-compatible API at:

```bash
POST http://localhost:7001/v1/chat/completions
```

### vLLM (GPU)

Example service:

```yaml
llm:
  image: vllm/vllm-openai:latest
  command: >
    --model /models/phi-3-mini-4k-instruct
    --dtype auto
    --gpu-memory-utilization 0.9
    --max-model-len 4096
  volumes:
    - ./models/phi-3-mini-4k-instruct:/models/phi-3-mini-4k-instruct
  ports: ["8000:8000"]
  environment:
    - VLLM_WORKER_MULTIPROC_METHOD=spawn
    - TRANSFORMERS_CACHE=/models
```

- Query like OpenAI:
  - `POST http://localhost:8000/v1/chat/completions`

## Evals & Guardrails

- Run basic evals on internal prompts before flipping models:

  - Quality: research, plan, code task pool

  - Cost/latency: tokens/s, latency P50/P95

  - Safety: jailbreak/PII prompts, blocked tool calls

- Keep eval harness in `packages/evals/` and record results in this doc.

## License Notes

- Phi-3 models are released under the MIT License

- If we later include Llama or other models, their licenses must also be included under docs/licenses/.

## Decision

- dopt Phi-3 mini 3.8B as default dev model.

- Backends:

  - Local: llm_host_py (OpenAI-compatible FastAPI).

  - Cloud: OpenAI GPT-4o-mini or GPT-4-turbo.

- Revisit larger models (e.g., GPT-4 family, Qwen, Mixtral) if quality gaps emerge.

### Dual Strategy

- Default Dev: Phi-3 mini 3.8B locally (cheap/free, reproducible).

- Optional Cloud: Any OpenAI-compatible model (e.g. GPT-4o, GPT-4-turbo).

- This makes it easy for contributors to clone the repo, run agents locally without paying, and still demonstrate parity with production-grade APIs.

## Open Questions / Next Checkpoint

- Do our agents require >4k context in practice?

- Which quantization (4-bit vs 8-bit) gives best latency/quality tradeoff?

- Budget target per day for sustained usage?
