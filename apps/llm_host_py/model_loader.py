# apps/llm_host_py/model_loader.py
import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

BASE = "microsoft/phi-3-mini-4k-instruct"
ADAPTERS_DIR = os.getenv("ADAPTERS_DIR", "/app/adapters")
ADAPTER_NAMES = ["agent_a", "agent_b", "agent_c"]

bnb = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=(
        torch.bfloat16 if torch.cuda.is_available() else torch.float16
    ),
)

_tok = AutoTokenizer.from_pretrained(BASE, use_fast=True)
_tok.pad_token = _tok.eos_token

_base = AutoModelForCausalLM.from_pretrained(
    BASE, quantization_config=bnb, device_map="auto"
)


def _adapter_path(name: str) -> str:
    return os.path.join(ADAPTERS_DIR, name)


def _has_adapter(name: str) -> bool:
    return os.path.isfile(os.path.join(_adapter_path(name), "adapter_config.json"))


# Collect available adapters
_available = [n for n in ADAPTER_NAMES if _has_adapter(n)]

if _available:
    first = _available[0]
    _model = PeftModel.from_pretrained(_base, _adapter_path(first), adapter_name=first)
    for n in _available[1:]:
        _model.load_adapter(_adapter_path(n), adapter_name=n)
    print(f"[LLM] Loaded adapters: {', '.join(_available)}")
else:
    _model = _base
    print("[LLM] No adapters found; running base model only.")


def generate(
    prompt: str,
    adapter: str | None,
    max_new_tokens: int = 256,
    temperature: float = 0.7,
) -> str:
    if isinstance(_model, PeftModel) and adapter in _available:
        _model.set_adapter(adapter)
    inputs = _tok(prompt, return_tensors="pt").to(_model.device)
    with torch.inference_mode():
        out = _model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=temperature,
        )
    return _tok.decode(out[0], skip_special_tokens=True)
