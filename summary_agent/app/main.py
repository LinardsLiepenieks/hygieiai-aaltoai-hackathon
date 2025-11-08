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

FINAL_MESSAGE = ""


def setFinalMessage(summary):
    global FINAL_MESSAGE
    print("SETTING SUMMARY", summary)
    FINAL_MESSAGE = summary


@app.on_event("startup")
async def startup_event():
    app.include_router(post_router)


@app.get("/")
async def root():
    return {"message": "Hello from summary agent"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/final-message")
async def final_message():
    """Return the FINAL_MESSAGE variable for quick access."""
    return {"final_message": FINAL_MESSAGE}
