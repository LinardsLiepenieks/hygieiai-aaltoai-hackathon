from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse
import json
import httpx

from ..agent.main import process_text

router = APIRouter()


@router.post("/post")
async def receive_post(request: Request):
    # read body and attempt to extract text
    body = await request.body()
    content_type = request.headers.get("content-type", "application/octet-stream")

    received_text = None
    try:
        if content_type and "application/json" in content_type:
            data = json.loads(body.decode("utf-8", errors="replace"))
            if isinstance(data, dict):
                received_text = data.get("text")
        elif content_type and content_type.startswith("text/"):
            received_text = body.decode("utf-8", errors="replace")
    except Exception:
        pass

    if received_text is None:
        return PlainTextResponse("Missing text in request", status_code=400)

    # call agent
    try:
        # fetch FINAL_MESSAGE from summary_agent and include it as context
        final_msg = None
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    "http://summary_agent:8002/final-message",
                )
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        final_msg = data.get("final_message")
                    except Exception:
                        final_msg = None
        except Exception as e:
            print("Could not fetch FINAL_MESSAGE from summary_agent:", e)

        if final_msg:
            print("Fetched FINAL_MESSAGE from summary_agent:", final_msg)
        print("HERE")
        processed = process_text(received_text, final_msg)
        print("PROCESSED", processed)
    except Exception as e:
        print("agent.process_text failed:", e)
        return PlainTextResponse("agent processing failed", status_code=500)

    if not processed:
        return PlainTextResponse("agent returned no processed text", status_code=500)

    # forward to response_agent
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # include the original received_text as the 'user' field so the
            # response agent receives both the processed output and the
            # original user message.
            resp = await client.post(
                "http://response_agent:8003/post",
                json={"text": processed, "user_message": received_text},
                headers={"Content-Type": "application/json"},
            )
            return PlainTextResponse(resp.text, status_code=resp.status_code)

    except Exception as e:
        print("Failed to contact response_agent:", e)
        return PlainTextResponse(
            "ERROR contacting response_agent: " + str(e), status_code=502
        )
