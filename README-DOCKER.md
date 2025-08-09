# Docker Deployment Guide

## Prerequisites

You need a database backup from your development environment. The database contains 8,861 CrossFit workouts with embeddings and metadata (~305 MB).

### Create Database Backup (on your local machine)

```bash
# Create compressed backup (~50-100MB)
docker exec wodrag_paradedb pg_dump -U postgres wodrag | gzip > wodrag_backup.sql.gz

# Verify backup was created
ls -lh wodrag_backup.sql.gz
```

## Quick Start

### 1. Clone and Configure

```bash
# Clone the repository
git clone https://github.com/yourusername/wodrag.git
cd wodrag

# Copy environment template
cp env.example .env

# Edit .env and add your API keys
nano .env
```

### 2. Transfer Database Backup

```bash
# From your local machine, copy backup to VPS
scp wodrag_backup.sql.gz root@your-vps-ip:/tmp/
```

### 3. Build and Initialize Database

```bash
# Start only the database container first
docker compose -f docker-compose.prod.yml up -d postgres

# Wait for database to be ready
sleep 5

# Restore the database backup
gunzip < /tmp/wodrag_backup.sql.gz | docker exec -i wodrag_paradedb psql -U postgres wodrag

# Verify data was loaded
docker exec wodrag_paradedb psql -U postgres -d wodrag -c "SELECT COUNT(*) FROM workouts;"
# Should show 8861 workouts
```

### 4. Start All Services

```bash
# Now start the backend and frontend
docker compose -f docker-compose.prod.yml up --build -d

# Check that everything is running
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f
```

### 5. Access the Application

Open your browser to: **http://localhost** (or your VPS IP)

## Caddy Frontend (Production)

The production stack serves the frontend with Caddy and proxies API requests to the backend.

- Domain: configure DNS for `wodrag.com` and `www.wodrag.com` to point to your host.
- TLS: Caddy automatically provisions certificates via Let's Encrypt on ports 80/443.
- Build: `Dockerfile.caddy` builds the React app and serves it using the repo `Caddyfile`.

Start services:

```bash
docker compose -f docker-compose.prod.yml up -d postgres
docker compose -f docker-compose.prod.yml up -d backend
docker compose -f docker-compose.prod.yml up -d frontend
```

Backend rate limits to review:

- `GLOBAL_RATE_LIMIT_REQUESTS_PER_DAY` (global request budget)
- `RATE_LIMIT_REQUESTS_PER_HOUR` (per-client requests/hour)
- `PER_REQUEST_LM_CALL_BUDGET` (LLM calls per request, default 6)

Per-client identification uses `X-Forwarded-For`/`X-Real-IP` set by Caddy.

## Services

The stack includes:

- **Frontend (port 80)**: React app served by nginx
- **Backend (internal)**: FastAPI server
- **Database (internal)**: ParadeDB (PostgreSQL + BM25 + pgvector)

## Production Deployment on VPS

### 1. Prerequisites

- VPS with Docker and Docker Compose installed
- Domain name (optional but recommended)
- SSL certificate (use Let's Encrypt)

### 2. Deploy to VPS

```bash
# SSH to your VPS
ssh root@your-vps-ip

# Clone the repository
git clone https://github.com/yourusername/wodrag.git
cd wodrag

# Configure environment
cp env.example .env
nano .env  # Add your OPENAI_API_KEY

# Build and run
docker compose -f docker-compose.prod.yml up --build -d
```

### 3. SSL Setup (Optional)

For HTTPS, use a reverse proxy like Caddy or nginx with Let's Encrypt:

```bash
# Install Caddy
apt install caddy

# Configure Caddy (/etc/caddy/Caddyfile)
your-domain.com {
    reverse_proxy localhost:80
}

# Restart Caddy
systemctl restart caddy
```

## Management Commands

```bash
# Stop all services
docker compose -f docker-compose.prod.yml down

# View logs
docker compose -f docker-compose.prod.yml logs -f [service-name]

# Rebuild a specific service
docker compose -f docker-compose.prod.yml build backend
docker compose -f docker-compose.prod.yml up -d backend

# Execute commands in containers
docker compose -f docker-compose.prod.yml exec backend bash
docker compose -f docker-compose.prod.yml exec postgres psql -U postgres -d wodrag

# Backup database
docker compose -f docker-compose.prod.yml exec postgres pg_dump -U postgres wodrag > backup.sql

# Clean up everything (including volumes)
docker compose -f docker-compose.prod.yml down -v
```

## Updating

```bash
# Pull latest code
git pull

# Rebuild and restart
docker compose -f docker-compose.prod.yml up --build -d
```

## Troubleshooting

### Services won't start
```bash
# Check logs
docker compose -f docker-compose.prod.yml logs

# Ensure ports are free
lsof -i :80
lsof -i :5432
```

### Database connection issues
```bash
# Check database is healthy
docker compose -f docker-compose.prod.yml exec postgres pg_isready

# Check if data is loaded
docker exec wodrag_paradedb psql -U postgres -d wodrag -c "SELECT COUNT(*) FROM workouts;"
```

### Database is empty
```bash
# If you forgot to restore the backup, do it now
gunzip < /tmp/wodrag_backup.sql.gz | docker exec -i wodrag_paradedb psql -U postgres wodrag

# Then restart the backend
docker compose -f docker-compose.prod.yml restart backend
```

### Frontend not updating
```bash
# Force rebuild without cache
docker compose -f docker-compose.prod.yml build --no-cache frontend
docker compose -f docker-compose.prod.yml up -d frontend
```

## Performance Tuning

For production, consider:

1. **Set resource limits** in docker-compose.prod.yml:
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

2. **Enable swap** on your VPS:
```bash
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
```

3. **Monitor with docker stats**:
```bash
docker stats
```
