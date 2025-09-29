#!/usr/bin/env python3
"""
Lightweight validator for our role datasets.

Usage:
  python packages/evals/datasets/tools/validate.py \
    packages/evals/datasets/researcher.jsonl \
    packages/evals/datasets/writer.jsonl \
    packages/evals/datasets/editor.jsonl
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence, Set, cast

ROLES: Set[str] = {"researcher", "writer", "editor"}
REQUIRED: Set[str] = {"role", "task_id", "instruction", "output", "source", "quality"}


def _utf8_ok() -> bool:
    enc = getattr(sys.stdout, "encoding", None) or ""
    return "UTF-8" in enc.upper()


OK = "✅" if _utf8_ok() else "OK"
FAIL = "❌" if _utf8_ok() else "FAIL"


def _err(msg: str) -> int:
    print(msg)
    return 1


def validate_obj(obj: Dict[str, Any], path: Path, line_no: int) -> int:
    # Required keys
    missing = REQUIRED - obj.keys()
    if missing:
        return _err(f"{path}:{line_no} missing keys: {sorted(missing)}")

    # role
    role = cast(str, obj["role"])
    if role not in ROLES:
        return _err(
            f"{path}:{line_no} invalid role={role!r} (must be one of {sorted(ROLES)})"
        )

    # task_id
    task_id = obj["task_id"]
    if not isinstance(task_id, str) or not task_id.strip():
        return _err(f"{path}:{line_no} task_id must be non-empty string")

    # instruction/output length
    instruction = obj["instruction"]
    if not isinstance(instruction, str) or len(instruction.strip()) < 10:
        return _err(f"{path}:{line_no} instruction too short (<10 chars)")

    output = obj["output"]
    if not isinstance(output, str) or len(output.strip()) < 10:
        return _err(f"{path}:{line_no} output too short (<10 chars)")

    # source
    source = obj["source"]
    if source not in {"manual", "synthetic", "internal"}:
        return _err(f"{path}:{line_no} invalid source={source!r}")

    # quality
    try:
        q = int(obj["quality"])
    except Exception:
        return _err(f"{path}:{line_no} quality must be int 1..5")
    if not (1 <= q <= 5):
        return _err(f"{path}:{line_no} quality={q} out of range 1..5")

    # optional fields types
    if "tags" in obj and not isinstance(obj["tags"], list):
        return _err(f"{path}:{line_no} tags must be a list of strings")
    if "tags" in obj:
        tags = cast(List[Any], obj["tags"])
        if any(not isinstance(t, str) or not t for t in tags):
            return _err(f"{path}:{line_no} tags contains non-string or empty values")

    if (
        "context" in obj
        and obj["context"] is not None
        and not isinstance(obj["context"], str)
    ):
        return _err(f"{path}:{line_no} context must be string or null")

    if (
        "notes" in obj
        and obj["notes"] is not None
        and not isinstance(obj["notes"], str)
    ):
        return _err(f"{path}:{line_no} notes must be string or null")

    return 0


def validate_file(path: Path) -> int:
    errors = 0
    with path.open(encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                obj = cast(Dict[str, Any], json.loads(line))
            except Exception as e:
                errors += _err(f"{path}:{i} invalid JSON: {e}")
                continue
            errors += validate_obj(obj, path, i)
    return errors


def main(args: Sequence[str]) -> int:
    if not args:
        print("Usage: python packages/evals/datasets/tools/validate.py <files...>")
        return 2
    total = 0
    for p in args:
        path = Path(p)
        if not path.exists():
            total += _err(f"{path} not found")
            continue
        total += validate_file(path)
    if total:
        print(f"\n{FAIL} Validation failed with {total} error(s).")
        return 1
    print(f"\n{OK} All files passed validation.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
