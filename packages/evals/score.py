#!/usr/bin/env python3
"""
Score eval outputs (baseline vs LoRA) and optionally write a Markdown report.

Each input JSONL row should look like what run_eval.py wrote:
{
  "task_id": "...",
  "role": "...",
  "instruction": "...",
  "context": "... or null",
  "reference": "<gold text>",
  "prediction": "<model text>"
}

Usage examples:
  # Score a single results file
  python packages/evals/score.py --file out/evals/researcher_base.jsonl

  # Compare base vs lora and write a report
  python packages/evals/score.py --base out/evals/researcher_base.jsonl \
                                 --lora out/evals/researcher_lora.jsonl \
                                 --report out/evals/researcher_report.md
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List, Tuple, Any


def _read_jsonl(path: Path) -> List[Dict]:
    rows: List[Dict] = []
    with path.open(encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception as e:
                raise ValueError(f"{path}:{i} invalid JSON: {e}")
    return rows


def _safe_to_str(x: Any) -> str:
    try:
        return str(x)
    except Exception:
        return ""


def _char_f1(ref: str, pred: str) -> float:
    """Very cheap character-level F1-ish score in [0,1]."""
    r, p = ref.strip(), pred.strip()
    if not r and not p:
        return 1.0
    if not r or not p:
        return 0.0
    # overlap by characters (bag-of-chars)
    from collections import Counter

    cr, cp = Counter(r), Counter(p)
    overlap = sum(min(cr[c], cp[c]) for c in set(cr) | set(cp))
    precision = overlap / max(len(p), 1)
    recall = overlap / max(len(r), 1)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def score_rows(rows: Iterable[Dict]) -> Tuple[float, List[Tuple[str, float]]]:
    """Return (average_score, per_item_scores[(task_id, score), ...])."""
    per: List[Tuple[str, float]] = []
    for ex in rows:
        ref = _safe_to_str(ex.get("reference", ""))
        pred = _safe_to_str(ex.get("prediction", ""))
        s = _char_f1(ref, pred)
        per.append((str(ex.get("task_id", "")), s))
    avg = sum(s for _, s in per) / max(len(per), 1)
    return avg, per


def index_by_task(rows: Iterable[Dict]) -> Dict[str, Dict]:
    return {str(ex.get("task_id", "")): ex for ex in rows}


def write_report_md(
    path: Path,
    base_avg: float | None,
    lora_avg: float | None,
    base_path: Path | None,
    lora_path: Path | None,
) -> None:
    lines: List[str] = []
    lines.append("# Eval Report")
    if base_avg is not None:
        lines.append(f"- Base file: `{base_path}`")
        lines.append(f"- Base avg: {base_avg:.3f}")
    if lora_avg is not None:
        lines.append(f"- LoRA file: `{lora_path}`")
        lines.append(f"- LoRA avg: {lora_avg:.3f}")
    if base_avg is not None and lora_avg is not None:
        delta = (lora_avg - base_avg) * 100
        lines.append(f"- Delta (LoRA - Base): {delta:+.2f} points")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote report -> {path}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", help="Score a single results JSONL")
    ap.add_argument("--base", help="Baseline results JSONL (with reference/prediction)")
    ap.add_argument("--lora", help="LoRA results JSONL (with reference/prediction)")
    ap.add_argument("--report", help="Optional Markdown report path")
    args = ap.parse_args()

    if not args.file and not (args.base and args.lora):
        ap.error("Provide either --file OR both --base and --lora")

    if args.file:
        fpath = Path(args.file)
        rows = _read_jsonl(fpath)
        avg, _ = score_rows(rows)
        print(f"[Single] {fpath} avg={avg:.3f}")
        if args.report:
            write_report_md(
                Path(args.report),
                base_avg=avg,
                lora_avg=None,
                base_path=fpath,
                lora_path=None,
            )
        return

    # base vs lora
    base_path, lora_path = Path(args.base), Path(args.lora)
    base_rows = _read_jsonl(base_path)
    lora_rows = _read_jsonl(lora_path)

    base_avg, _ = score_rows(base_rows)
    lora_avg, _ = score_rows(lora_rows)

    print(f"[Base] {base_path} avg={base_avg:.3f}")
    print(f"[LoRA] {lora_path} avg={lora_avg:.3f}")
    print(f"[Delta] LoRA - Base = {(lora_avg - base_avg):+.3f}")

    if args.report:
        write_report_md(Path(args.report), base_avg, lora_avg, base_path, lora_path)


if __name__ == "__main__":
    main()
