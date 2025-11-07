from fastapi import FastAPI

app = FastAPI(title="extraction_agent")


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
