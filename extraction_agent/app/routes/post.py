from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse
import json

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

    if received_text is not None:
        # call into agent to process the text
        try:
            process_text(received_text)
        except Exception as e:
            print("agent.process_text failed:", e)
    else:
        print("Extraction agent received non-text payload (len=", len(body), ")")
        # still call a simple notify so we can see the agent run
        try:
            simple_notify()
        except Exception as e:
            print("agent.simple_notify failed:", e)

    return PlainTextResponse("RECIEVED POST")
