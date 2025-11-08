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

OR_KEY = "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"
OR_BASE = "https://openrouter.ai/api/v1"

MODEL = "meta-llama/llama-3.1-70b-instruct"

# ---- demo data (local ISO "YYYY-MM-DDTHH:MM") ----
AVAILABILITY: Dict[str, List[str]] = {
    "dentist": [
        "2025-11-09T10:00", "2025-11-09T14:30",
        "2025-11-10T09:00", "2025-11-10T13:00",
        "2025-11-11T11:00",
    ],
    "physio": [
        "2025-11-09T16:00", "2025-11-10T10:30",
        "2025-11-11T09:00", "2025-11-12T15:00",
    ],
}

SESSIONS: Dict[str, Dict] = {}  # in-memory state

SYSTEM = """You are a persistent, polite scheduling assistant for older adults.
Goal: schedule an appointment. Keep replies short, clear, and friendly.

You will ALWAYS return ONLY JSON with keys:
- reply: string  // what you say to the user
- intent: one of ["propose","ask","confirm","finalize","smalltalk_nudge"]
- service: "dentist" or "physio"
- when_iso: string or null  // must be exact ISO "YYYY-MM-DDTHH:MM" from the availability list if proposing/confirming

Rules:
- Use ONLY slots shown under AVAILABILITY_ISO. Do not invent times.
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
        "HTTP-Referer": "http://local.scheduling",
        "X-Title": "Schedule Agent",
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "response_format": {"type": "json_object"},
    }
    r = httpx.post(f"{OR_BASE}/chat/completions", headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    raw = r.json()["choices"][0]["message"]["content"]
    try:
        return json.loads(raw)
    except Exception:
        return None

def _consume_slot(service: str, iso: str) -> None:
    if iso in AVAILABILITY.get(service, []):
        AVAILABILITY[service].remove(iso)

def start_session() -> Dict:
    sid = uuid.uuid4().hex[:8]
    service = "dentist"
    SESSIONS[sid] = {"service": service}

    # Try LLM for first message
    ctx = _context(service)
    resp = _or_chat_json(SYSTEM, f"{ctx}\n\nUSER: BEGIN OUTREACH")
    if not resp:
        # Fallback if no OR key or JSON failure
        opts = [ _fmt(s) for s in AVAILABILITY[service][:3] ]
        reply = f"Hello, it’s time to schedule your {service} visit. Next times: {', '.join(opts)}. Which works for you?"
        return {"session_id": sid, "reply": reply, "status": "ongoing", "service": service}

    reply = str(resp.get("reply","")).strip() or "Hello, let’s pick a time."
    return {"session_id": sid, "reply": reply, "status": "ongoing", "service": service}

def handle_user(session_id: str, text: str) -> Dict:
    if not session_id or session_id not in SESSIONS:
        return {"error": "invalid_session"}
    service = SESSIONS[session_id].get("service") or "dentist"

    # Let LLM drive
    ctx = _context(service)
    resp = _or_chat_json(SYSTEM, f"{ctx}\n\nUSER: {text}")
    if not resp:
        # Fallback: propose next few
        opts = [ _fmt(s) for s in AVAILABILITY[service][:3] ]
        reply = f"I couldn’t check that time. Available {service} slots: {', '.join(opts)}. Which should I book?"
        return {"session_id": session_id, "reply": reply, "status": "ongoing", "service": service}

    intent = str(resp.get("intent","ask"))
    llm_service = resp.get("service")
    if llm_service in ("dentist","physio") and llm_service != service:
        service = llm_service
        SESSIONS[session_id]["service"] = service

    when_iso = resp.get("when_iso")
    reply = str(resp.get("reply","")).strip() or "Which time works for you?"

    if intent in ("confirm","finalize") and isinstance(when_iso, str):
        # Only allow exact available slots
        if when_iso in AVAILABILITY.get(service, []):
            _consume_slot(service, when_iso)
            when_text = _fmt(when_iso)
            final = f"Okay, your appointment has been made for {service} on {when_text}. This demo will now reset."
            SESSIONS.pop(session_id, None)
            return {"session_id": session_id, "reply": final, "status": "confirmed", "service": service}
        else:
            # Not available; nudge with next options
            opts = [ _fmt(s) for s in AVAILABILITY[service][:3] ]
            reply = f"That time isn’t available. Next {service} slots: {', '.join(opts)}. Which should I book?"

    # Keep going
    return {"session_id": session_id, "reply": reply, "status": "ongoing", "service": service}
