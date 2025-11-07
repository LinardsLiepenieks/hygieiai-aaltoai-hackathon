"""
Simple agent functions for the extraction_agent service.

Called by your POST route. Given plain text, it:
- runs keyword/emergency gates
- calls OpenRouter classifier (JSON)
- overrides intent if needed
- calls responder
- calls safety/summary gate (JSON)
- prints all decisions and raw outputs
"""

import os, json
from typing import Optional, Dict, Any
import httpx
from dotenv import load_dotenv


OR_KEY="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"
OR_BASE="https://openrouter.ai/api/v1"
MODEL_CLS="meta-llama/llama-3.1-70b-instruct"
MODEL_RSP ="meta-llama/llama-3.1-70b-instruct"
MODEL_SFT="meta-llama/llama-3.1-70b-instruct"

if not OR_KEY:
    raise SystemExit("Missing OPENROUTER_API_KEY")

# ---------- keyword gates ----------
EMERGENCY_PATTERNS = [
    ("chest pain", ["shortness of breath","breathless","sweating","radiating","left arm","jaw"]),
    ("slurred speech", []),
    ("face droop", []),
    ("one side weak", []),
    ("worst headache", []),
    ("severe bleeding", []),
]
MEDICAL_KEYWORDS = [
    "pain","ache","dizzy","fall","bleed","cut","chest","breath","shortness of breath",
    "faint","numb","tingling","slurred speech","confusion","swelling","fever","vomit",
    "black stool","pressure","radiating","jaw","left arm","headache","weakness","puffy",
    "stiffness","sore","rash"
]

def _kw_sieve(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in MEDICAL_KEYWORDS)

def _emergency_hit(text: str) -> bool:
    t = text.lower()
    for main, alts in EMERGENCY_PATTERNS:
        if main in t and (not alts or any(a in t for a in alts)):
            return True
    return False


SYSTEM_CLASSIFIER = """You classify a single user message.
Return ONLY JSON with keys:
intent: one of ["smalltalk","medical","emergency_candidate","routine_checkin"]
essence: short noun phrase for the main topic, like "lower back pain" or "cookies"
red_flags: array of strings for any dangerous signals present
confidence: number 0..1 for your intent decision
No extra text."""
SYSTEM_RESPONDER_SMALLTALK = (
    "You are a brief, friendly companion. No medical opinions. One short reply. "
    "1–2 short sentences max. Be respectful and warm, like a caring nurse. "
    "Prefer a gentle open question unless the user signaled the end of discussion."
)
SYSTEM_RESPONDER_MEDICAL = """You are a cautious health check-in assistant for older adults.
Never diagnose. Ask focused follow-ups using OLD CARTS: Onset, Location, Duration, Character, Aggravating/Relieving, Radiation, Timing, Severity(0-10).
Be concise. 2–3 short sentences. Avoid medical jargon.
Patient profile and last notes may follow after a delimiter."""
SYSTEM_SAFETY = """You judge the reply and create a storage summary.
Return ONLY JSON with:
medically_relevant: boolean
emergency: boolean
safety_ok: boolean
db_summary: string"""


def _or_chat(model: str, system: str, user: str, response_json: bool=False) -> str:
    headers = {
        "Authorization": f"Bearer {OR_KEY}",
        "HTTP-Referer": "https://local.hackathon",
        "X-Title": "AI Nurse MVP",
    }
    payload: Dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    if response_json:
        payload["response_format"] = {"type": "json_object"}

    print(f"\n[LLM CALL] model={model}")
    print(f"[SYSTEM]\n{system}")
    print(f"[USER]\n{user}")
    r = httpx.post(f"{OR_BASE}/chat/completions", headers=headers, json=payload, timeout=60.0)
    r.raise_for_status()
    msg = r.json()["choices"][0]["message"]["content"]
    print(f"[RAW LLM OUTPUT]\n{msg}\n")
    return msg

# ---------- pipeline ----------
def _run_pipeline(user_text: str, profile: Dict[str, Any] | None = None, recent_notes: str = "") -> None:
    print("="*72)
    print(f"Input: {user_text}")

    force_med = _kw_sieve(user_text)
    emerg = _emergency_hit(user_text)
    print(f"- keyword_sieve: {force_med}")
    print(f"- emergency_pattern: {emerg}")

    # 1) classify
    cls_raw = _or_chat(MODEL_CLS, SYSTEM_CLASSIFIER, user_text, response_json=True)
    try:
        cls = json.loads(cls_raw)
    except json.JSONDecodeError:
        cls = {"intent":"smalltalk","essence":"","red_flags":[],"confidence":0.0}
        print("[WARN] classifier JSON parse failed. Fallback -> smalltalk")

    intent = cls.get("intent","smalltalk")
    if emerg:
        intent = "emergency_candidate"
        cls.setdefault("red_flags",[]).append("emergency_pattern_hit")
    elif force_med and intent == "smalltalk":
        intent = "medical"

    print(f"- classifier.intent: {cls.get('intent')}  -> final.intent: {intent}")
    print(f"- classifier.essence: {cls.get('essence')}")
    print(f"- classifier.red_flags: {cls.get('red_flags')}")
    print(f"- classifier.confidence: {cls.get('confidence')}")

    # 2) responder
    profile_blob = json.dumps(profile or {}, ensure_ascii=False)
    context_block = f"\n---\nPROFILE: {profile_blob}\nNOTES: {recent_notes or ''}"
    if intent in ("medical","emergency_candidate"):
        rsp_text = _or_chat(MODEL_RSP, SYSTEM_RESPONDER_MEDICAL, user_text + context_block, response_json=False)
    elif intent == "routine_checkin":
        rsp_text = _or_chat(MODEL_RSP, SYSTEM_RESPONDER_SMALLTALK, "How are you feeling today?", response_json=False)
    else:
        rsp_text = _or_chat(MODEL_RSP, SYSTEM_RESPONDER_SMALLTALK, user_text, response_json=False)

    print(f"- responder.reply:\n{rsp_text}")

    # 3) safety + summary
    safety_input = f"USER:\n{user_text}\n---\nASSISTANT:\n{rsp_text}"
    s_raw = _or_chat(MODEL_SFT, SYSTEM_SAFETY, safety_input, response_json=True)
    try:
        s = json.loads(s_raw)
    except json.JSONDecodeError:
        s = {"medically_relevant": False, "emergency": False, "safety_ok": True, "db_summary": "N/A"}
        print("[WARN] safety JSON parse failed. Fallback flags set.")

    medically_relevant = bool(s.get("medically_relevant", False)) or (intent in ("medical","emergency_candidate"))
    emergency_flag = bool(s.get("emergency", False)) or emerg

    print(f"- safety.medically_relevant: {s.get('medically_relevant')} -> store={medically_relevant}")
    print(f"- safety.emergency: {s.get('emergency')} or gate={emerg} -> emergency={emergency_flag}")
    print(f"- safety.safety_ok: {s.get('safety_ok')}")
    print(f"- safety.db_summary: {s.get('db_summary')}")
    if medically_relevant or emergency_flag:
        print("[STORE] would store encounter summary and reply")
    else:
        print("[SKIP STORE] smalltalk or non-medical")

# ---------- public API ----------
def process_text(text: Optional[str]) -> None:
    if text is None:
        print("agent.process_text called with no text")
        return
    print("agent.process_text called with:", text)
    _run_pipeline(
        text,
        profile={"age": 82, "diagnoses": ["hypertension"]},
        recent_notes="Baseline: mild chronic knee pain."
    )

def simple_notify() -> None:
    """Simple helper to show agent is reachable."""
    print("agent.simple_notify called")
