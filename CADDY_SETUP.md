# 🔒 Caddy HTTPS Setup Guide for Datacrunch

This guide will help you enable automatic HTTPS for your Hygiei AI application using Caddy reverse proxy.

## 📋 Prerequisites

1. **Domain Name**: You need a domain (e.g., `hygiei.yourdomain.com`)
2. **DNS Configuration**: Point your domain's A record to your Datacrunch server IP
3. **Ports Open**: Ensure ports 80 and 443 are accessible on your Datacrunch instance

## 🔧 Setup Steps

### Step 1: Configure DNS

Point your domain to your Datacrunch IP:

```
Type: A Record
Name: @ (or hygiei for subdomain)
Value: YOUR_DATACRUNCH_IP
TTL: 3600 (or auto)
```

For API subdomain (optional):

```
Type: A Record
Name: api
Value: YOUR_DATACRUNCH_IP
TTL: 3600
```

**Wait for DNS propagation** (usually 5-15 minutes, check with `nslookup YOUR_DOMAIN.com`)

### Step 2: Update Caddyfile

Edit `Caddyfile` and replace:

- `YOUR_DOMAIN.com` → Your actual domain (e.g., `hygiei.example.com`)
- `api.YOUR_DOMAIN.com` → Your API subdomain (e.g., `api.hygiei.example.com`)
- `admin@yourdomain.com` → Your email for Let's Encrypt notifications

```bash
# Quick find and replace
sed -i 's/YOUR_DOMAIN.com/hygiei.example.com/g' Caddyfile
sed -i 's/admin@yourdomain.com/your-email@example.com/g' Caddyfile
```

### Step 3: Update Environment Variables

Create or update `.env` file:

```bash
# Frontend URLs (use HTTPS!)
NEXT_PUBLIC_BACKEND_URL=https://api.hygiei.example.com
NEXT_PUBLIC_SCHEDULE_AGENT_URL=https://api.hygiei.example.com

# Or if using main domain for API
NEXT_PUBLIC_BACKEND_URL=https://hygiei.example.com/api
NEXT_PUBLIC_SCHEDULE_AGENT_URL=https://hygiei.example.com/api

# Keep your existing API keys
NEXT_PUBLIC_ELEVENLABS_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here
```

### Step 4: Update Backend CORS Settings

Make sure your backend allows HTTPS origin. Check `backend/app/main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://hygiei.example.com",  # Your production domain
        "https://api.hygiei.example.com",  # API subdomain
        "http://localhost:3000",  # Local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Step 5: Deploy with Caddy

```bash
# Stop existing deployment if running
docker compose -f docker-compose.prod.yml down

# Deploy with Caddy
docker compose -f docker-compose.caddy.yml up -d --build

# Check Caddy logs to verify SSL certificate acquisition
docker logs hygiei-caddy -f
```

### Step 6: Verify HTTPS

1. **Check certificate**: Visit `https://YOUR_DOMAIN.com` in browser
2. **Verify SSL**: Look for padlock icon in address bar
3. **Test API**:
   ```bash
   curl https://api.YOUR_DOMAIN.com/health
   ```

## 🔍 Troubleshooting

### Certificate Not Issued

**Problem**: "Could not get certificate from authority"

**Solutions**:

1. Verify DNS is properly configured:
   ```bash
   nslookup YOUR_DOMAIN.com
   dig YOUR_DOMAIN.com
   ```
2. Ensure ports 80 and 443 are accessible:
   ```bash
   sudo netstat -tulpn | grep -E ':(80|443)'
   ```
3. Check Caddy logs:
   ```bash
   docker logs hygiei-caddy
   ```

### CORS Errors

**Problem**: "Access to fetch blocked by CORS policy"

**Solution**: Update backend CORS origins to include your HTTPS domain:

```python
allow_origins=["https://YOUR_DOMAIN.com"]
```

### Mixed Content Warnings

**Problem**: Browser blocks HTTP requests from HTTPS page

**Solution**: Ensure all API URLs use HTTPS in frontend environment variables.

### Certificate Renewal

Caddy automatically renews certificates before they expire. Check renewal status:

```bash
docker exec hygiei-caddy caddy list-certificates
```

## 🎯 Simplified Setup (Single Domain)

If you don't want a separate API subdomain, use this simpler Caddyfile:

```caddyfile
{
    email admin@yourdomain.com
}

hygiei.example.com {
    # Frontend for main routes
    reverse_proxy frontend:3000

    # Backend for /api routes
    handle /api/* {
        uri strip_prefix /api
        reverse_proxy backend:8000
    }

    encode gzip

    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        X-Frame-Options "SAMEORIGIN"
        X-Content-Type-Options "nosniff"
    }
}
```

Then set:

```bash
NEXT_PUBLIC_BACKEND_URL=https://hygiei.example.com/api
```

## 📊 Monitoring

### View Caddy Logs

```bash
# Real-time logs
docker logs -f hygiei-caddy

# Access logs (if configured)
docker exec hygiei-caddy cat /var/log/caddy/access.log
```

### Check Certificate Status

```bash
docker exec hygiei-caddy caddy list-certificates
```

### Test SSL Configuration

Use online tools:

- [SSL Labs](https://www.ssllabs.com/ssltest/)
- [Security Headers](https://securityheaders.com/)

## 🚀 Production Checklist

- [ ] Domain DNS configured and propagated
- [ ] Ports 80, 443 open on Datacrunch firewall
- [ ] Caddyfile updated with your domain
- [ ] Environment variables set with HTTPS URLs
- [ ] Backend CORS configured for HTTPS origin
- [ ] Deployment running: `docker compose -f docker-compose.caddy.yml up -d`
- [ ] HTTPS accessible in browser (padlock visible)
- [ ] API endpoints working via HTTPS
- [ ] Certificate auto-renewal enabled (default with Caddy)

## 🔄 Updating Deployment

When you need to update:

```bash
# Pull latest changes
git pull

# Rebuild and redeploy
docker compose -f docker-compose.caddy.yml up -d --build

# Caddy will automatically handle zero-downtime certificate renewal
```

## 💡 Advanced Options

### Rate Limiting

Add to Caddyfile:

```caddyfile
rate_limit {
    zone dynamic {
        key {remote_host}
        events 100
        window 1m
    }
}
```

### Custom Headers

```caddyfile
header {
    Content-Security-Policy "default-src 'self'"
    Permissions-Policy "geolocation=(), microphone=(), camera=()"
}
```

### Logging to File

Already configured in the provided Caddyfile at `/var/log/caddy/access.log`

---

**Need Help?** Check Caddy documentation: https://caddyserver.com/docs/
