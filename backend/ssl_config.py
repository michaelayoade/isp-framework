#!/usr/bin/env python3
"""
SSL Configuration for ISP Framework Backend
Provides SSL/HTTPS setup options for production deployment
"""

import ssl
import uvicorn
from pathlib import Path
from typing import Optional

class SSLConfig:
    """SSL Configuration manager for the ISP Framework backend"""
    
    def __init__(self, cert_path: Optional[str] = None, key_path: Optional[str] = None):
        self.cert_path = cert_path or "/etc/ssl/certs/ispframework.crt"
        self.key_path = key_path or "/etc/ssl/private/ispframework.key"
        
    def create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context for HTTPS server"""
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(self.cert_path, self.key_path)
        
        # Security hardening
        context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
        context.options |= ssl.OP_NO_SSLv2
        context.options |= ssl.OP_NO_SSLv3
        context.options |= ssl.OP_NO_TLSv1
        context.options |= ssl.OP_NO_TLSv1_1
        
        return context
    
    def validate_certificates(self) -> bool:
        """Validate that SSL certificates exist and are readable"""
        cert_file = Path(self.cert_path)
        key_file = Path(self.key_path)
        
        if not cert_file.exists():
            print(f"❌ SSL certificate not found: {self.cert_path}")
            return False
            
        if not key_file.exists():
            print(f"❌ SSL private key not found: {self.key_path}")
            return False
            
        print(f"✅ SSL certificates found: {self.cert_path}, {self.key_path}")
        return True
    
    def get_uvicorn_ssl_config(self) -> dict:
        """Get SSL configuration for uvicorn server"""
        if not self.validate_certificates():
            raise FileNotFoundError("SSL certificates not found")
            
        return {
            "ssl_keyfile": self.key_path,
            "ssl_certfile": self.cert_path,
            "ssl_version": ssl.PROTOCOL_TLS_SERVER,
            "ssl_cert_reqs": ssl.CERT_NONE,
            "ssl_ca_certs": None,
        }

def run_with_ssl(app, host="0.0.0.0", port=8443, cert_path=None, key_path=None):
    """Run the FastAPI app with SSL/HTTPS"""
    ssl_config = SSLConfig(cert_path, key_path)
    
    try:
        ssl_params = ssl_config.get_uvicorn_ssl_config()
        print(f"🔒 Starting HTTPS server on https://{host}:{port}")
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            **ssl_params,
            access_log=True,
            reload=False  # Disable reload in production with SSL
        )
    except Exception as e:
        print(f"❌ Failed to start HTTPS server: {e}")
        print("💡 Consider using HTTP with reverse proxy or ngrok for development")
        raise

if __name__ == "__main__":
    # Example usage
    from app.main import app
    
    # Option 1: Use custom certificate paths
    run_with_ssl(
        app, 
        host="0.0.0.0", 
        port=8443,
        cert_path="/path/to/your/cert.pem",
        key_path="/path/to/your/key.pem"
    )
