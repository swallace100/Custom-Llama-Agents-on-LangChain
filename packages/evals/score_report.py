#!/usr/bin/env python3
"""
Compare two eval runs (base vs lora) and write a Markdown report.

Usage:
  python packages/evals/score_report.py \
    --base out/evals/researcher_base.jsonl \
    --lora out/evals/researcher_lora.jsonl \
    --out  out/evals/researcher_report.md
"""

from __future__ import annotations
import argparse
import json
import statistics
import textwrap
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Tuple


def sim(a: str, b: str) -> float:
    return SequenceMatcher(None, a or "", b or "").ratio()


def normalize(s: str) -> str:
    return " ".join((s or "").strip().split()).lower()


def exact(a: str, b: str) -> bool:
    return normalize(a) == normalize(b)


def load(path: Path) -> Dict[str, Dict[str, Any]]:
    by_id: Dict[str, Dict[str, Any]] = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            ex = json.loads(line)
            by_id[str(ex["task_id"])] = ex
    return by_id


def summarize(rows: List[Dict[str, Any]]) -> Dict[str, float]:
    lat = [r.get("latency_ms", 0) for r in rows if isinstance(r.get("latency_ms"), int)]
    return {
        "n": float(len(rows)),
        "lat_p50": float(statistics.median(lat)) if lat else 0.0,
        "lat_p95": (
            float(statistics.quantiles(lat, n=20)[18])
            if len(lat) >= 20
            else (float(max(lat)) if lat else 0.0)
        ),
        "avg_pred_len": (
            float(statistics.mean([len((r.get("prediction") or "")) for r in rows]))
            if rows
            else 0.0
        ),
    }


def pick_examples(
    pairs: List[Tuple[Dict[str, Any], Dict[str, Any]]], k: int = 3
) -> Tuple[List[Tuple[Any, Any, float]], List[Tuple[Any, Any, float]]]:
    diffs: List[Tuple[float, Dict[str, Any], Dict[str, Any]]] = []
    for base_row, lora_row in pairs:
        s_base = sim(base_row.get("reference", ""), base_row.get("prediction", ""))
        s_lora = sim(lora_row.get("reference", ""), lora_row.get("prediction", ""))
        diffs.append((s_lora - s_base, base_row, lora_row))
    diffs.sort(key=lambda x: x[0], reverse=True)
    improved = [(base, lora, delta) for delta, base, lora in diffs[:k]]
    regressed = [(base, lora, delta) for delta, base, lora in diffs[-k:]]
    return improved, regressed


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--lora", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    base = load(Path(args.base))
    lora = load(Path(args.lora))

    common_ids = sorted(set(base) & set(lora))
    pairs = [(base[i], lora[i]) for i in common_ids]

    rows: List[Dict[str, Any]] = []
    for base_row, lora_row in pairs:
        ref = base_row.get("reference", "")
        sb = sim(ref, base_row.get("prediction", ""))
        sl = sim(ref, lora_row.get("prediction", ""))
        eb = exact(ref, base_row.get("prediction", ""))
        el = exact(ref, lora_row.get("prediction", ""))
        rows.append(
            {
                "task_id": base_row["task_id"],
                "sim_base": sb,
                "sim_lora": sl,
                "exact_base": eb,
                "exact_lora": el,
            }
        )

    # Aggregate
    avg_base = sum(r["sim_base"] for r in rows) / len(rows) if rows else 0.0
    avg_lora = sum(r["sim_lora"] for r in rows) / len(rows) if rows else 0.0
    acc_base = sum(1 for r in rows if r["exact_base"]) / len(rows) if rows else 0.0
    acc_lora = sum(1 for r in rows if r["exact_lora"]) / len(rows) if rows else 0.0

    sum_base = summarize([base[i] for i in common_ids])
    sum_lora = summarize([lora[i] for i in common_ids])

    improved, regressed = pick_examples(pairs, k=3)

    md: List[str] = []
    md.append("# Eval Report")
    md.append("")
    md.append(
        f"Comparing **{Path(args.base).name}** vs **{Path(args.lora).name}** on {len(common_ids)} tasks."
    )
    md.append("")
    md.append("## Metrics")
    md.append("")
    md.append("| Metric | Baseline | LoRA | Δ |")
    md.append("|---|---:|---:|---:|")
    md.append(
        f"| Avg similarity (0–1) | {avg_base:.3f} | {avg_lora:.3f} | {avg_lora - avg_base:+.3f} |"
    )
    md.append(
        f"| Exact match | {acc_base * 100:.1f}% | {acc_lora * 100:.1f}% | {(acc_lora - acc_base) * 100:+.1f} pp |"
    )
    md.append(
        f"| P50 latency (ms) | {sum_base['lat_p50']:.0f} | {sum_lora['lat_p50']:.0f} | {sum_lora['lat_p50'] - sum_base['lat_p50']:+.0f} |"
    )
    md.append(
        f"| P95 latency (ms) | {sum_base['lat_p95']:.0f} | {sum_lora['lat_p95']:.0f} | {sum_lora['lat_p95'] - sum_base['lat_p95']:+.0f} |"
    )
    md.append(
        f"| Avg output length (chars) | {sum_base['avg_pred_len']:.0f} | {sum_lora['avg_pred_len']:.0f} | {sum_lora['avg_pred_len'] - sum_base['avg_pred_len']:+.0f} |"
    )
    md.append("")
    md.append("## Notable Improvements")
    for base_row, lora_row, delta in improved:
        md.append(f"- **{base_row['task_id']}** (Δ sim {delta:+.3f})")
        md.append(
            "  - Ref: "
            + textwrap.shorten(
                base_row.get("reference", ""), width=220, placeholder="…"
            )
        )
        md.append(
            "  - Base: "
            + textwrap.shorten(
                base_row.get("prediction", ""), width=220, placeholder="…"
            )
        )
        md.append(
            "  - LoRA: "
            + textwrap.shorten(
                lora_row.get("prediction", ""), width=220, placeholder="…"
            )
        )
    md.append("")
    md.append("## Possible Regressions")
    for base_row, lora_row, delta in regressed:
        md.append(f"- **{base_row['task_id']}** (Δ sim {delta:+.3f})")
        md.append(
            "  - Ref: "
            + textwrap.shorten(
                base_row.get("reference", ""), width=220, placeholder="…"
            )
        )
        md.append(
            "  - Base: "
            + textwrap.shorten(
                base_row.get("prediction", ""), width=220, placeholder="…"
            )
        )
        md.append(
            "  - LoRA: "
            + textwrap.shorten(
                lora_row.get("prediction", ""), width=220, placeholder="…"
            )
        )

    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote report -> {outp}")


if __name__ == "__main__":
    main()
