#!/usr/bin/env python3
"""
Convert either:
  A) pretty JSON array -> JSONL (each object per line),
  B) existing JSONL (validated + copied),
  C) 9-lines-per-sample text -> JSONL.

Usage:
  python packages/evals/datasets/tools/convert_any_to_jsonl.py <in_path> <out_path>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

ORDER: List[str] = [
    "role",
    "task_id",
    "instruction",
    "context",
    "output",
    "tags",
    "source",
    "quality",
    "notes",
]


def clean_scalar(s: str) -> Optional[str]:
    t = s.strip()
    if t.lower() == "null":
        return None
    if t.startswith('"') and t.endswith('"') and len(t) >= 2:
        t = t[1:-1]
    return t


def parse_tags(raw: str) -> List[str]:
    raw = raw.strip()
    # Try as JSON array first
    try:
        v = json.loads(raw)
        if isinstance(v, list):
            return [str(x) for x in v]
    except Exception:
        pass
    # Fallback: comma-separated
    t = clean_scalar(raw) or ""
    return [x.strip() for x in t.split(",") if x.strip()]


def parse_quality(raw: str) -> int:
    t = clean_scalar(raw)
    try:
        return int(t) if t is not None else 0
    except Exception as e:
        raise ValueError(f"quality must be int, got: {raw!r}") from e


def write_jsonl(rows: List[Dict[str, Any]], out_path: Path) -> None:
    n = 0
    with out_path.open("w", encoding="utf-8") as w:
        for obj in rows:
            w.write(json.dumps(obj, ensure_ascii=False) + "\n")
            n += 1
    print(f"Wrote {n} examples -> {out_path}")


def convert_json_array_to_jsonl(in_path: Path, out_path: Path) -> None:
    data = json.loads(in_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Top-level JSON must be an array of objects.")
    write_jsonl(data, out_path)


def convert_existing_jsonl(in_path: Path, out_path: Path) -> None:
    """Validate each line parses as JSON; then copy to out_path."""
    n = 0
    with in_path.open(encoding="utf-8") as r, out_path.open("w", encoding="utf-8") as w:
        for i, line in enumerate(r, 1):
            if not line.strip():
                continue
            try:
                _ = json.loads(line)
            except Exception as e:
                raise ValueError(f"{in_path}:{i} invalid JSON line: {e}") from e
            w.write(line.rstrip("\n") + "\n")
            n += 1
    print(f"Validated & copied {n} JSONL rows -> {out_path}")


def convert_9_lines_per_sample(in_path: Path, out_path: Path) -> None:
    lines = [
        ln for ln in in_path.read_text(encoding="utf-8").splitlines() if ln.strip()
    ]
    if len(lines) % 9 != 0:
        print(
            f"Warning: input has {len(lines)} non-empty lines (not a multiple of 9). "
            f"Trailing lines will be ignored."
        )
    rows: List[Dict[str, Any]] = []
    for i in range(0, len(lines) - (len(lines) % 9), 9):
        chunk = lines[i : i + 9]
        role = clean_scalar(chunk[0])
        task_id = clean_scalar(chunk[1])
        instruction = clean_scalar(chunk[2]) or ""
        context_raw = chunk[3]
        output = clean_scalar(chunk[4]) or ""
        tags = parse_tags(chunk[5])
        source = clean_scalar(chunk[6]) or "manual"
        quality = parse_quality(chunk[7])
        notes = clean_scalar(chunk[8])

        context: Optional[str]
        context = (
            None if context_raw.strip().lower() == "null" else clean_scalar(context_raw)
        )

        obj: Dict[str, Any] = {
            "role": role,
            "task_id": task_id,
            "instruction": instruction,
            "context": context,
            "output": output,
            "tags": tags,
            "source": source,
            "quality": quality,
            "notes": notes,
        }
        rows.append(obj)
    write_jsonl(rows, out_path)


def main(argv: Sequence[str]) -> int:
    if len(argv) != 2:
        print("Usage: convert_any_to_jsonl.py <in_path> <out_path>")
        return 2
    in_path, out_path = Path(argv[0]), Path(argv[1])
    text = in_path.read_text(encoding="utf-8", errors="replace")

    # Heuristic:
    # - '['  -> JSON array
    # - '{'  -> likely existing JSONL (object per line)
    # - else -> 9-lines-per-sample text
    first_non_ws = next((c for c in text if not c.isspace()), "")
    if first_non_ws == "[":
        convert_json_array_to_jsonl(in_path, out_path)
    elif first_non_ws == "{":
        convert_existing_jsonl(in_path, out_path)
    else:
        convert_9_lines_per_sample(in_path, out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
