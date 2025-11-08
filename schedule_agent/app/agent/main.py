"""
schedule_agent: LLM-driven appointment scheduler.
- Initiates conversation
- Uses OpenRouter to steer dialog
- Only books exact ISO slots from AVAILABILITY
- Returns plain JSON to the frontend
"""

from __future__ import annotations
import os, uuid, json
from typing import Dict, List, Optional
from datetime import datetime
import httpx

OR_KEY = os.getenv("OPENROUTER_API_KEY")
OR_BASE = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

MODEL = os.getenv("MODEL_SCHEDULER", "meta-llama/llama-3.1-70b-instruct")

# ---- demo data (local ISO "YYYY-MM-DDTHH:MM") ----
AVAILABILITY: Dict[str, List[str]] = {
    "dentist": [
        "2025-11-09T10:00",
        "2025-11-09T14:30",
        "2025-11-10T09:00",
        "2025-11-10T13:00",
        "2025-11-11T11:00",
    ],
    "physio": [
        "2025-11-09T16:00",
        "2025-11-10T10:30",
        "2025-11-11T09:00",
        "2025-11-12T15:00",
    ],
    "checkup": [
        "2025-11-09T11:30",
        "2025-11-10T08:30",
        "2025-11-10T15:00",
        "2025-11-12T09:30",
    ],
}

SESSIONS: Dict[str, Dict] = {}  # in-memory state

ALLOWED_SERVICES = {"dentist", "physio", "checkup"}


def _normalize_service(s: Optional[str]) -> str:
    if not s:
        return "dentist"
    s = s.strip().lower()
    if "physio" in s:
        return "physio"
    if "dent" in s:
        return "dentist"
    if "check" in s or "gp" in s or "doctor" in s:
        return "checkup"
    return "dentist"


def _detect_service(text: str) -> Optional[str]:
    t = text.lower()
    if "dent" in t:
        return "dentist"
    if "physio" in t or "physiother" in t:
        return "physio"
    if "checkup" in t or "check up" in t or "gp" in t or "doctor" in t:
        return "checkup"
    return None


SYSTEM = """You are a persistent, polite scheduling assistant for older adults.
Goal: schedule an appointment. Keep replies short, clear, and friendly.

You will ALWAYS return ONLY JSON with keys:
- reply: string
- intent: one of ["propose","ask","confirm","finalize","smalltalk_nudge"]
- service: "dentist" or "physio" or "checkup"
- when_iso: string or null  // exact ISO from the availability list if proposing/confirming

Rules:
- Use ONLY slots shown under AVAILABILITY_ISO for that service. Do not invent times.
- If user gives a time not available, acknowledge and propose 2–3 next available slots.
- If user is off-topic, gently steer back (intent="smalltalk_nudge").
- When a valid time is agreed, set intent="finalize" and include when_iso.
- No extra text outside JSON.
"""


def _fmt(dt: str) -> str:
    return datetime.fromisoformat(dt).strftime("%a %d %b %H:%M")


def _context(service: str) -> str:
    slots = "\n".join(AVAILABILITY.get(service, []))
    return f"SERVICE: {service}\nAVAILABILITY_ISO:\n{slots or '(none)'}"


def _or_chat_json(system: str, user: str) -> Optional[dict]:
    if not OR_KEY:
        return None
    headers = {
        "Authorization": f"Bearer {OR_KEY}",
        "HTTP-Referer": os.getenv("OPENROUTER_REFERER", "http://local.scheduling"),
        "X-Title": os.getenv("OPENROUTER_TITLE", "Schedule Agent"),
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "response_format": {"type": "json_object"},
    }
    r = httpx.post(
        f"{OR_BASE}/chat/completions", headers=headers, json=payload, timeout=60
    )
    r.raise_for_status()
    raw = r.json()["choices"][0]["message"]["content"]
    try:
        return json.loads(raw)
    except Exception:
        return None


def _consume_slot(service: str, iso: str) -> None:
    if iso in AVAILABILITY.get(service, []):
        AVAILABILITY[service].remove(iso)


def _or_chat_json_ctx_history(
    system: str, context: str, history: list[dict]
) -> Optional[dict]:
    if not OR_KEY:
        return None
    headers = {
        "Authorization": f"Bearer {OR_KEY}",
        "HTTP-Referer": os.getenv("OPENROUTER_REFERER", "http://local.scheduling"),
        "X-Title": os.getenv("OPENROUTER_TITLE", "Schedule Agent"),
    }
    # Cap history to avoid long prompts
    hist = history[-16:] if len(history) > 16 else history
    payload = {
        "model": MODEL,
        "messages": (
            [{"role": "system", "content": system}]
            + [{"role": "user", "content": context}]
            + hist
        ),
        "response_format": {"type": "json_object"},
    }
    r = httpx.post(
        f"{OR_BASE}/chat/completions", headers=headers, json=payload, timeout=60
    )
    r.raise_for_status()
    raw = r.json()["choices"][0]["message"]["content"]
    try:
        return json.loads(raw)
    except Exception:
        return None


# --- replace start_session() ---
def start_session(service: Optional[str] = None) -> Dict:
    svc = _normalize_service(service)
    if svc not in ALLOWED_SERVICES:
        svc = "dentist"
    sid = uuid.uuid4().hex[:8]
    SESSIONS[sid] = {"service": svc, "history": []}

    ctx = _context(svc)
    # Ask the model to open the conversation
    resp = _or_chat_json_ctx_history(
        SYSTEM, ctx, [{"role": "user", "content": "BEGIN OUTREACH"}]  # seed turn
    )

    if not resp:
        opts = [_fmt(s) for s in AVAILABILITY[svc][:3]]
        reply = f"Hello, it’s time to schedule your {svc} appointment. Next times: {', '.join(opts)}. Which works for you?"
    else:
        reply = (resp.get("reply") or "").strip() or f"Hello, let’s pick a {svc} time."

    # record assistant turn
    SESSIONS[sid]["history"].append({"role": "assistant", "content": reply})
    return {"session_id": sid, "reply": reply, "status": "ongoing", "service": svc}


# --- replace handle_user() ---
def handle_user(session_id: str, text: str) -> Dict:
    if not session_id or session_id not in SESSIONS:
        return {"error": "invalid_session"}

    svc = SESSIONS[session_id].get("service") or "dentist"
    hist: list[dict] = SESSIONS[session_id].setdefault("history", [])

    # append user turn
    hist.append({"role": "user", "content": text})
    ctx = _context(svc)

    resp = _or_chat_json_ctx_history(SYSTEM, ctx, hist)
    if not resp:
        # fallback: propose next few
        opts = [_fmt(s) for s in AVAILABILITY[svc][:3]]
        reply = f"I couldn’t check that time. Available {svc} slots: {', '.join(opts)}. Which should I book?"
        hist.append({"role": "assistant", "content": reply})
        return {
            "session_id": session_id,
            "reply": reply,
            "status": "ongoing",
            "service": svc,
        }

    # allow model to switch service explicitly
    llm_service = resp.get("service")
    if llm_service in ALLOWED_SERVICES and llm_service != svc:
        svc = llm_service
        SESSIONS[session_id]["service"] = svc
        ctx = _context(svc)  # regenerated next call

    intent = str(resp.get("intent", "ask"))
    when_iso = resp.get("when_iso")
    reply = (resp.get("reply") or "Which time works for you?").strip()

    # finalize only if exact ISO slot exists
    if intent in ("confirm", "finalize") and isinstance(when_iso, str):
        if when_iso in AVAILABILITY.get(svc, []):
            _consume_slot(svc, when_iso)
            when_text = _fmt(when_iso)
            final = f"Okay, your appointment has been made for {svc} on {when_text}. This demo will now reset."
            hist.append({"role": "assistant", "content": final})
            SESSIONS.pop(session_id, None)
            return {
                "session_id": session_id,
                "reply": final,
                "status": "confirmed",
                "service": svc,
            }
        else:
            opts = [_fmt(s) for s in AVAILABILITY[svc][:3]]
            reply = f"That time isn’t available. Next {svc} slots: {', '.join(opts)}. Which should I book?"

    # keep going
    hist.append({"role": "assistant", "content": reply})
    # trim history to protect context length
    if len(hist) > 24:
        SESSIONS[session_id]["history"] = hist[-24:]
    return {
        "session_id": session_id,
        "reply": reply,
        "status": "ongoing",
        "service": svc,
    }
