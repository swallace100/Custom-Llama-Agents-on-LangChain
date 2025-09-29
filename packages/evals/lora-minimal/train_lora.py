import argparse
import torch
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer, SFTConfig


def load_jsonl(path):
    # allow local jsonl via datasets for shuffling/splits
    return load_dataset("json", data_files=path, split="train")


def build_prompt(ex):
    # Minimal formatter: instruction + input -> target = output
    inst = ex.get("instruction", "")
    inp = ex.get("input", "")
    out = ex.get("output", "")
    # Few-shot friendly template; keep simple for small data
    prompt = f"Instruction: {inst}\nInput: {inp}\nAnswer:"
    return {"text": prompt, "labels": out}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base_model", required=True)
    ap.add_argument("--data_path", required=True)
    ap.add_argument("--output_dir", default="lora_out")
    ap.add_argument("--max_steps", type=int, default=300)
    ap.add_argument("--batch_size", type=int, default=2)
    ap.add_argument("--grad_accum", type=int, default=8)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--lora_r", type=int, default=16)
    ap.add_argument("--lora_alpha", type=int, default=32)
    ap.add_argument("--lora_dropout", type=float, default=0.05)
    args = ap.parse_args()

    # 4-bit quantization for cheap fine-tuning
    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=(
            torch.bfloat16 if torch.cuda.is_available() else torch.float16
        ),
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
    )

    tok = AutoTokenizer.from_pretrained(args.base_model, use_fast=True)
    tok.pad_token = tok.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        args.base_model, quantization_config=bnb, device_map="auto"
    )
    model = prepare_model_for_kbit_training(model)

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
        ],  # safe defaults for many hf LLMs
    )
    model = get_peft_model(model, lora_cfg)

    raw = load_jsonl(args.data_path)
    ds = raw.map(build_prompt, remove_columns=raw.column_names)

    def formatting(examples):
        # returns list[str] for input texts
        return [t for t in examples["text"]]

    trainer = SFTTrainer(
        model=model,
        tokenizer=tok,
        train_dataset=ds,
        dataset_text_field="text",
        max_seq_length=1024,
        args=SFTConfig(
            output_dir=args.output_dir,
            per_device_train_batch_size=args.batch_size,
            gradient_accumulation_steps=args.grad_accum,
            learning_rate=args.lr,
            logging_steps=10,
            save_steps=100,
            max_steps=args.max_steps,
            bf16=torch.cuda.is_available(),  # use bf16 on modern GPUs
            optim="paged_adamw_32bit",
            lr_scheduler_type="cosine",
            warmup_ratio=0.03,
            gradient_checkpointing=True,
            report_to=[],
        ),
        formatting_func=None,  # we prebuilt "text"
    )

    trainer.train()
    # Save just the adapters (tiny)
    trainer.model.save_pretrained(args.output_dir)
    tok.save_pretrained(args.output_dir)
    print(f"Saved LoRA adapter to: {args.output_dir}")


if __name__ == "__main__":
    main()
