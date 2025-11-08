# 🚀 Datacrunch Deployment Guide

## Pre-Deployment Checklist

### 1. Update Frontend URLs

Replace all hardcoded localhost URLs with environment variables:

**Files to update:**

- [ ] `frontend/src/app/page.tsx` (line 49)
- [ ] `frontend/src/components/ScheduleSidebar.tsx` (lines 31, 63)
- [ ] `frontend/src/app/schedule/start/route.ts` (line 5)
- [ ] `frontend/src/app/schedule/post/route.ts` (line 4)

**Change from:**

```typescript
const res = await fetch('http://localhost:8000/post', {
```

**Change to:**

```typescript
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
const res = await fetch(`${BACKEND_URL}/post`, {
```

### 2. Enable Next.js Standalone Output

Add to `frontend/next.config.ts`:

```typescript
const nextConfig = {
  output: 'standalone',
  // ... rest of config
};
```

### 3. Set Environment Variables on Datacrunch

Create `.env` file with:

```bash
# OpenRouter API Configuration
OPENROUTER_API_KEY=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
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Model Configuration
MODEL_CLASSIFIER=meta-llama/llama-3.1-70b-instruct
MODEL_RESPONDER=meta-llama/llama-3.1-70b-instruct
MODEL_SAFETY=meta-llama/llama-3.1-70b-instruct
MODEL_SCHEDULER=meta-llama/llama-3.1-70b-instruct

# HTTP Referer for OpenRouter
OPENROUTER_REFERER=https://hack.local
OPENROUTER_TITLE=HygieiAI

# Frontend Environment Variables
NEXT_PUBLIC_ELEVENLABS_API_KEY=sk_5481606b3a245b139ed118cf775c1fc9ce2f03b30500dacc
NEXT_PUBLIC_BACKEND_URL=http://YOUR_DATACRUNCH_IP:8000
NEXT_PUBLIC_SCHEDULE_AGENT_URL=http://YOUR_DATACRUNCH_IP:8004
```

## Deployment Steps

### Option 1: Quick Deploy (Development Mode)

```bash
# On Datacrunch instance
git clone YOUR_REPO_URL
cd hygieiai-aaltoai-hackathon

# Copy and configure .env
cp .env.example .env
# Edit .env with your API keys

# Run with docker-compose
docker compose up -d --build
```

### Option 2: Production Deploy (Recommended)

```bash
# On Datacrunch instance
git clone YOUR_REPO_URL
cd hygieiai-aaltoai-hackathon

# Set environment variables
export NEXT_PUBLIC_ELEVENLABS_API_KEY=your_key
export NEXT_PUBLIC_BACKEND_URL=http://$(curl -s ifconfig.me):8000
export NEXT_PUBLIC_SCHEDULE_AGENT_URL=http://$(curl -s ifconfig.me):8004

# Run production build
docker compose -f docker-compose.prod.yml up -d --build
```

## Port Configuration

Make sure these ports are open on Datacrunch:

- **3000** - Frontend (Next.js)
- **8000** - Backend API
- **8001** - Extraction Agent
- **8002** - Summary Agent
- **8003** - Response Agent
- **8004** - Schedule Agent

## Health Checks

After deployment, verify services:

```bash
curl http://YOUR_IP:8000/health
curl http://YOUR_IP:8001/health
curl http://YOUR_IP:8002/health
curl http://YOUR_IP:8003/health
curl http://YOUR_IP:8004/health
curl http://YOUR_IP:3000
```

## Troubleshooting

### CORS Issues

If you see CORS errors, update backend CORS settings to include your Datacrunch IP:

```python
allow_origins=["http://YOUR_DATACRUNCH_IP:3000", "https://YOUR_DOMAIN"]
```

### Container Logs

```bash
docker compose logs -f [service_name]
# Example: docker compose logs -f backend
```

### Restart Services

```bash
docker compose restart
# Or specific service: docker compose restart backend
```

## Security Notes

⚠️ **IMPORTANT**: Before pushing to GitHub:

1. Remove actual API keys from `.env`
2. Use `.env.example` with placeholder values
3. Verify `.env` is in `.gitignore`

## Performance Tips

- Use `--workers 4` for production FastAPI instances (adjust based on CPU cores)
- Consider adding nginx reverse proxy for better performance
- Monitor memory usage: `docker stats`
