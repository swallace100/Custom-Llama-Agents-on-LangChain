import argparse
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

ap = argparse.ArgumentParser()
ap.add_argument("--base_model", required=True)
ap.add_argument("--adapter_dir", required=True)
ap.add_argument("--prompt", required=True)
ap.add_argument("--max_new_tokens", type=int, default=256)
args = ap.parse_args()

bnb = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=(
        torch.bfloat16 if torch.cuda.is_available() else torch.float16
    ),
)

tok = AutoTokenizer.from_pretrained(args.base_model, use_fast=True)
tok.pad_token = tok.eos_token
base = AutoModelForCausalLM.from_pretrained(
    args.base_model, quantization_config=bnb, device_map="auto"
)
model = PeftModel.from_pretrained(base, args.adapter_dir)

inputs = tok(args.prompt, return_tensors="pt").to(model.device)
with torch.inference_mode():
    out = model.generate(
        **inputs, max_new_tokens=args.max_new_tokens, do_sample=True, temperature=0.7
    )
print(tok.decode(out[0], skip_special_tokens=True))
