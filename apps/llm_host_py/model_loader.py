from __future__ import annotations
import os
import glob
from typing import Dict, Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

BASE_MODEL_NAME = os.getenv("BASE_MODEL", "microsoft/phi-3-mini-4k-instruct")
ADAPTERS_DIR = os.getenv("ADAPTERS_DIR", "/app/adapters")  # set in compose

# --- Load base model (GPU if available)
_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
_tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_NAME, use_fast=True)
if _tokenizer.pad_token is None:
    _tokenizer.pad_token = _tokenizer.eos_token

_base = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL_NAME, dtype=_dtype, device_map=None
).to("cuda" if torch.cuda.is_available() else "cpu")
_base.eval()

# --- Load/attach all adapters
# We keep a dict of adapter_name -> attached peft adapter name
_adapters: Dict[str, str] = {}


def _attach_adapter(adapter_path: str, adapter_name: str) -> None:
    """
    Attach a PEFT adapter (LoRA) into the base model under a given name.
    This uses low-level state dict load so we keep one shared base.
    """
    # Create a lightweight Peft wrapper just to read its state dict/config
    tmp = PeftModel.from_pretrained(_base, adapter_path)
    # Register adapter on the shared base under `adapter_name`
    _base.load_adapter(adapter_path, adapter_name=adapter_name)
    _adapters[adapter_name] = adapter_name  # record
    # Free the temp wrapper (safetensors already read)
    del tmp


# Discover subfolders with adapter_config.json
for p in sorted(glob.glob(os.path.join(ADAPTERS_DIR, "*"))):
    cfg = os.path.join(p, "adapter_config.json")
    if os.path.isfile(cfg):
        name = os.path.basename(p)
        try:
            _attach_adapter(p, name)
            print(f"[LLM] Loaded adapter: {name} from {p}")
        except Exception as e:
            print(f"[LLM] Skipped adapter at {p}: {e}")

print(f"[LLM] Base model: {BASE_MODEL_NAME} | Adapters: {list(_adapters)}")


def set_active_adapter(name: Optional[str]) -> None:
    """
    Switch active adapter. name=None disables adapters (base-only).
    """
    if name is None:
        _base.set_adapter(None)
        return
    if name not in _adapters:
        raise ValueError(f"Unknown adapter: {name}. Available={list(_adapters)}")
    _base.set_adapter(name)


@torch.inference_mode()
def generate(
    prompt: str,
    adapter: Optional[str],
    max_new_tokens: int = 256,
    temperature: float = 0.7,
) -> str:
    set_active_adapter(adapter)
    inputs = _tokenizer(prompt, return_tensors="pt").to(_base.device)
    out = _base.generate(
        **inputs,
        do_sample=temperature > 0.0,
        temperature=temperature,
        max_new_tokens=max_new_tokens,
        pad_token_id=_tokenizer.eos_token_id,
    )
    return _tokenizer.decode(out[0], skip_special_tokens=True)
