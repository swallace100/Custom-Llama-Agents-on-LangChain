Milestone 0 — Project scaffolding

Initialize monorepo (apps + packages)
Why: Keep agents, backend, and evals cleanly separated.
DoD: pnpm/npm workspaces (or uv/pip/poetry) set up; folders: apps/api, apps/demo, packages/agents, packages/tools, packages/memory, packages/evals, infra/.

Base Python env + lockfile
Why: Reproducible builds.
DoD: pyproject.toml (or requirements.txt), pinned versions, make setup.

Code style + pre-commit
Why: Consistency.
DoD: black/ruff/isort/mypy + pre-commit hooks passing.

.env management & secrets policy
Why: Safe config.
DoD: .env.example, config loader, no secrets in repo.

Docker dev images
Why: Easy spin-up.
DoD: Dockerfiles for api and demo, docker-compose.dev.yml runs locally.

Milestone 1 — Data & model setup (Phi-3)

Choose base LLM + license notes
Why: Legal/size/VRAM constraints.
DoD: decision doc (quantization, context window, inference backend).

LoRA finetune pipeline (minimal)
Why: Specialize agents cheaply.
DoD: script/notebook to run LoRA on tiny curated set; saves adapters; README.

Dataset curation v1
Why: Make “Researcher/Planner/Coder” actually good.
DoD: data/ with small, high-quality instruction sets per role + JSON schema.

Eval-before/after finetune
Why: Prove value.
DoD: baseline vs LoRA scores on small tasks; markdown report.

Milestone 2 — Agent design (LangChain)

Agent specs (Researcher / Planner / Coder)
Why: Clear contracts.
DoD: role docs (inputs/outputs, tools, memory use, stop conditions).

Prompt templates + structured output
Why: Deterministic IO.
DoD: Jinja templates; Pydantic/TypedDict schemas; parser tests.

Researcher agent (web/tooling stub)
Why: First working agent.
DoD: LangChain Runnable/AgentExecutor; accepts query; returns sources + notes.

Planner agent
Why: Break down work.
DoD: turns a goal into tasks w/ dependencies; JSON plan.

Coder agent
Why: Produce code patches safely.
DoD: outputs diff/patch chunks with rationale + tests to add.

Milestone 3 — Tools

Web search + fetch tool
Why: Researcher needs it.
DoD: tool with rate limiting, retries, domain allowlist, HTML→text.

Repo I/O tool (read/patch)
Why: Let Coder edit safely.
DoD: read paths, propose unified diff; never writes without guardian step.

Shell/sandbox exec tool
Why: Run tests/linters.
DoD: jailed subprocess; time/memory limits; returns stdout/stderr/exit code.

Vector memory tool (RAG)
Why: Persist context.
DoD: embedder + DB (e.g., Chroma/Weaviate/Pinecone); CRUD API.

Task tracker tool
Why: Agents update GH issues.
DoD: GitHub API wrapper to create/comment/close issues (dry-run mode).

Milestone 4 — Memory & state

Short-term scratchpad (per run)
Why: Reduce token waste.
DoD: ephemeral store keyed by run_id with truncation strategy.

Long-term memory
Why: Cross-session learning.
DoD: write important facts to vector store with tags (agent, topic, date).

Plan state machine
Why: Orchestrate safely.
DoD: finite states (plan→execute→review→done/error); JSON state persisted.

Milestone 5 — Orchestration (production style)

Coordinator graph
Why: Glue agents together.
DoD: LangChain graph (LCEL) with branching: if research gaps → loop; if tests fail → fix.

Guardrails & approvals
Why: Safety.
DoD: human-in-the-loop on risky ops (repo writes, external posts); policy file.

Cost/latency budgeter
Why: Predictable runs.
DoD: middleware measuring tokens/time; stops or degrades gracefully.

Milestone 6 — Evals

Unit evals (per agent)
Why: Prevent regressions.
DoD: pytest suite with fixture prompts + golden outputs.

End-to-end task evals
Why: Realism.
DoD: 5–10 scenario scripts (research→plan→PR) scored by automatic rubric + spot human grades.

Hallucination & citation check
Why: Trust.
DoD: checker ensuring every claim has source or is marked speculative.

Milestone 7 — API & demo

FastAPI backend
Why: Serve the graph.
DoD: /run, /status/{id}, /cancel/{id}, /cost/{id}; OpenAPI docs.

Demo UI (React/Vite)
Why: Show it off.
DoD: simple console + plan visualizer + file diff viewer; dark mode.

Streaming & progress events
Why: Good UX.
DoD: Server-sent events or websockets; step logs.

Milestone 8 — CI/CD & infra

CI (lint, typecheck, tests, smoke run)
Why: Confidence.
DoD: GitHub Actions; matrix for py versions; cache deps.

Images & compose.prod
Why: Deployable.
DoD: slim images, healthchecks, docker-compose.prod.yml.

Observability
Why: Debugging.
DoD: structured logs, request IDs, OpenTelemetry traces, basic dashboards.

Milestone 9 — Security & governance

Model & tool access controls
Why: Least privilege.
DoD: per-agent API keys/scopes; kill-switch.

Prompt/PII hygiene
Why: Compliance.
DoD: redaction for logs; opt-in data retention flags.

Milestone 10 — Docs & content

Top-level README (narrative)
Why: Recruiting/portfolio.
DoD: what/why/how, screenshots/GIFs, quickstart, roadmap.

Agent cards & tool docs
Why: Extensibility.
DoD: per-agent MD with I/O schema, examples; per-tool usage.

Repro guide for finetune
Why: Credibility.
DoD: step-by-step with hardware notes & cost.

Demo script + short video plan
Why: Launchable content.
DoD: script bullets, beats, claims; list of shots for a 2–3 min video.
