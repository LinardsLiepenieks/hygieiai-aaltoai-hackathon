from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse

import json
import httpx

# import agent functions
from ..agent.main import process_text

router = APIRouter()


@router.post("/post")
async def receive_post(request: Request):
    body = await request.body()
    content_type = request.headers.get("content-type", "application/octet-stream")

    received_text = None
    parsed_json = None
    try:
        if content_type and "application/json" in content_type:
            try:
                data = json.loads(body.decode("utf-8", errors="replace"))
                if isinstance(data, dict):
                    parsed_json = data
                    # prefer the processed text field if provided
                    received_text = data.get("text")
            except Exception:
                received_text = None
        elif content_type and content_type.startswith("text/"):
            received_text = body.decode("utf-8", errors="replace")
    except Exception:
        received_text = None

    if received_text is not None:
        # Build a JSON payload combining the processed text and the original
        # user message (if provided). The agent expects a JSON string like
        # {"text": "...", "intent": "..."} but extra fields are fine.
        user_msg = None
        if parsed_json is not None:
            # extraction_agent forwards original message as 'user' or 'user_message'
            user_msg = parsed_json.get("user") or parsed_json.get("user_message")

        payload_obj = {"text": received_text}
        if user_msg:
            payload_obj["user"] = user_msg

        payload_json = json.dumps(payload_obj)

        # pass JSON string to process_text so the agent can parse intent/etc.
        response = process_text(payload_json)
        # after generating response, forward it to the summary_agent /post endpoint
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    "http://summary_agent:8002/post",
                    json={"text": response, "user_message": user_msg or received_text},
                    headers={"Content-Type": "application/json"},
                )
        except Exception as e:
            # log but keep the main response flow unaffected
            print("Failed to forward generated response to summary_agent:", e)
    else:
        print("response_agent received non-text payload (len=", len(body), ")")
        return PlainTextResponse("Missing text in request", status_code=400)

    return PlainTextResponse(response)
