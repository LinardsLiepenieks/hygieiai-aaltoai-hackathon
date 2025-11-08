from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# import and include routers
from .routes.post import router as post_router

app = FastAPI(title="schedule_agent")

# Allow any origin for development convenience
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include router immediately (not in startup event)
app.include_router(post_router)


@app.get("/")
async def root():
    return {"message": "Hello from schedule agent"}


@app.get("/health")
async def health():
    return {"status": "ok"}
