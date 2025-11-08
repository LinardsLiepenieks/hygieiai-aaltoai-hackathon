#!/bin/bash

echo "🔄 Reloading Caddy with updated configuration..."
docker exec hygieiai-aaltoai-hackathon-caddy-1 caddy reload --config /etc/caddy/Caddyfile

echo "🏗️  Rebuilding frontend with environment variables..."
export NEXT_PUBLIC_BACKEND_URL="https://hygieiai.chickenkiller.com/api"
export NEXT_PUBLIC_SCHEDULE_AGENT_URL="https://hygieiai.chickenkiller.com/api"

docker compose -f docker-compose.prod.yml build --no-cache frontend

echo "🚀 Restarting frontend service..."
docker compose -f docker-compose.prod.yml up -d frontend

echo "✅ Deployment updated!"
echo ""
echo "🧪 Testing schedule agent..."
curl -s https://hygieiai.chickenkiller.com/api/schedule/start?service=dentist | jq .

echo ""
echo "🔍 Verifying environment variables in frontend..."
docker compose -f docker-compose.prod.yml exec frontend env | grep NEXT_PUBLIC
