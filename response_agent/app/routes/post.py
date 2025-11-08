from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse

import json

# import agent functions
from ..agent.main import process_text

router = APIRouter()


@router.post("/post")
async def receive_post(request: Request):
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
        # print("response_agent received text:", received_text[:200])
        response = process_text(received_text)
    else:
        print("response_agent received non-text payload (len=", len(body), ")")
    return PlainTextResponse(response)
