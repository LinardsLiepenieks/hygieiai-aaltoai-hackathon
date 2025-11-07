# Compose-based dev setup

This repository contains a minimal Docker Compose setup with three services:

- `frontend` — a barebones Next.js app served on port 3000
- `backend` — a FastAPI app served on port 8000
- `extraction_agent` — a FastAPI app (placeholder) served on port 8001

How to run (requires Docker & docker-compose):

1. Build and start everything:

```bash
docker-compose up --build
```

2. Visit the frontend at http://localhost:3000
   - Backend: http://localhost:8000
   - Extraction agent: http://localhost:8001

Notes:

- The services are intentionally minimal so you can extend them.
- For the frontend, run `npm install` locally to populate node_modules if you plan to develop locally.
- For Python services, edit `requirements.txt` to add dependencies.
