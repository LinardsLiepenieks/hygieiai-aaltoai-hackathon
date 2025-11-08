#!/bin/bash
# Quick deployment script for Datacrunch

echo "🚀 HygieiAI Deployment Script"
echo "=============================="

# Check if running on Datacrunch or similar environment
if [ -z "$DATACRUNCH_IP" ]; then
    echo "⚠️  DATACRUNCH_IP not set. Using ifconfig to detect..."
    export DATACRUNCH_IP=$(curl -s ifconfig.me 2>/dev/null || echo "localhost")
fi

echo "📍 Detected IP: $DATACRUNCH_IP"

# Set environment variables
export NEXT_PUBLIC_BACKEND_URL="http://${DATACRUNCH_IP}:8000"
export NEXT_PUBLIC_SCHEDULE_AGENT_URL="http://${DATACRUNCH_IP}:8004"

echo "🔧 Environment configured:"
echo "   NEXT_PUBLIC_BACKEND_URL=$NEXT_PUBLIC_BACKEND_URL"
echo "   NEXT_PUBLIC_SCHEDULE_AGENT_URL=$NEXT_PUBLIC_SCHEDULE_AGENT_URL"

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "   Please create .env with your API keys."
    echo "   You can copy from .env.example:"
    echo "   cp .env.example .env"
    exit 1
fi

# Check if API key is set
if grep -q "your-openrouter-api-key-here" .env; then
    echo "⚠️  Warning: Please update OPENROUTER_API_KEY in .env file"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Build and deploy
echo "🏗️  Building and starting services..."
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --build

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Health checks
echo "🏥 Running health checks..."
services=("backend:8000" "extraction_agent:8001" "summary_agent:8002" "response_agent:8003" "schedule_agent:8004")

for service in "${services[@]}"; do
    name="${service%%:*}"
    port="${service##*:}"
    if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo "   ✅ $name is healthy"
    else
        echo "   ❌ $name is not responding"
    fi
done

# Check frontend
if curl -s "http://localhost:3000" > /dev/null 2>&1; then
    echo "   ✅ frontend is running"
else
    echo "   ❌ frontend is not responding"
fi

echo ""
echo "🎉 Deployment complete!"
echo "=============================="
echo "Access your application at:"
echo "   http://${DATACRUNCH_IP}:3000"
echo ""
echo "API endpoints:"
echo "   Backend:         http://${DATACRUNCH_IP}:8000"
echo "   Extraction:      http://${DATACRUNCH_IP}:8001"
echo "   Summary:         http://${DATACRUNCH_IP}:8002"
echo "   Response:        http://${DATACRUNCH_IP}:8003"
echo "   Schedule:        http://${DATACRUNCH_IP}:8004"
echo ""
echo "📋 View logs: docker compose -f docker-compose.prod.yml logs -f"
echo "🛑 Stop services: docker compose -f docker-compose.prod.yml down"
