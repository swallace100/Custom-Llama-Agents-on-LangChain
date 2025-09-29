# 📚 Dataset Curation (Researcher / Writer / Editor)

This folder contains **small, high-quality instruction datasets** for training role-specialized adapters (LoRA).
The goal is to make our three core roles — **Researcher, Writer, Editor** — actually good by fine-tuning on carefully curated data.

---

## 🎯 Roles

- **Researcher** → Produces structured research plans, evaluations, and evidence-based outputs.
- **Writer** → Produces polished prose: product updates, announcements, docs.
- **Editor** → Refines/restructures text for clarity, brevity, or tone.

Each role has its own dataset file:

- researcher.jsonl
- writer.jsonl
- editor.jsonl

## 🗂 Schema

Each dataset is stored as **JSONL** (one JSON object per line).
The schema is defined in [`schema.json`](schema.json):

```jsonc
{
  "role": "researcher | writer | editor",
  "task_id": "string", // unique id for traceability
  "instruction": "string", // the user ask
  "context": "string|null", // optional background or docs
  "output": "string", // the target assistant reply
  "tags": ["optional", "labels"], // e.g., ["plan","tone:formal"]
  "source": "manual|synthetic|internal",
  "quality": 1, // 1..5 rating
  "notes": "string|null"
}
```

## ✅ Quality Guidelines

- Clarity: Instruction should be specific and unambiguous.
- Role consistency: Output must reflect the intended role:
- Researcher = structured plans, explicit metrics, risks.
- Writer = polished prose, clear and concise.
- Editor = rewrites for style/tone, removes redundancy.
- Length bounds: Respect word/bullet limits (e.g., “≤150 words”, “3 steps”).
- Deterministic: Avoid randomness or “it depends”.
- Provenance: Mark whether an item is manual, synthetic, or internal.
- Quality score: Only include ≥4 unless you’re testing.

## 🔧 Tools

Two helper scripts are provided in tools/:

- validate.py — Check JSON validity + schema compliance.

```bash
python tools/validate.py researcher.jsonl writer.jsonl editor.jsonl
```

- to_trl.py — Convert to TRL-compatible chat format for SFT training.

```bash
python tools/to_trl.py out/researcher.chat.jsonl researcher.jsonl
```

## 🚀 Workflow

1. Curate
   Write ~30–50 examples per role. Quality > quantity. Hand-curated first.

2. Validate
   Run validate.py before committing.

3. Convert
   Use to_trl.py to produce role-specific chat datasets.

4. Train LoRA
   Point each dataset at train_lora.py to generate adapters:

```bash
apps/llm_host_py/adapters/agent_a   # researcher
apps/llm_host_py/adapters/agent_b   # writer
apps/llm_host_py/adapters/agent_c   # editor

```

5. Deploy
   Restart the llm service — logs should show loaded adapters.

## 📌 Example

{
"role": "writer",
"task_id": "w-014",
"instruction": "Draft a 120–150 word product update announcing the new local Phi-3 mode. Tone: confident, clear; avoid jargon.",
"context": "Feature: local Phi-3 mini host; toggle in .env; works with LangChain; no API cost.",
"output": "Today we’re adding a fast, local Phi-3 mode for agents… (120–150 words, crisp paragraphs, CTA to docs)",
"tags": ["announcement","tone:confident"],
"source": "manual",
"quality": 5,
"notes": "No hype words like ‘revolutionary’."
}

## 📊 DoD (Definition of Done)

- At least 30 high-quality items per role.

- schema.json + README.md included.

- Validation + conversion scripts committed.

- Adapters can be trained and loaded without errors.
