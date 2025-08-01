#!/bin/bash
# Start ISP Framework backend with HTTPS in Docker
# Uses the SSL certificates we generated

echo "🔒 Starting ISP Framework Backend with HTTPS in Docker..."

# Copy SSL certificates to backend directory for Docker access
mkdir -p ./backend/ssl
cp /tmp/ssl-certs/server.crt ./backend/ssl/
cp /tmp/ssl-certs/server.key ./backend/ssl/

# Update Docker Compose to include HTTPS
cat > docker-compose.https.yml << 'EOF'
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:14-alpine
    container_name: isp-postgres
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "${POSTGRES_PORT}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - isp-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis for caching and background jobs
  redis:
    image: redis:7-alpine
    container_name: isp-redis
    ports:
      - "${REDIS_PORT}:6379"
    volumes:
      - redis_data:/data
    networks:
      - isp-network
    restart: unless-stopped
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # MinIO S3-compatible storage
  minio:
    image: minio/minio:latest
    container_name: isp-minio
    ports:
      - "${MINIO_PORT}:9000"
      - "${MINIO_CONSOLE_PORT}:9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
      MINIO_BROWSER: "on"
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"
    networks:
      - isp-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

  # ISP Framework Backend with HTTPS
  backend:
    build: ./backend
    container_name: isp-backend
    ports:
      - "${BACKEND_PORT}:8000"      # HTTP
      - "8443:8443"                 # HTTPS
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      REDIS_URL: ${REDIS_URL}
      MINIO_ENDPOINT: ${MINIO_ENDPOINT}
      MINIO_ACCESS_KEY: ${MINIO_ACCESS_KEY}
      MINIO_SECRET_KEY: ${MINIO_SECRET_KEY}
      MINIO_BUCKET_CUSTOMER_UPLOADS: ${MINIO_BUCKET_CUSTOMER_UPLOADS}
      MINIO_BUCKET_TICKET_MEDIA: ${MINIO_BUCKET_TICKET_MEDIA}
      MINIO_BUCKET_CSV_IMPORTS: ${MINIO_BUCKET_CSV_IMPORTS}
      MINIO_BUCKET_BACKUPS: ${MINIO_BUCKET_BACKUPS}
      MINIO_BUCKET_TEMP: ${MINIO_BUCKET_TEMP}
      MINIO_USE_SSL: ${MINIO_USE_SSL}
      SECRET_KEY: ${SECRET_KEY}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      JWT_ALGORITHM: ${JWT_ALGORITHM}
      ACCESS_TOKEN_EXPIRE_MINUTES: ${ACCESS_TOKEN_EXPIRE_MINUTES}
      REFRESH_TOKEN_EXPIRE_MINUTES: ${REFRESH_TOKEN_EXPIRE_MINUTES}
      SECRETS_BACKEND: ${SECRETS_BACKEND}
      LOG_LEVEL: ${LOG_LEVEL}
      ALLOWED_HOSTS: '["*"]'
      # SSL Configuration
      ENABLE_HTTPS: "true"
      SSL_CERT_PATH: "/app/ssl/server.crt"
      SSL_KEY_PATH: "/app/ssl/server.key"
    volumes:
      - ./backend/app:/app/app
      - ./backend/logs:/app/logs
      - ./backend/ssl:/app/ssl:ro  # Mount SSL certificates
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      minio:
        condition: service_healthy
    networks:
      - isp-network
    restart: unless-stopped
    command: python run_https.py
    healthcheck:
      test: ["CMD", "curl", "-k", "-f", "https://localhost:8443/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  minio_data:
    driver: local

networks:
  isp-network:
    driver: bridge
EOF

echo "✅ Docker Compose HTTPS configuration created"
echo ""
echo "🚀 Starting backend with HTTPS support..."
docker-compose -f docker-compose.https.yml up -d backend postgres redis minio

echo ""
echo "🔒 ISP Framework Backend with HTTPS is starting..."
echo "📍 HTTP:  http://localhost:8000"
echo "📍 HTTPS: https://localhost:8443"
echo "📖 API Docs: https://localhost:8443/docs"
echo "❤️  Health: https://localhost:8443/health"
echo ""
echo "⚠️  Note: Browser will show security warning for self-signed certificate"
echo "   Click 'Advanced' -> 'Proceed to localhost (unsafe)'"
echo ""
echo "🔧 For frontend integration, use:"
echo "   const API_BASE_URL = 'https://localhost:8443';"
