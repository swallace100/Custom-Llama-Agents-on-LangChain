### Compile the requirements files

```bash
pip-compile apps/api/requirements.in        -o apps/api/requirements.txt
pip-compile packages/agents/requirements.in -o packages/agents/requirements.txt
pip-compile packages/tools/requirements.in  -o packages/tools/requirements.txt
pip-compile packages/memory/requirements.in -o packages/memory/requirements.txt
pip-compile packages/evals/requirements.in  -o packages/evals/requirements.txt
pip-compile requirements-dev.in             -o requirements-dev.txt

```

## Install exactly the locked dependencies

```bash
pip install -r apps/api/requirements.txt
pip install -r packages/agents/requirements.txt
pip install -r packages/tools/requirements.txt
pip install -r packages/memory/requirements.txt
pip install -r packages/evals/requirements.txt
pip install -r requirements-dev.txt

```

### Implement Pre-commmit and Pre-commit install

```bash
python -m venv .venv
pip install pre-commit black ruff mypy
pre-commit install

```

### Run Docker

```bash
docker-compose -f docker-compose.dev.yml up --build

```

```powershell
### Compile a requirements.in
python -m piptools compile requirements.in -o requirements.txt
```

### Data Set commands

Validate eval data sets

```bash
python packages/evals/datasets/tools/validate.py \
  packages/evals/datasets/researcher.jsonl \
  packages/evals/datasets/writer.jsonl \
  packages/evals/datasets/editor.jsonl

```

```bash
Build per-role training files (chat format)
# researcher
python packages/evals/datasets/tools/to_trl.py \
  packages/evals/datasets/out/researcher.chat.jsonl \
  packages/evals/datasets/researcher.jsonl

# writer
python packages/evals/datasets/tools/to_trl.py \
  packages/evals/datasets/out/writer.chat.jsonl \
  packages/evals/datasets/writer.jsonl

# editor
python packages/evals/datasets/tools/to_trl.py \
  packages/evals/datasets/out/editor.chat.jsonl \
  packages/evals/datasets/editor.jsonl
```

Train LoRA adapters (maps to your three agents)

- Use your packages/evals/lora-minimal/train_lora.py and point to each \*.chat.jsonl.

- Output to the adapters that your service loads:

```bash
# agent_a = researcher
python packages/evals/lora-minimal/train_lora.py \
  --base_model microsoft/phi-3-mini-4k-instruct \
  --data_path packages/evals/datasets/out/researcher.chat.jsonl \
  --output_dir apps/llm_host_py/adapters/agent_a

# agent_b = writer
python packages/evals/lora-minimal/train_lora.py \
  --data_path packages/evals/datasets/out/writer.chat.jsonl \
  --output_dir apps/llm_host_py/adapters/agent_b

# agent_c = editor
python packages/evals/lora-minimal/train_lora.py \
  --data_path packages/evals/datasets/out/editor.chat.jsonl \
  --output_dir apps/llm_host_py/adapters/agent_c

```

Then rester the container

```bash
docker compose -f docker-compose.dev.yml restart llm
# logs should say: [LLM] Loaded adapters: agent_a, agent_b, agent_c

```

## JSON to JSONL converter

```powershell
python packages/evals/datasets/tools/convert_any_to_jsonl.py `
  packages/evals/datasets/editor.json `
  packages/evals/datasets/editor.jsonl
```
