"""
response_agent: generate the assistant reply with rolling chat history.
Payload from routes: {"text": "<control/context prompt>", "user": "<original user msg>", "conv_id":"optional"}
"""

import os, json, httpx
from typing import Optional, Dict, Any, List

OR_KEY = os.getenv("OPENROUTER_API_KEY")
OR_BASE = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
MODEL_RSP = os.getenv("MODEL_RESPONDER", "meta-llama/llama-3.1-70b-instruct")

if not OR_KEY:
    raise SystemExit("Missing OPENROUTER_API_KEY environment variable")

# in-memory chat history: conv_id -> list[{"role":"user"|"assistant","content":str}]
HISTORY: Dict[str, List[Dict[str, str]]] = {}

SYSTEM_BASE = (
    "You are a cautious, concise companion for older adults. "
    "Follow any control instructions provided in prior system/user context blocks. "
    "Be warm, brief, and safe. Never diagnose. Prefer short follow-ups."
)

def _or_chat_with_history(
    model: str,
    system_base: str,
    control_context: str,
    history: List[Dict[str, str]],
    new_user_msg: str,
) -> str:
    headers = {
        "Authorization": f"Bearer {OR_KEY}",
        "HTTP-Referer": os.getenv("OPENROUTER_REFERER", "https://hack.local"),
        "X-Title": os.getenv("OPENROUTER_TITLE", "HygieiAI"),
    }
    # keep prompt short but consistent
    prior = history[-16:] if len(history) > 16 else history
    messages: List[Dict[str, str]] = (
        [{"role": "system", "content": system_base}]
        + [{"role": "system", "content": control_context}]  # classifier-built prompt
        + prior
        + [{"role": "user", "content": new_user_msg}]
    )
    payload: Dict[str, Any] = {"model": model, "messages": messages}
    r = httpx.post(f"{OR_BASE}/chat/completions", headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    out = r.json()["choices"][0]["message"]["content"]
    return out

def process_text(payload: Optional[str]) -> str:
    if not payload:
        print("agent.process_text called with no payload"); return ""
    print("agent.process_text called with payload:", payload)

    try:
        p = json.loads(payload)
    except json.JSONDecodeError:
        # assume raw text is the context; no user turn provided
        p = {"text": payload}

    control_context = p.get("text", "") or ""
    user_msg = p.get("user") or p.get("user_message") or ""  # prefer real human utterance
    conv_id = str(p.get("conv_id") or "default")

    hist = HISTORY.setdefault(conv_id, [])

    # call LLM with prior history + this user turn
    reply = _or_chat_with_history(
        MODEL_RSP,
        SYSTEM_BASE,
        control_context,
        hist,
        user_msg or control_context,  # fallback if no explicit user text
    )

    # update history with the new pair
    hist.append({"role": "user", "content": user_msg or control_context})
    hist.append({"role": "assistant", "content": reply})
    if len(hist) > 24:
        HISTORY[conv_id] = hist[-24:]

    print(f"[HISTORY conv={conv_id}] now {len(HISTORY[conv_id])} turns")
    print(f"- reply:\n{reply}")
    return reply
