from fastapi import FastAPI

app = FastAPI(title="backend")


@app.get("/")
async def root():
    return {"message": "Hello from backend"}


@app.get("/health")
async def health():
    return {"status": "ok"}
