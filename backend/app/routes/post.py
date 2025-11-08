from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse
import httpx
import json

router = APIRouter()


@router.post("/post")
async def receive_post(request: Request):
    # print to server logs
    print("RECIEVED POST")

    # read incoming body and headers
    body = await request.body()
    content_type = request.headers.get("content-type", "application/octet-stream")

    # try to extract text payload for logging/processing
    received_text = None
    try:
        if content_type and "application/json" in content_type:
            # parse json from raw body and look for 'text' field
            try:
                data = json.loads(body.decode("utf-8", errors="replace"))
                if isinstance(data, dict):
                    received_text = data.get("text")
            except Exception:
                received_text = None
        elif content_type and content_type.startswith("text/"):
            received_text = body.decode("utf-8", errors="replace")
    except Exception:
        # best-effort; ignore parsing errors
        received_text = None

    if received_text is not None:
        print("Received text:", received_text)

    # forward the request to the extraction_agent service
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if received_text is not None:
                # send a simple JSON payload containing the extracted text
                resp = await client.post(
                    "http://extraction_agent:8001/post",
                    json={"text": received_text},
                    headers={"Content-Type": "application/json"},
                )
            else:
                # fallback: forward raw body and original content type
                resp = await client.post(
                    "http://extraction_agent:8001/post",
                    content=body,
                    headers={"Content-Type": content_type},
                )
        print(f"Forwarded to extraction_agent, status={resp.status_code}")
    except Exception as e:
        # log but don't fail the original request
        print("Failed to forward to extraction_agent:", e)

    return PlainTextResponse(resp.text)
