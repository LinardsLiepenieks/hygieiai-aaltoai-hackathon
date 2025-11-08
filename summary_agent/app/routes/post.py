from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse
from ..agent.main import process_text
import json

router = APIRouter()


@router.post("/post")
async def receive_post(request: Request):
    from ..main import setFinalMessage

    body = await request.body()
    content_type = request.headers.get("content-type", "application/octet-stream")

    received_text = None
    try:
        if content_type and "application/json" in content_type:
            try:
                data = json.loads(body.decode("utf-8", errors="replace"))
                if isinstance(data, dict):
                    received_text = data.get("text")
            except Exception:
                received_text = None
        elif content_type and content_type.startswith("text/"):
            received_text = body.decode("utf-8", errors="replace")
    except Exception:
        received_text = None

    if received_text is not None:
        # print("summary_agent received text:", received_text[:200])
        # Build JSON payload expected by summary_agent.process_text
        user_msg = None
        assistant_text = None
        try:
            # if the request was JSON we may have access to the parsed `data`
            if "data" in locals() and isinstance(data, dict):
                assistant_text = (
                    data.get("text") or data.get("assistant_text") or received_text
                )
                user_msg = (
                    data.get("user")
                    or data.get("user_message")
                    or data.get("user_text")
                )
        except Exception:
            assistant_text = received_text

        payload_obj = {
            "user_text": user_msg or "",
            "assistant_text": assistant_text or received_text,
            "emergency_gate_hit": False,
        }

        try:
            summary = process_text(json.dumps(payload_obj))
            setFinalMessage(summary=summary)
        except Exception as e:
            print("summary_agent.process_text failed:", e)
            summary = None
    else:
        print("summary_agent received non-text payload (len=", len(body), ")")

    return PlainTextResponse("RECEIVED POST")
