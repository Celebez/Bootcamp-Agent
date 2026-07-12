"""Pelacakan biaya token USD per panggilan LLM.

Harga per 1K token (USD) disimpan di `PRICING`. Override via env:
  BOOTCAMP_COST_INPUT   (per 1K input token)
  BOOTCAMP_COST_OUTPUT  (per 1K output token)

Tersimpan ke ~/.bootcamp/cost.json (append-only).
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, asdict
from typing import Dict, Optional


# Harga default (USD per 1K token) — model umum OpenAI-compatible.
# Override env akan menimpa seluruh dict bila model tidak ada di sini.
PRICING: Dict[str, Dict[str, float]] = {
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
    "claude-3-sonnet": {"input": 0.003, "output": 0.015},
    "claude-3-opus": {"input": 0.015, "output": 0.075},
    "deepseek-chat": {"input": 0.00014, "output": 0.00028},
    "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
}


def _home() -> str:
    return os.environ.get("BOOTCAMP_HOME") or os.path.join(
        os.path.expanduser("~"), ".bootcamp"
    )


def _path() -> str:
    return os.path.join(_home(), "cost.json")


def _pricing_for(model: str) -> Dict[str, float]:
    """Lookup harga untuk model; fallback env override atau default aman."""
    if model in PRICING:
        return PRICING[model]
    # Coba cari prefix match (mis. 'gpt-4o-2024-...' → 'gpt-4o').
    for key in PRICING:
        if model.startswith(key):
            return PRICING[key]
    # Env override tunggal (model custom).
    env_in = os.environ.get("BOOTCAMP_COST_INPUT")
    env_out = os.environ.get("BOOTCAMP_COST_OUTPUT")
    if env_in and env_out:
        return {"input": float(env_in), "output": float(env_out)}
    # Default sangat murah agar tidak误导.
    return {"input": 0.001, "output": 0.002}


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    p = _pricing_for(model)
    return (input_tokens / 1000.0) * p["input"] + (output_tokens / 1000.0) * p["output"]


@dataclass
class CostEntry:
    ts: float
    model: str
    input_tokens: int
    output_tokens: int
    usd: float


def record(model: str, input_tokens: int, output_tokens: int) -> CostEntry:
    entry = CostEntry(
        ts=time.time(),
        model=model,
        input_tokens=int(input_tokens or 0),
        output_tokens=int(output_tokens or 0),
        usd=round(estimate_cost(model, input_tokens, output_tokens), 6),
    )
    os.makedirs(_home(), exist_ok=True)
    try:
        with open(_path(), "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(entry)) + "\n")
    except OSError:
        pass  # Jangan gagalkan agen karena IO cost log.
    return entry


def summary(limit: int = 1000) -> dict:
    """Ringkasan agregat dari log terakhir."""
    total_in = total_out = 0
    total_usd = 0.0
    by_model: Dict[str, dict] = {}
    try:
        with open(_path(), "r", encoding="utf-8") as f:
            lines = f.readlines()[-limit:]
    except FileNotFoundError:
        return {"total_usd": 0.0, "total_input_tokens": 0, "total_output_tokens": 0, "by_model": {}}
    for line in lines:
        try:
            e = json.loads(line)
        except Exception:
            continue
        m = e["model"]
        b = by_model.setdefault(m, {"usd": 0.0, "input": 0, "output": 0, "calls": 0})
        b["usd"] += e["usd"]
        b["input"] += e["input_tokens"]
        b["output"] += e["output_tokens"]
        b["calls"] += 1
        total_in += e["input_tokens"]
        total_out += e["output_tokens"]
        total_usd += e["usd"]
    return {
        "total_usd": round(total_usd, 6),
        "total_input_tokens": total_in,
        "total_output_tokens": total_out,
        "by_model": {k: {kk: (round(vv, 6) if isinstance(vv, float) else vv) for kk, vv in v.items()} for k, v in by_model.items()},
    }


def format_summary(s: dict) -> str:
    if not s or s["total_usd"] == 0:
        return "Belum ada catatan biaya."
    lines = [
        f"Total: ${s['total_usd']:.4f} | "
        f"in={s['total_input_tokens']:,} out={s['total_output_tokens']:,}",
        "Per model:",
    ]
    for m, b in sorted(s["by_model"].items(), key=lambda x: -x[1]["usd"]):
        lines.append(
            f"  • {m:32s}  ${b['usd']:8.4f}  ({b['calls']:4d}×, "
            f"in={b['input']:>7,}, out={b['output']:>6,})"
        )
    return "\n".join(lines)
