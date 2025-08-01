#!/usr/bin/env python3
"""
HTTPS Server Runner for ISP Framework Backend
Production-ready SSL/HTTPS server startup script
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.main import app
from app.core.config import settings
from ssl_config import SSLConfig

def main():
    """Main entry point for HTTPS server"""
    
    # Check if SSL is enabled
    if not settings.enable_https:
        print("❌ HTTPS is not enabled in configuration")
        print("💡 Set ENABLE_HTTPS=true in your environment variables")
        print("🔧 Or use: docker-compose up -d for HTTP development server")
        return
    
    # Initialize SSL configuration
    ssl_config = SSLConfig(
        cert_path=settings.ssl_cert_path,
        key_path=settings.ssl_key_path
    )
    
    # Validate certificates
    if not ssl_config.validate_certificates():
        print("\n📋 SSL Certificate Setup Options:")
        print("1. Generate self-signed certificates:")
        print("   openssl req -x509 -newkey rsa:4096 -keyout server.key -out server.crt -days 365 -nodes")
        print("\n2. Use Let's Encrypt:")
        print("   certbot certonly --standalone -d yourdomain.com")
        print("\n3. Use reverse proxy (Nginx/Apache) with SSL termination")
        print("\n4. Use ngrok for development:")
        print("   ngrok http 8000")
        return
    
    try:
        # Get SSL configuration for uvicorn
        ssl_params = ssl_config.get_uvicorn_ssl_config()
        
        print(f"🔒 Starting ISP Framework Backend with HTTPS")
        print(f"📍 Server: https://0.0.0.0:8443")
        print(f"📖 API Docs: https://0.0.0.0:8443/docs")
        print(f"🔧 ReDoc: https://0.0.0.0:8443/redoc")
        print(f"❤️  Health: https://0.0.0.0:8443/health")
        
        # Start HTTPS server
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8443,
            reload=False,  # Disable reload in production
            access_log=True,
            log_level=settings.log_level.lower(),
            **ssl_params
        )
        
    except Exception as e:
        print(f"❌ Failed to start HTTPS server: {e}")
        print("\n🔧 Troubleshooting:")
        print("- Check certificate file permissions")
        print("- Verify certificate and key file paths")
        print("- Ensure port 8443 is available")
        print("- Check firewall settings")
        sys.exit(1)

if __name__ == "__main__":
    main()
