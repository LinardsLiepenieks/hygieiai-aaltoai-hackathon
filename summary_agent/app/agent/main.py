"""
summary_agent: safety+storage decision and summary.
Input to process_text is a JSON string:
{"user_text":"...","assistant_text":"...","emergency_gate_hit":false}
"""

import os, json
from typing import Optional, Dict, Any
import httpx
from .prompt_builder import build_memory_prompt

OR_KEY = os.getenv("OPENROUTER_API_KEY")
OR_BASE = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

MODEL_CLS = os.getenv("MODEL_CLASSIFIER", "meta-llama/llama-3.1-70b-instruct")
MODEL_RSP = os.getenv("MODEL_RESPONDER", "meta-llama/llama-3.1-70b-instruct")
MODEL_SFT = os.getenv("MODEL_SAFETY", "meta-llama/llama-3.1-70b-instruct")

if not OR_KEY:
    raise SystemExit("Missing OPENROUTER_API_KEY environment variable")

SYSTEM_SAFETY = """You judge the reply and create a storage summary.
Return ONLY JSON with: medically_relevant:boolean, emergency:boolean, safety_ok:boolean, db_summary:string"""


def _or_chat(model: str, system: str, user: str) -> str:
    headers = {
        "Authorization": f"Bearer {OR_KEY}",
        "HTTP-Referer": os.getenv("OPENROUTER_REFERER", "https://hack.local"),
        "X-Title": os.getenv("OPENROUTER_TITLE", "HygieiAI"),
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "response_format": {"type": "json_object"},
    }
    print(f"\n[LLM CALL] {model}\n[SYSTEM]\n{system}\n[USER]\n{user}")
    r = httpx.post(
        f"{OR_BASE}/chat/completions", headers=headers, json=payload, timeout=60
    )
    r.raise_for_status()
    out = r.json()["choices"][0]["message"]["content"]
    print(f"[RAW]\n{out}\n")
    return out


def process_text(payload: Optional[str]) -> None:
    if not payload:
        print("agent.process_text called with no payload")
        return
    print("agent.process_text called with payload:", payload)
    try:
        p = json.loads(payload)
    except json.JSONDecodeError:
        print("[ERROR] expected JSON with user_text and assistant_text")
        return

    user_text = p.get("user_text", "")
    assistant_text = p.get("assistant_text", "")
    emerg_gate = False

    safety_input = f"USER:\n{user_text}\n---\nASSISTANT:\n{assistant_text}"
    raw = _or_chat(MODEL_SFT, SYSTEM_SAFETY, safety_input)
    try:
        s = json.loads(raw)
    except json.JSONDecodeError:
        s = {
            "medically_relevant": False,
            "emergency": False,
            "safety_ok": True,
            "db_summary": "N/A",
        }
        print("[WARN] safety JSON parse failed -> defaults")

    medically_relevant = bool(s.get("medically_relevant", False))
    emergency = bool(s.get("emergency", False)) or emerg_gate
    print(f"- medically_relevant={medically_relevant}")
    print(f"- emergency={emergency} (llm={s.get('emergency')} gate={emerg_gate})")
    print(f"- safety_ok={s.get('safety_ok')}")
    print(f"- db_summary={s.get('db_summary')}")
    if medically_relevant or emergency:
        print("[STORE] would store encounter summary and reply")
    else:
        print("[SKIP STORE] smalltalk or non-medical")

    # ALWAYS store, regardless of type
    print("[STORE] building memory prompt for storage")
    summary_data = {
        "medically_relevant": medically_relevant,
        "emergency": emergency,
        "safety_ok": s.get("safety_ok"),
        "db_summary": s.get("db_summary"),
    }

    return build_memory_prompt(summary_data)
