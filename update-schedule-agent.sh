#!/bin/bash
# Quick schedule_agent rebuild script for production

echo "🔄 Updating Schedule Agent"
echo "=========================="

# Rebuild and restart schedule_agent
echo "🏗️  Rebuilding schedule_agent..."
docker compose -f docker-compose.prod.yml up -d --build --no-deps schedule_agent

# Wait for service
echo "⏳ Waiting for schedule_agent to start..."
sleep 5

# Check if running
if docker ps | grep -q schedule_agent; then
    echo "✅ Schedule agent is running"
    
    # Health check
    echo "🏥 Health check..."
    sleep 2
    if curl -s http://localhost:8004/health > /dev/null 2>&1; then
        echo "✅ Schedule agent is healthy"
    else
        echo "⚠️  Schedule agent health check failed"
    fi
else
    echo "❌ Schedule agent failed to start"
    echo "📋 Recent logs:"
    docker compose -f docker-compose.prod.yml logs --tail=20 schedule_agent
    exit 1
fi

echo ""
echo "🎉 Schedule agent updated!"
echo "📋 Check logs: docker compose -f docker-compose.prod.yml logs -f schedule_agent"
