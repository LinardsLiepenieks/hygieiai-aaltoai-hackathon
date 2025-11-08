"""
response_agent: generate the assistant reply based on intent.
Input to process_text is a JSON string:
{"text":"...","intent":"medical|smalltalk|emergency_candidate|routine_checkin"}
"""

import os, json
from typing import Optional, Dict, Any
import httpx

OR_KEY = "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"
OR_BASE = "https://openrouter.ai/api/v1"

MODEL_CLS = "meta-llama/llama-3.1-70b-instruct"
MODEL_RSP = "meta-llama/llama-3.1-70b-instruct"
MODEL_SFT = "meta-llama/llama-3.1-70b-instruct"
if not OR_KEY:
    raise SystemExit("Missing OPENROUTER_API_KEY")

SYSTEM_RESPONDER_SMALLTALK = "You are a brief, friendly companion. No medical opinions. 1–2 short sentences, warm and respectful."
SYSTEM_RESPONDER_MEDICAL = "You are a cautious health check-in assistant. Ask OLD CARTS follow-ups. Be concise (2–3 short sentences)."


def _or_chat(model: str, system: str, user: str) -> str:
    headers = {
        "Authorization": f"Bearer {OR_KEY}",
        "HTTP-Referer": "https://hack.local",
        "X-Title": "HygieiAI",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
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
        p = {"text": payload, "intent": "smalltalk"}
    text = p.get("text", "")
    intent = p.get("intent", "smalltalk")

    if intent in ("medical", "emergency_candidate"):
        reply = _or_chat(MODEL_RSP, SYSTEM_RESPONDER_MEDICAL, text)
    elif intent == "routine_checkin":
        reply = _or_chat(
            MODEL_RSP, SYSTEM_RESPONDER_SMALLTALK, "How are you feeling today?"
        )
    else:
        reply = _or_chat(MODEL_RSP, SYSTEM_RESPONDER_SMALLTALK, text)

    # print(f"- reply:\n{reply}")
    return reply
