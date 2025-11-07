from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse
import json
import httpx

# import agent functions
from ..agent.main import process_text, simple_notify

router = APIRouter()


@router.post("/post")
async def receive_post(request: Request):
    # read body and attempt to extract text
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

    if received_text is None:
        # Happy-path-only: require text and error if missing
        return PlainTextResponse("Missing text in request", status_code=400)

    # call into agent to process the text and get processed output
    try:
        processed = process_text(received_text)
    except Exception as e:
        print("agent.process_text failed:", e)
        return PlainTextResponse("agent processing failed", status_code=500)

    if not processed:
        return PlainTextResponse("agent returned no processed text", status_code=500)

    # forward the processed text to the response agent and return its response
    try:
        print("SENDING TO RESPONSE")
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "http://response_agent:8003/post",
                json={"text": processed},
                headers={"Content-Type": "application/json"},
            )
            # return response from response_agent directly
            return PlainTextResponse(resp.text, status_code=resp.status_code)
    except Exception as e:
        print("Failed to contact response_agent:", e)
        return PlainTextResponse(
            "ERROR contacting response_agent: " + str(e), status_code=502
        )
    else:
        # Non-text payload: try forwarding the raw body to response_agent
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    "http://response_agent:8003/post",
                    content=body,
                    headers={
                        "Content-Type": content_type or "application/octet-stream"
                    },
                )
                return PlainTextResponse(resp.text, status_code=resp.status_code)
        except Exception as e:
            print("Failed to contact response_agent for non-text payload:", e)
            # fallback to previous behavior: notify locally and acknowledge
            print("Extraction agent received non-text payload (len=", len(body), ")")
            try:
                simple_notify()
            except Exception as e:
                print("agent.simple_notify failed:", e)

    return PlainTextResponse("RECIEVED POST2")
