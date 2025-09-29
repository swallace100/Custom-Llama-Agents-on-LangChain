#!/usr/bin/env python3
"""
Convert our JSONL schema -> TRL chat JSONL (messages[] per sample).

Usage:
  python packages/evals/datasets/tools/to_trl.py out/researcher.chat.jsonl packages/evals/datasets/researcher.jsonl
"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, List, TypedDict


class Message(TypedDict):
    role: str
    content: str


class ChatRow(TypedDict, total=False):
    messages: List[Message]
    meta: Dict[str, Any]


def to_chat(ex: Dict[str, Any]) -> ChatRow:
    ctx = f"\n\nContext:\n{ex['context']}" if ex.get("context") else ""
    return {
        "messages": [
            {
                "role": "system",
                "content": {
                    "researcher": "You are a pragmatic research agent. Be structured and specific.",
                    "writer": "You are a concise technical writer. Prefer clear, active voice.",
                    "editor": "You are a precise editor. Rewrite for clarity and brevity.",
                }[ex["role"]],
            },
            {"role": "user", "content": str(ex["instruction"]) + ctx},
            {"role": "assistant", "content": str(ex["output"])},
        ],
        "meta": {
            "role": str(ex["role"]),
            "task_id": str(ex["task_id"]),
            "tags": list(ex.get("tags", [])),
        },
    }


def main(out_path: str, *paths: str) -> None:
    out: List[ChatRow] = []
    for p in paths:
        with open(p, encoding="utf-8") as fh:
            for i, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    ex = json.loads(line)
                except Exception as e:
                    raise ValueError(f"{p}:{i} invalid JSON: {e}") from e
                out.append(to_chat(ex))
    with open(out_path, "w", encoding="utf-8") as w:
        for row in out:
            w.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Wrote {len(out)} samples -> {out_path}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: to_trl.py <out.jsonl> <files...>")
        sys.exit(2)
    main(sys.argv[1], *sys.argv[2:])
