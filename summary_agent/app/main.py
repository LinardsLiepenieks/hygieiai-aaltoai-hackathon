from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# import and include routers
from .routes.post import router as post_router

app = FastAPI(title="summary_agent")

# Allow any origin for development convenience
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    app.include_router(post_router)


@app.get("/")
async def root():
    return {"message": "Hello from summary agent"}


@app.get("/health")
async def health():
    return {"status": "ok"}
