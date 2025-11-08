"""
extraction_agent: classify intent and print all decisions.
Input to process_text is a plain user string.
"""

import os, json
from typing import Optional, Dict, Any
import httpx
from .prompt_builder import build_llm_prompt

OR_KEY = "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"
OR_BASE = "https://openrouter.ai/api/v1"

MODEL_CLS = "meta-llama/llama-3.1-70b-instruct"
MODEL_RSP = "meta-llama/llama-3.1-70b-instruct"
MODEL_SFT = "meta-llama/llama-3.1-70b-instruct"
if not OR_KEY:
    raise SystemExit("Missing OPENROUTER_API_KEY")

# ---- keyword gates ----
EMERGENCY_PATTERNS = [
    (
        "chest pain",
        [
            "shortness of breath",
            "breathless",
            "sweating",
            "radiating",
            "left arm",
            "jaw",
        ],
    ),
    ("slurred speech", []),
    ("face droop", []),
    ("one side weak", []),
    ("worst headache", []),
    ("severe bleeding", []),
]
MEDICAL_KEYWORDS = [
    "pain",
    "ache",
    "dizzy",
    "fall",
    "bleed",
    "cut",
    "chest",
    "breath",
    "shortness of breath",
    "faint",
    "numb",
    "tingling",
    "slurred speech",
    "confusion",
    "swelling",
    "fever",
    "vomit",
    "black stool",
    "pressure",
    "radiating",
    "jaw",
    "left arm",
    "headache",
    "weakness",
    "puffy",
    "stiffness",
    "sore",
    "rash",
]


def _kw_sieve(t: str) -> bool:
    t = t.lower()
    return any(k in t for k in MEDICAL_KEYWORDS)


def _emergency_hit(t: str) -> bool:
    t = t.lower()
    for main, alts in EMERGENCY_PATTERNS:
        if main in t and (not alts or any(a in t for a in alts)):
            return True
    return False


# ---- prompts ----
SYSTEM_CLASSIFIER = """You classify a single user message.
Return ONLY JSON with keys:
intent: one of ["smalltalk","medical","emergency_candidate","routine_checkin"]
essence: short noun phrase like "lower back pain" or "cookies"
red_flags: array of dangerous signals
confidence: number 0..1
No extra text."""
SYSTEM_RESPONDER_SMALLTALK = "You are a brief, friendly companion. No medical opinions. 1–2 short sentences, warm and respectful."
SYSTEM_RESPONDER_MEDICAL = """You are a cautious health check-in assistant for older adults.
Never diagnose. Ask focused OLD CARTS follow-ups. Be concise (2–3 short sentences)."""
SYSTEM_SAFETY = """You judge the reply and create a storage summary.
Return ONLY JSON with: medically_relevant:boolean, emergency:boolean, safety_ok:boolean, db_summary:string"""


# ---- OpenRouter helper ----
def _or_chat(model: str, system: str, user: str, json_mode: bool = False) -> str:
    headers = {
        "Authorization": f"Bearer {OR_KEY}",
        "HTTP-Referer": "https://hack.local",
        "X-Title": "HygieiAI",
    }
    payload: Dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    print(f"\n[LLM CALL] {model}\n[SYSTEM]\n{system}\n[USER]\n{user}")
    r = httpx.post(
        f"{OR_BASE}/chat/completions", headers=headers, json=payload, timeout=60
    )
    r.raise_for_status()
    out = r.json()["choices"][0]["message"]["content"]
    print(f"[RAW]\n{out}\n")
    return out


# ---- public entrypoint for your service ----
def process_text(text: Optional[str]) -> None:
    if text is None:
        print("agent.process_text called with no text")
        return
    print("agent.process_text called with:", text)
    print("=" * 72)

    force_med = _kw_sieve(text)
    emerg = _emergency_hit(text)
    print(f"- keyword_sieve={force_med}")
    print(f"- emergency_pattern={emerg}")

    # 1) classify
    cls_raw = _or_chat(MODEL_CLS, SYSTEM_CLASSIFIER, text, json_mode=True)
    try:
        cls = json.loads(cls_raw)
    except json.JSONDecodeError:
        print("[WARN] classifier JSON parse failed -> fallback smalltalk")
        cls = {"intent": "smalltalk", "essence": "", "red_flags": [], "confidence": 0.0}

    intent = cls.get("intent", "smalltalk")
    if emerg:
        intent = "emergency_candidate"
        cls.setdefault("red_flags", []).append("emergency_pattern_hit")
    elif force_med and intent == "smalltalk":
        intent = "medical"

    print(f"- classifier.intent={cls.get('intent')}  -> final.intent={intent}")
    print(f"- essence={cls.get('essence')}")
    print(f"- red_flags={cls.get('red_flags')}")
    print(f"- confidence={cls.get('confidence')}")

    # 2) responder
    if intent in ("medical", "emergency_candidate"):
        rsp = _or_chat(MODEL_RSP, SYSTEM_RESPONDER_MEDICAL, text, json_mode=False)
    elif intent == "routine_checkin":
        rsp = _or_chat(
            MODEL_RSP,
            SYSTEM_RESPONDER_SMALLTALK,
            "How are you feeling today?",
            json_mode=False,
        )
    else:
        rsp = _or_chat(MODEL_RSP, SYSTEM_RESPONDER_SMALLTALK, text, json_mode=False)
    print(f"- reply:\n{rsp}")

    # 3) safety + summary
    safety_input = f"USER:\n{text}\n---\nASSISTANT:\n{rsp}"
    s_raw = _or_chat(MODEL_SFT, SYSTEM_SAFETY, safety_input, json_mode=True)
    try:
        s = json.loads(s_raw)
    except json.JSONDecodeError:
        print("[WARN] safety JSON parse failed -> default flags")
        s = {
            "medically_relevant": False,
            "emergency": False,
            "safety_ok": True,
            "db_summary": "N/A",
        }

    medically_relevant = bool(s.get("medically_relevant", False)) or (
        intent in ("medical", "emergency_candidate")
    )
    emergency_flag = bool(s.get("emergency", False)) or emerg
    print(
        f"- safety.medically_relevant={s.get('medically_relevant')} -> store={medically_relevant}"
    )
    print(
        f"- safety.emergency={s.get('emergency')} or gate={emerg} -> emergency={emergency_flag}"
    )
    print(f"- safety.safety_ok={s.get('safety_ok')}")
    print(f"- safety.db_summary={s.get('db_summary')}")
    if medically_relevant or emergency_flag:
        print("[STORE] would store encounter summary and reply")
    else:
        print("[SKIP STORE] smalltalk or non-medical")

    llm_prompt = build_llm_prompt(
        text=text,
        intent=intent,
        essence=cls.get("essence", ""),
        red_flags=cls.get("red_flags", []),
        confidence=cls.get("confidence", 0.0),
        keyword_sieve=force_med,
        emergency_pattern=emerg,
        medically_relevant=medically_relevant,
        emergency_flag=emergency_flag,
        safety_ok=s.get("safety_ok", True),
    )

    return llm_prompt
