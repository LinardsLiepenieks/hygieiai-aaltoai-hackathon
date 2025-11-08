#!/bin/bash
# Quick frontend rebuild script for production

echo "🔄 Rebuilding Frontend for Production"
echo "======================================"

# Stop frontend container
echo "🛑 Stopping frontend container..."
docker compose -f docker-compose.prod.yml stop frontend

# Remove old frontend image
echo "🗑️  Removing old frontend image..."
docker rmi hygieiai-aaltoai-hackathon-frontend 2>/dev/null || true

# Set environment variables
echo "🔧 Setting environment variables..."
export NEXT_PUBLIC_ELEVENLABS_API_KEY="sk_5481606b3a245b139ed118cf775c1fc9ce2f03b30500dacc"
export NEXT_PUBLIC_BACKEND_URL="https://hygieiai.chickenkiller.com/api"
export NEXT_PUBLIC_SCHEDULE_AGENT_URL="https://hygieiai.chickenkiller.com/api"

echo "   NEXT_PUBLIC_BACKEND_URL=$NEXT_PUBLIC_BACKEND_URL"
echo "   NEXT_PUBLIC_SCHEDULE_AGENT_URL=$NEXT_PUBLIC_SCHEDULE_AGENT_URL"

# Rebuild frontend with no cache
echo "🏗️  Building frontend..."
docker compose -f docker-compose.prod.yml build --no-cache frontend

# Start frontend
echo "🚀 Starting frontend..."
docker compose -f docker-compose.prod.yml up -d frontend

# Wait for service
echo "⏳ Waiting for frontend to start..."
sleep 10

# Check if running
if docker ps | grep -q hygieiai-aaltoai-hackathon-frontend; then
    echo "✅ Frontend is running"
else
    echo "❌ Frontend failed to start"
    echo "📋 Recent logs:"
    docker compose -f docker-compose.prod.yml logs --tail=20 frontend
    exit 1
fi

echo ""
echo "🎉 Frontend rebuild complete!"
echo "🌐 Visit: https://hygieiai.chickenkiller.com"
echo ""
echo "📋 Check logs: docker compose -f docker-compose.prod.yml logs -f frontend"
