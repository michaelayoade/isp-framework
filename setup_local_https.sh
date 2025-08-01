#!/bin/bash
# Quick setup script for local HTTPS testing
# Alternative to ngrok while setting up account

echo "🔧 Setting up local HTTPS for ISP Framework backend..."

# Create SSL directory
mkdir -p /tmp/ssl-certs
cd /tmp/ssl-certs

# Generate self-signed certificate
echo "📜 Generating self-signed SSL certificate..."
openssl req -x509 -newkey rsa:4096 -keyout server.key -out server.crt -days 365 -nodes \
  -subj "/C=US/ST=State/L=City/O=ISP Framework/OU=Development/CN=localhost"

# Set permissions
chmod 600 server.key
chmod 644 server.crt

echo "✅ SSL certificates generated:"
echo "   Certificate: /tmp/ssl-certs/server.crt"
echo "   Private Key: /tmp/ssl-certs/server.key"

# Create HTTPS startup script
cat > /tmp/start_https_backend.py << 'EOF'
#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '/home/ispframework/projects/isp-framework/backend')

import uvicorn
from app.main import app

print("🔒 Starting ISP Framework Backend with HTTPS")
print("📍 Server: https://localhost:8443")
print("📖 API Docs: https://localhost:8443/docs")
print("❤️  Health: https://localhost:8443/health")
print()
print("⚠️  Note: You'll need to accept the self-signed certificate in your browser")
print("   Click 'Advanced' -> 'Proceed to localhost (unsafe)' in Chrome")
print()

uvicorn.run(
    app,
    host="0.0.0.0",
    port=8443,
    ssl_keyfile="/tmp/ssl-certs/server.key",
    ssl_certfile="/tmp/ssl-certs/server.crt",
    reload=False
)
EOF

chmod +x /tmp/start_https_backend.py

echo ""
echo "🚀 Local HTTPS setup complete!"
echo ""
echo "To start HTTPS backend:"
echo "   python3 /tmp/start_https_backend.py"
echo ""
echo "Your API will be available at:"
echo "   https://localhost:8443"
echo "   https://localhost:8443/docs (API documentation)"
echo ""
echo "⚠️  Browser will show security warning - click 'Advanced' -> 'Proceed to localhost'"
echo ""
echo "For production use, set up ngrok with your authtoken:"
echo "1. Sign up: https://dashboard.ngrok.com/signup"
echo "2. Get authtoken: https://dashboard.ngrok.com/get-started/your-authtoken"
echo "3. Configure: ngrok config add-authtoken YOUR_TOKEN"
echo "4. Start tunnel: ngrok http 8000"
