import argparse
import json
import time
from pathlib import Path
from typing import Dict, Any, List
import requests


def call_local_api(messages: List[Dict[str, str]], model: str, port: int = 7001) -> str:
    url = f"http://localhost:{port}/v1/chat/completions"
    r = requests.post(url, json={"model": model, "messages": messages}, timeout=120)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--model", required=True, help="base or lora:adapter_name (passed to server)"
    )
    ap.add_argument("--data", required=True, help="Path to .jsonl dataset")
    ap.add_argument("--out", required=True, help="Path to write predictions (.jsonl)")
    ap.add_argument("--port", type=int, default=7001, help="llm_host_py port")
    args = ap.parse_args()

    model = "microsoft/phi-3-mini-4k-instruct" if args.model == "base" else args.model

    in_path = Path(args.data)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    n, results = 0, []
    with in_path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            ex: Dict[str, Any] = json.loads(line)

            messages = [
                {"role": "system", "content": f"You are a {ex['role']} agent."},
                {
                    "role": "user",
                    "content": ex["instruction"]
                    + (f"\n\nContext:\n{ex['context']}" if ex.get("context") else ""),
                },
            ]

            t0 = time.perf_counter()
            try:
                pred = call_local_api(messages, model=model, port=args.port)
            except Exception:
                pred = ""
            lat_ms = int((time.time() - t0) * 1000)

            results.append(
                {
                    "task_id": ex["task_id"],
                    "role": ex["role"],
                    "instruction": ex["instruction"],
                    "context": ex.get("context"),
                    "reference": ex["output"],
                    "prediction": pred,
                    "latency_ms": lat_ms,
                }
            )
            n += 1

    with out_path.open("w", encoding="utf-8") as w:
        for row in results:
            w.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Wrote {n} results -> {out_path}")


if __name__ == "__main__":
    main()
