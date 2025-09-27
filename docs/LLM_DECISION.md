# LLM Choice & Inference Plan

## Goals

- Agents: Researcher / Planner / Coder (tool use, retrieval, planning)
- Constraints: <$X/day infra, single-GPU dev, easy local reproducibility
- Latency target: P50 <= 1.5s for 256-token outputs

## Deployment Modes (Provider Toggle)

We support both local Llama inference and hosted APIs via a simple .env switch:

- Local (Ollama / llama.cpp / vLLM):

  - Reproducible offline dev.

  - Uses Meta Llama 3.x models with quantization.

  - Best for hacking and demos.

- Cloud (OpenAI-compatible APIs):

  - Swap to OpenAI (e.g. gpt-4o-mini, gpt-4-turbo) or other hosted providers (Together, Fireworks, Groq).

  - Provides larger contexts, stronger guardrails, and scales without GPU management.

  - Costs $/token, but avoids infra overhead.

- Implementation:

  - All LangChain agents pull make_chat_llm() from packages/agents/llm_client.py.

  - Provider is chosen via .env:

    ```dotenv
    LLM_PROVIDER=ollama    # or openai
    ```

## Candidate Models

- Llama 3.x Instruct 8B — baseline (good quality/cost)
- Llama 3.x Instruct 70B — higher quality, multi-GPU or heavy quant
- (Optional tiny) Llama 3.2 3B/1B — edge/CPU, lower quality

> We will keep model cards + licenses under `docs/licenses/`.

## Context Window

- Default: 8k–16k is enough for most agent steps.
- If we truly need long docs / plans: 32k–128k variants (verify model card).
- Note: larger context ⇒ larger KV cache ⇒ more VRAM and slower.

## Quantization & Memory Rough-cuts

Rule of thumb (params × bytes/param, excluding KV cache):

- BF16/FP16 ≈ 2 B/param → 8B ≈ 16 GB; 70B ≈ 140 GB
- 8-bit ≈ 1 B/param → 8B ≈ 8 GB
- 4-bit ≈ 0.5 B/param → 8B ≈ 4 GB; 70B ≈ 35 GB

KV cache adds ~2× hidden size × layers × sequence length (per batch).
Long contexts or big batch sizes can dominate VRAM.

## Backends

- Dev (simple): **Ollama** (GGUF via llama.cpp, one command, CPU/GPU)
- Dev/CPU: **llama.cpp** (fast quantized CPU/GPU, small footprint)
- Prod GPU: **vLLM** (paged attention, tensor-parallel, high throughput)
- Alt GPU: **TGI** (HF Text-Generation-Inference), **TensorRT-LLM** (NVIDIA)

## Our Choice (initial)

- Model: **Llama 3.x Instruct 8B**
- Quantization:
  - Dev laptop/CPU: **GGUF Q4_K_M** via llama.cpp/Ollama
  - GPU server (A10/A40/4090/RTX 6000): **AWQ/GPTQ 4-bit** via vLLM
  - If 24 GB+ spare VRAM: try **FP16 8B** for max quality
- Context: **8k–16k** now; revisit **32k–128k** if agents need longer chains
- Backend:
  - Local: **Ollama** (pull + run)
  - Dev/Prod GPU: **vLLM** (Docker, serves OpenAI-compatible API)

## Inference Endpoints (reference)

### Ollama (local dev)

- Install and run:
  - `ollama pull llama3:8b-instruct` # (exact tag per registry)
  - `ollama run llama3:8b-instruct`
- OpenAI-compat shim (optional): `ollama serve` + adapters

### vLLM (GPU)

Docker compose service (example):

```yaml
llm:
  image: vllm/vllm-openai:latest
  command: >
    --model /models/llama-3-8b-instruct
    --dtype auto
    --gpu-memory-utilization 0.9
    --max-model-len 8192
  volumes:
    - ./models/llama-3-8b-instruct:/models/llama-3-8b-instruct
  ports: ["8000:8000"]
  environment:
    - VLLM_WORKER_MULTIPROC_METHOD=spawn
    - TRANSFORMERS_CACHE=/models
```

- Query like OpenAI:
  - `POST http://localhost:8000/v1/chat/completions`

### llama.cpp (CPU/GPU)

- Quantize to GGUF; run:

  - `./main -m ./llama3-8b-instruct-q4_k_m.gguf -c 4096 -ngl 0` # CPU

  -`-ngl 20` to move layers to GPU if available

## Evals & Guardrails

- Run basic evals on internal prompts before flipping models:

  - Quality: simple task pool (research, plan, code)

  - Cost/latency: tokens/s, latency P50/P95, cost per 1k tokens

  - Safety: jailbreak/PII test prompts (blocked tool calls)

- Keep eval harness in `packages/evals/` and record results in this doc.

## License Notes

- Include the Meta Llama license with this repo under docs/licenses/.

- If hosting weights or derivatives, follow attribution & usage terms.

- Verify any foundation weights’ redistribution terms before publishing images.

## Decision

- Adopt Llama 3.x Instruct 8B as default.

- Backends:

  - Ollama locally, vLLM for GPU server.

- Revisit 70B after baseline evals; only promote if quality wins justify infra cost.

### Dual Strategy

- Default Dev: Llama 3.x Instruct 8B via Ollama.

- Optional Cloud: Any OpenAI-compatible model (e.g. GPT-4o, GPT-4-turbo).

- This makes it easy for contributors to clone the repo and run agents without paying for API tokens — while still showing parity with production-grade APIs.

## Open Questions / Next Checkpoint

- Do our agents require >8k context in practice?

- Which quantization gives best latency/quality on our hardware?

- Budget target per day for sustained usage?
