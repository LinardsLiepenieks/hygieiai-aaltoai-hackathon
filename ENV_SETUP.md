# Environment Variables Setup

## Overview

All agent services (extraction_agent, response_agent, schedule_agent, summary_agent) now use centralized environment variables defined in the `.env` file at the root of the project.

## Setup Instructions

1. **Copy the example environment file:**

   ```bash
   cp .env.example .env
   ```

2. **Update the `.env` file with your actual values:**
   - Replace `your-openrouter-api-key-here` with your actual OpenRouter API key
   - Adjust model names if needed
   - Customize other settings as required

## Environment Variables

### API Configuration

- `OPENROUTER_API_KEY`: Your OpenRouter API key (required)
- `OPENROUTER_BASE_URL`: OpenRouter API base URL (default: `https://openrouter.ai/api/v1`)
- `OPENROUTER_REFERER`: HTTP Referer header for OpenRouter (default: `https://hack.local`)
- `OPENROUTER_TITLE`: Application title for OpenRouter (default: `HygieiAI`)

### Model Configuration

- `MODEL_CLASSIFIER`: Model for classification tasks (default: `meta-llama/llama-3.1-70b-instruct`)
- `MODEL_RESPONDER`: Model for response generation (default: `meta-llama/llama-3.1-70b-instruct`)
- `MODEL_SAFETY`: Model for safety checks (default: `meta-llama/llama-3.1-70b-instruct`)
- `MODEL_SCHEDULER`: Model for scheduling (default: `meta-llama/llama-3.1-70b-instruct`)

## Docker Compose Integration

The `docker-compose.yml` file has been updated to automatically load the `.env` file for all agent services:

```yaml
extraction_agent:
  env_file:
    - .env
```

This ensures all agents have access to the centralized configuration.

## Security Notes

- **Never commit the `.env` file** to version control (it's already in `.gitignore`)
- The `.env.example` file is safe to commit and serves as a template
- Keep your API keys secure and rotate them regularly
- Use different API keys for development, staging, and production environments

## Troubleshooting

### Missing API Key Error

If you see `Missing OPENROUTER_API_KEY environment variable`, ensure:

1. The `.env` file exists in the project root
2. The `OPENROUTER_API_KEY` is set in the `.env` file
3. You've rebuilt the Docker containers: `docker compose up --build`

### Changes Not Taking Effect

After modifying the `.env` file:

1. Restart the Docker containers: `docker compose restart`
2. Or rebuild completely: `docker compose down && docker compose up --build`

## Migration Notes

All hardcoded variables have been removed from the following files:

- `extraction_agent/app/agent/main.py`
- `response_agent/app/agent/main.py`
- `schedule_agent/app/agent/main.py`
- `summary_agent/app/agent/main.py`

These files now read configuration from environment variables with sensible defaults.
