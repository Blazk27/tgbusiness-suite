# TG Business Suite - Deployment Guide

This guide covers deploying TG Business Suite to a production Ubuntu VPS.

## Prerequisites

- Ubuntu 20.04+ VPS
- Docker & Docker Compose
- Domain name with DNS configured
- Stripe account (for billing)
- Telegram API credentials (from my.telegram.org)

## Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Nginx (for SSL)
sudo apt install -y nginx certbot python3-certbot-nginx
```

## Step 2: Clone and Configure

```bash
# Clone repository
git clone https://github.com/your-repo/tg-business-suite.git
cd tg-business-suite/docker

# Copy environment file
cp .env.example .env

# Edit environment variables
nano .env
```

## Step 3: Configure SSL (Production)

```bash
# Stop nginx temporarily
sudo systemctl stop nginx

# Get SSL certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Update nginx config for SSL
# (Edit docker/nginx/nginx.conf - see ssl.conf example)
```

## Step 4: Start Services

```bash
# Build and start all services
docker-compose up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
```

## Step 5: Database Migrations

```bash
# Run migrations
docker-compose exec backend alembic upgrade head
```

## Step 6: Verify Deployment

```bash
# Check all containers
docker-compose ps

# Test API health
curl http://localhost:8000/health

# Test frontend
curl http://localhost:3000
```

## Maintenance Commands

```bash
# Restart services
docker-compose restart

# Update code and rebuild
git pull
docker-compose up -d --build

# View logs
docker-compose logs -f

# Backup database
docker-compose exec db pg_dump -U tguser tgbusiness > backup.sql

# Scale workers (for high load)
docker-compose up -d --scale worker=3
```

## Security Checklist

- [ ] Change all default passwords
- [ ] Configure firewall (ufw)
- [ ] Enable SSL/TLS
- [ ] Set up regular backups
- [ ] Configure log rotation
- [ ] Enable rate limiting

## Troubleshooting

### Database Connection Issues
```bash
docker-compose logs db
docker-compose exec backend python -c "from app.core.database import async_engine; print('OK')"
```

### Redis Connection Issues
```bash
docker-compose exec redis redis-cli ping
```

### Build Errors
```bash
# Clear cache and rebuild
docker-compose build --no-cache
```
