from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse
import httpx

router = APIRouter()


@router.post("/post")
async def receive_post(request: Request):
    print("RECEIVED POST")

    # Read incoming body
    body = await request.body()
    content_type = request.headers.get("content-type", "application/json")

    # Forward to extraction_agent (increase timeout to allow slower downstream responses)
    # You can tune this value or replace with httpx.Timeout for finer control.
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "http://extraction_agent:8001/post",
            content=body,
            headers={"Content-Type": content_type},
        )

    print(f"Forwarded to extraction_agent, status={resp.status_code}")

    return PlainTextResponse(resp.text)
