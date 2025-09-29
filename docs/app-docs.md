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
