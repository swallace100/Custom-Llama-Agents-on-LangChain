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
.\.venv\Scripts\Activate
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

- Max steps should be set between 200 and 500 for better results. 50 steps is too little.

- Output to the adapters that your service loads:

```bash
# agent_researcher
python packages/train/train_lora.py `
  --base_model microsoft/phi-3-mini-4k-instruct `
  --data_path packages/evals/datasets/researcher.jsonl `
  --output_dir apps/llm_host_py/adapters/agent_researcher `
  --max_steps 300 `
  --batch_size 1 `
  --grad_accum 16

# agent_writer
python packages/train/train_lora.py `
  --base_model microsoft/phi-3-mini-4k-instruct `
  --data_path packages/evals/datasets/writer.jsonl `
  --output_dir apps/llm_host_py/adapters/agent_writer `
  --max_steps 300 `
  --batch_size 1 `
  --grad_accum 16

# agent_editor
python packages/train/train_lora.py `
  --base_model microsoft/phi-3-mini-4k-instruct `
  --data_path packages/evals/datasets/editor.jsonl `
  --output_dir apps/llm_host_py/adapters/agent_editor `
  --max_steps 300 `
  --batch_size 1 `
  --grad_accum 16


```

Then restart the container

```bash
docker compose -f docker-compose.dev.yml restart llm
# logs should say: [LLM] Loaded adapters: agent_a, agent_b, agent_c

```

Evaluate the newly trained agent

```bash
python packages/evals/run_eval.py \
  --model lora:agent_researcher \
  --data packages/evals/datasets/researcher.jsonl \
  --out out/evals/researcher_lora.jsonl
```

Then score it

```bash
python packages/evals/score.py `
  --base out/evals/researcher_base.jsonl `
  --lora out/evals/researcher_lora.jsonl `
  --report out/evals/researcher_report.md

```

## JSON to JSONL converter

```powershell
python packages/evals/score.py --ref out/evals/researcher_base.jsonl --pred out/evals/researcher_lora.jsonl --report out/evals/researcher_report.md

```

## Setup GPU

Check if GPU is visible. Run this PowerShell script in venv:

```powershell
python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.device_count()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'No CUDA')"

```

Expected result

```yaml
True
1
NVIDIA GeForce RTX 3060 (or whatever GPU you have)
```

### Install the correct PyTorch build

```powershell
pip uninstall torch torchvision torchaudio -y
pip cache purge
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

```

### Install bitsandbytes

```powershell
pip install bitsandbytes

```
