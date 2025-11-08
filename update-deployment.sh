#!/bin/bash

echo "� Finding Caddy container..."
CADDY_CONTAINER=$(docker ps --filter "name=caddy" --format "{{.Names}}" | head -1)
echo "Found: $CADDY_CONTAINER"

if [ -z "$CADDY_CONTAINER" ]; then
    echo "⚠️  Caddy container not found. Starting it..."
    docker compose -f docker-compose.prod.yml up -d caddy
    CADDY_CONTAINER=$(docker ps --filter "name=caddy" --format "{{.Names}}" | head -1)
fi

echo ""
echo "📋 Current Caddy configuration:"
docker exec $CADDY_CONTAINER cat /etc/caddy/Caddyfile | grep -A 5 "handle"

echo ""
echo "🔄 Reloading Caddy with updated configuration..."
docker exec $CADDY_CONTAINER caddy reload --config /etc/caddy/Caddyfile

echo ""
echo "🏗️  Rebuilding frontend with environment variables..."
export NEXT_PUBLIC_BACKEND_URL="https://hygieiai.chickenkiller.com/api"
export NEXT_PUBLIC_SCHEDULE_AGENT_URL="https://hygieiai.chickenkiller.com/api"

docker compose -f docker-compose.prod.yml build --no-cache frontend

echo "🚀 Restarting frontend service..."
docker compose -f docker-compose.prod.yml up -d frontend

echo "✅ Deployment updated!"
echo ""
echo "🧪 Testing schedule agent directly (port 8004)..."
curl -s http://localhost:8004/schedule/start?service=dentist

echo ""
echo ""
echo "🧪 Testing schedule agent through Caddy..."
curl -s https://hygieiai.chickenkiller.com/api/schedule/start?service=dentist

echo ""
echo ""
echo "🔍 Verifying environment variables in frontend..."
docker compose -f docker-compose.prod.yml exec frontend env | grep NEXT_PUBLIC

echo ""
echo "📋 Checking Caddy logs for errors..."
docker logs $CADDY_CONTAINER --tail 20
