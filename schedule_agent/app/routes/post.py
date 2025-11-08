from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from ..agent.main import start_session, handle_user

router = APIRouter()

@router.get("/schedule/start")
async def start():
    return JSONResponse(start_session())

@router.post("/schedule/post")
async def post_root(request: Request):
    try:
        data = await request.json()
    except Exception:
        return PlainTextResponse("invalid json", status_code=400)
    out = handle_user(data.get("session_id"), data.get("text") or "")
    if "error" in out:
        return PlainTextResponse(out["error"], status_code=400)
    return JSONResponse(out)
