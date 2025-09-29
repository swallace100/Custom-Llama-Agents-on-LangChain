import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

BASE = "microsoft/phi-3-mini-4k-instruct"

bnb = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
)

_tok = AutoTokenizer.from_pretrained(BASE, use_fast=True)
_tok.pad_token = _tok.eos_token

_base = AutoModelForCausalLM.from_pretrained(
    BASE, quantization_config=bnb, device_map="auto"
)
_model = PeftModel.from_pretrained(
    _base, "apps/llm_host_py/adapters/agent_a", adapter_name="agent_a"
)
_model.load_adapter("apps/llm_host_py/adapters/agent_b", adapter_name="agent_b")
_model.load_adapter("apps/llm_host_py/adapters/agent_c", adapter_name="agent_c")


def generate(
    prompt: str, adapter: str, max_new_tokens: int = 256, temperature: float = 0.7
) -> str:
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
