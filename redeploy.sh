#!/bin/bash
# Quick redeploy script - run this on Datacrunch after pulling latest changes

echo "🔄 Quick Redeploy Script"
echo "========================"

# Get public IP
PUBLIC_IP=$(curl -s ifconfig.me)
echo "📍 Public IP: $PUBLIC_IP"

# Stop existing containers
echo "🛑 Stopping containers..."
docker compose -f docker-compose.prod.yml down

# Remove old frontend image to force rebuild
echo "🗑️  Removing old frontend image..."
docker rmi hygieiai-aaltoai-hackathon-frontend 2>/dev/null || true

# Set environment variables
echo "🔧 Setting environment variables..."
export NEXT_PUBLIC_ELEVENLABS_API_KEY="sk_5481606b3a245b139ed118cf775c1fc9ce2f03b30500dacc"
export NEXT_PUBLIC_BACKEND_URL="http://${PUBLIC_IP}:8000"
export NEXT_PUBLIC_SCHEDULE_AGENT_URL="http://${PUBLIC_IP}:8004"

echo "   NEXT_PUBLIC_BACKEND_URL=$NEXT_PUBLIC_BACKEND_URL"
echo "   NEXT_PUBLIC_SCHEDULE_AGENT_URL=$NEXT_PUBLIC_SCHEDULE_AGENT_URL"
echo "   NEXT_PUBLIC_ELEVENLABS_API_KEY=sk_****...${NEXT_PUBLIC_ELEVENLABS_API_KEY: -4}"

# Build and start
echo "🏗️  Building and starting services..."
docker compose -f docker-compose.prod.yml build --no-cache frontend
docker compose -f docker-compose.prod.yml up -d

# Wait for services
echo "⏳ Waiting for services to start..."
sleep 15

# Health checks
echo "🏥 Health checks..."
for port in 8000 8001 8002 8003 8004; do
    if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo "   ✅ Port $port is healthy"
    else
        echo "   ❌ Port $port is not responding"
    fi
done

echo ""
echo "🎉 Deployment complete!"
echo "========================"
echo "🌐 Access your app at: http://${PUBLIC_IP}:3000"
echo ""
echo "📋 Check logs: docker compose -f docker-compose.prod.yml logs -f frontend"
echo "🔍 Verify env vars in container:"
echo "   docker compose -f docker-compose.prod.yml exec frontend env | grep NEXT_PUBLIC"
