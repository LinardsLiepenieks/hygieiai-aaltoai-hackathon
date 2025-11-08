#!/bin/bash
# Production redeploy script - run this on Datacrunch after pulling latest changes

echo "🔄 Production Redeploy Script"
echo "============================="

# Get public IP
PUBLIC_IP=$(curl -s ifconfig.me)
echo "📍 Public IP: $PUBLIC_IP"

# Check if user has a domain configured
echo ""
echo "🌐 HTTPS Setup (Optional)"
echo "-------------------------"
echo "For HTTPS, you need a domain name (e.g., hygiei.example.com)"
echo "Note: SSL certificates don't work with IP addresses"
echo ""
read -p "Do you have a domain configured? (y/n) [default: n]: " HAS_DOMAIN
HAS_DOMAIN=${HAS_DOMAIN:-n}

if [ "$HAS_DOMAIN" = "y" ] || [ "$HAS_DOMAIN" = "Y" ]; then
    read -p "Enter your domain (e.g., hygiei.example.com): " DOMAIN
    
    echo ""
    echo "⚠️  IMPORTANT: Update Caddyfile before continuing!"
    echo "   1. Edit Caddyfile"
    echo "   2. Uncomment the production domain section"
    echo "   3. Replace YOUR_DOMAIN.com with: $DOMAIN"
    echo "   4. Update email for SSL notifications"
    echo ""
    read -p "Press ENTER when ready, or Ctrl+C to exit and configure Caddyfile first..."
    
    # Use HTTPS URLs
    BASE_URL="https://${DOMAIN}"
    API_URL="https://${DOMAIN}/api"  # Using /api path instead of subdomain
    USE_HTTPS=true
else
    # Use HTTP with IP
    BASE_URL="http://${PUBLIC_IP}:3000"
    API_URL="http://${PUBLIC_IP}:8000"
    USE_HTTPS=false
    
    echo "📋 Using HTTP mode (no SSL)"
    echo "   Frontend will be accessible via Caddy on port 3000"
fi

# Stop existing containers
echo ""
echo "🛑 Stopping containers..."
docker compose -f docker-compose.prod.yml down

# Remove old frontend image to force rebuild
echo "🗑️  Removing old frontend image..."
docker rmi hygieiai-aaltoai-hackathon-frontend 2>/dev/null || true

# Set environment variables
echo "🔧 Setting environment variables..."
export NEXT_PUBLIC_ELEVENLABS_API_KEY="sk_5481606b3a245b139ed118cf775c1fc9ce2f03b30500dacc"
export NEXT_PUBLIC_BACKEND_URL="${API_URL}"
export NEXT_PUBLIC_SCHEDULE_AGENT_URL="${API_URL}"

if [ "$USE_HTTPS" = true ]; then
    export DOMAIN="${DOMAIN}"
fi

echo "   NEXT_PUBLIC_BACKEND_URL=$NEXT_PUBLIC_BACKEND_URL"
echo "   NEXT_PUBLIC_SCHEDULE_AGENT_URL=$NEXT_PUBLIC_SCHEDULE_AGENT_URL"
echo "   NEXT_PUBLIC_ELEVENLABS_API_KEY=sk_****...${NEXT_PUBLIC_ELEVENLABS_API_KEY: -4}"

# Build and start
echo "🏗️  Building and starting services..."
docker compose -f docker-compose.prod.yml build --no-cache frontend
docker compose -f docker-compose.prod.yml up -d

# Wait for services
echo "⏳ Waiting for services to start..."
sleep 20

# Health checks
echo "🏥 Health checks..."
for port in 8000 8001 8002 8003 8004; do
    if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo "   ✅ Port $port is healthy"
    else
        echo "   ❌ Port $port is not responding"
    fi
done

# Check Caddy
if docker ps | grep -q hygiei-caddy; then
    echo "   ✅ Caddy reverse proxy is running"
    
    if [ "$USE_HTTPS" = true ]; then
        echo ""
        echo "🔒 Waiting for SSL certificate acquisition..."
        echo "   (This may take 30-60 seconds on first run)"
        sleep 10
        
        echo ""
        echo "📋 Recent Caddy logs:"
        docker logs hygiei-caddy 2>&1 | tail -n 15
    fi
else
    echo "   ⚠️  Caddy is not running (check docker logs)"
fi

echo ""
echo "🎉 Deployment complete!"
echo "======================="

if [ "$USE_HTTPS" = true ]; then
    echo "🌐 Frontend: $BASE_URL"
    echo "🔒 API: $API_URL"
    echo ""
    echo "🔐 SSL Status:"
    echo "   Visit your domain in a browser to verify HTTPS"
    echo "   Check certificate: curl -vI $BASE_URL 2>&1 | grep -i 'subject\\|issuer'"
    echo ""
    echo "⚠️  If SSL fails:"
    echo "   • Verify DNS points to $PUBLIC_IP (nslookup $DOMAIN)"
    echo "   • Ensure ports 80 and 443 are open"
    echo "   • Check Caddy logs: docker logs hygiei-caddy -f"
else
    echo "🌐 Frontend: $BASE_URL"
    echo "🌐 API: $API_URL"
    echo ""
    echo "🔓 HTTP Mode (No SSL)"
    echo "   Your app is accessible but not encrypted"
    echo "   To enable HTTPS later, get a domain and rerun this script"
fi

echo ""
echo "📋 Useful Commands:"
echo "   • All logs: docker compose -f docker-compose.prod.yml logs -f"
echo "   • Caddy logs: docker logs hygiei-caddy -f"
echo "   • Frontend logs: docker compose -f docker-compose.prod.yml logs -f frontend"
echo "   • Check env: docker compose -f docker-compose.prod.yml exec frontend env | grep NEXT_PUBLIC"
echo "   • Restart: docker compose -f docker-compose.prod.yml restart"
