#!/usr/bin/env python3
"""
Minimal, robust LoRA trainer for Phi-3 mini.

- Auto-detects bitsandbytes/CUDA; falls back to torch AdamW if unavailable.
- Auto-names adapter dir from dataset role: apps/llm_host_py/adapters/agent_<role>
- Expects dataset lines with: instruction, (optional) context, output
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Dict, Any

import torch
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer

# bitsandbytes is optional
try:
    from transformers import BitsAndBytesConfig
except Exception:
    BitsAndBytesConfig = None

from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer, SFTConfig


def bnb_available() -> bool:
    if not torch.cuda.is_available():
        return False
    if BitsAndBytesConfig is None:
        return False
    try:
        import bitsandbytes as _  # noqa: F401
    except Exception:
        return False
    return True


def guess_role_from_data(data_path: str) -> str:
    p = Path(data_path)
    with p.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                ex = json.loads(line)
                role = str(ex.get("role", "unknown")).strip() or "unknown"
                return f"agent_{role}"
    return "agent_unknown"


def build_prompt(ex: Dict[str, Any]) -> Dict[str, str]:
    """Return a single string field 'text' (prompt + reference)."""
    inst = ex.get("instruction", "") or ""
    ctx = ex.get("context", "") or ""
    out = ex.get("output", "") or ""
    parts = [f"Instruction: {inst}"]
    if ctx:
        parts.append(f"Context: {ctx}")
    parts.append("Answer:")
    # Combine into ONE string (prompt + gold answer)
    text = "\n\n".join(parts) + " " + out
    return {"text": text}  # ✅ always a plain str


def formatting_func(batch: Dict[str, Any]) -> list[str]:
    """Force TRL to always get list[str]."""
    texts = batch["text"]
    if isinstance(texts, list):
        return [str(t) for t in texts]
    return [str(texts)]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--base_model", required=True, help="e.g. microsoft/phi-3-mini-4k-instruct"
    )
    ap.add_argument("--data_path", required=True, help="Path to JSONL dataset")
    ap.add_argument(
        "--output_dir", default=None, help="Defaults to adapters/agent_<role>"
    )
    ap.add_argument("--max_steps", type=int, default=300)
    ap.add_argument("--batch_size", type=int, default=2)
    ap.add_argument("--grad_accum", type=int, default=8)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--lora_r", type=int, default=16)
    ap.add_argument("--lora_alpha", type=int, default=32)
    ap.add_argument("--lora_dropout", type=float, default=0.05)
    args = ap.parse_args()

    if args.output_dir is None:
        role_name = guess_role_from_data(args.data_path)
        args.output_dir = f"apps/llm_host_py/adapters/{role_name}"

    print(f"Training LoRA adapter → {args.output_dir}")
    print(f"- CUDA available: {torch.cuda.is_available()}")
    print(f"- bitsandbytes available: {bnb_available()}")

    # Tokenizer
    tok = AutoTokenizer.from_pretrained(args.base_model, use_fast=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    # Base model (prefer 4-bit if available)
    if bnb_available():
        bnb_cfg = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=(
                torch.bfloat16 if torch.cuda.is_available() else torch.float16
            ),
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
        )
        model = AutoModelForCausalLM.from_pretrained(
            args.base_model, quantization_config=bnb_cfg, device_map="auto"
        )
        model = prepare_model_for_kbit_training(model)
        chosen_optim = "paged_adamw_32bit"
    else:
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        model = AutoModelForCausalLM.from_pretrained(
            args.base_model, dtype=dtype, device_map="auto"
        )
        chosen_optim = "adamw_torch"

    # LoRA
    lora_cfg = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
    )
    model = get_peft_model(model, lora_cfg)

    # Data + small eval split
    raw = load_dataset("json", data_files=args.data_path, split="train")
    raw = raw.train_test_split(test_size=0.05, seed=42)

    # Ensure text is plain string
    ds_train = raw["train"].map(build_prompt, remove_columns=raw["train"].column_names)
    ds_eval = raw["test"].map(build_prompt, remove_columns=raw["test"].column_names)

    # TRL config (your TRL wants max_length; if your env supports max_seq_length, you can swap)
    cfg = SFTConfig(
        output_dir=args.output_dir,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        logging_steps=10,
        save_steps=100,
        save_total_limit=1,
        save_strategy="steps",
        max_steps=args.max_steps,
        bf16=torch.cuda.is_available(),
        optim=chosen_optim,
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        gradient_checkpointing=True,
        report_to=[],
    )

    # Build trainer; prefer dataset_text_field="text" if available
    try:
        trainer = SFTTrainer(
            model=model,
            train_dataset=ds_train,
            eval_dataset=ds_eval,
            args=cfg,
        )
    except TypeError:
        # Older/newer TRL variants: fall back to formatting_func
        trainer = SFTTrainer(
            model=model,
            train_dataset=ds_train,
            eval_dataset=ds_eval,
            formatting_func=formatting_func,
            args=cfg,
        )

    print(">>>>> Starting training...")
    trainer.train()
    print(">>>>> Saving adapter...")
    trainer.model.save_pretrained(args.output_dir)
    tok.save_pretrained(args.output_dir)
    print(f"Saved LoRA adapter to: {args.output_dir}")


if __name__ == "__main__":
    main()
