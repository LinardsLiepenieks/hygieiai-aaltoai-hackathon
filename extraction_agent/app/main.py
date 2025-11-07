from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# import and include routers
from .routes.post import router as post_router


app = FastAPI(title="extraction_agent")

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
    return {"message": "Hello from extraction agent test"}


@app.get("/extract")
async def extract():
    # placeholder endpoint for extraction work
    return {"extracted": []}


@app.get("/health")
async def health():
    return {"status": "ok"}
