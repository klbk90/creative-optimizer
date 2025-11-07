# 🚀 Deployment Guide - UTM Tracking System

**Complete guide for deploying to production.**

---

## 📚 Table of Contents

1. [Quick Deploy (5 minutes)](#quick-deploy-5-minutes)
2. [Manual Deployment](#manual-deployment)
3. [Multi-Domain Setup](#multi-domain-setup)
4. [SSL Configuration](#ssl-configuration)
5. [Monitoring & Maintenance](#monitoring--maintenance)
6. [Scaling](#scaling)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Quick Deploy (5 minutes)

**Prerequisites:**
- VPS with Ubuntu 20.04+ (Hetzner CPX11 - €4.51/month recommended)
- Domain pointed to server IP
- SSH access

### One-Command Deploy:

```bash
bash <(curl -s https://raw.githubusercontent.com/klbk88/utm-tracking/main/deploy/setup-vps.sh)
```

**What this does:**
1. ✅ Installs Docker & Docker Compose
2. ✅ Clones repository
3. ✅ Sets up environment variables
4. ✅ Starts all services
5. ✅ Configures Nginx reverse proxy
6. ✅ Sets up SSL with Let's Encrypt

**After setup:**
- API: `https://api.yourdomain.com`
- Docs: `https://api.yourdomain.com/docs`
- Admin Bot: Running in background

---

## 🛠️ Manual Deployment

For more control, follow these step-by-step instructions.

### Step 1: Get a VPS

**Recommended providers:**

| Provider | Plan | Price | Specs |
|----------|------|-------|-------|
| **Hetzner** (Best) | CPX11 | €4.51/month | 2 vCPU, 2GB RAM, 40GB SSD |
| DigitalOcean | Basic | $6/month | 1 vCPU, 1GB RAM, 25GB SSD |
| Vultr | Cloud Compute | $6/month | 1 vCPU, 1GB RAM, 25GB SSD |

**Setup:**

1. Create account on [Hetzner](https://www.hetzner.com/cloud)
2. Create new server:
   - Location: Closest to your users
   - Image: **Ubuntu 22.04**
   - Type: **CPX11**
   - SSH key: Add your public key
3. Note down the IP address

---

### Step 2: Initial Server Setup

SSH into your server:

```bash
ssh root@YOUR_SERVER_IP
```

#### Update system:

```bash
apt update && apt upgrade -y
```

#### Create deploy user:

```bash
adduser deploy
usermod -aG sudo deploy
su - deploy
```

#### Install Docker:

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify
docker --version
docker-compose --version
```

---

### Step 3: Clone Repository

```bash
cd /home/deploy
git clone https://github.com/klbk88/utm-tracking.git
cd utm-tracking
```

---

### Step 4: Configure Environment

```bash
cp .env.example .env
nano .env
```

**Production .env:**

```bash
# === DATABASE ===
DATABASE_URL=postgresql://utm_user:CHANGE_THIS_PASSWORD@postgres:5432/utm_tracking
POSTGRES_USER=utm_user
POSTGRES_PASSWORD=CHANGE_THIS_PASSWORD
POSTGRES_DB=utm_tracking

# === REDIS ===
REDIS_URL=redis://redis:6379/0

# === API ===
SECRET_KEY=GENERATE_LONG_RANDOM_STRING_HERE
LANDING_BASE_URL=https://api.yourdomain.com
TELEGRAM_BOT_USERNAME=your_bot

# === TELEGRAM ADMIN BOT ===
ADMIN_BOT_TOKEN=your_bot_token_from_@BotFather
ADMIN_USER_IDS=123456789,987654321

# === LANDING PAGE ===
LANDING_REDIRECT_TYPE=bot
LANDING_REDIRECT_DELAY=3

# === SECURITY ===
ALLOWED_ORIGINS=https://yourdomain.com,https://api.yourdomain.com
ENCRYPTION_KEY=GENERATE_32_BYTE_KEY_HERE

# === ANTHROPIC (for creative analysis) ===
ANTHROPIC_API_KEY=your_anthropic_key_here
```

**Generate SECRET_KEY:**

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Generate ENCRYPTION_KEY:**

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

### Step 5: Start Services

```bash
# Production mode
docker-compose -f deploy/docker-compose.prod.yml up -d

# Check logs
docker-compose -f deploy/docker-compose.prod.yml logs -f
```

**Services:**
- API: Port 8000
- PostgreSQL: Port 5432 (internal)
- Redis: Port 6379 (internal)
- Admin Bot: Background process

---

### Step 6: Setup Nginx

```bash
sudo apt install nginx -y
```

**Create Nginx config:**

```bash
sudo nano /etc/nginx/sites-available/utm-tracking
```

**Paste this config:**

```nginx
# API Server
server {
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Landing Pages (if using same server)
server {
    server_name yourdomain.com www.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /home/deploy/utm-tracking/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

**Enable site:**

```bash
sudo ln -s /etc/nginx/sites-available/utm-tracking /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

### Step 7: Setup SSL (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx -y

# Get certificates
sudo certbot --nginx -d api.yourdomain.com -d yourdomain.com -d www.yourdomain.com

# Auto-renewal (already setup by certbot)
sudo certbot renew --dry-run
```

**Done!** 🎉

Visit:
- https://api.yourdomain.com/docs
- https://api.yourdomain.com/health

---

## 🌐 Multi-Domain Setup

Deploy multiple landing pages on different domains.

### Scenario:

```
lootbox1.com → Landing Template #1
lootbox2.com → Landing Template #2
betting1.com → Landing Template #3
```

### Setup:

#### 1. Point DNS

For each domain, create **A record**:

```
Type: A
Name: @
Value: YOUR_SERVER_IP
TTL: 3600
```

#### 2. Create Landing via API

```bash
curl -X POST https://api.yourdomain.com/api/v1/landings/create \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{
    "name": "Lootbox Campaign 1",
    "template": "lootbox",
    "utm_campaign": "lootbox1_jan_2025",
    "config": {
      "headline": "🎁 Win $500!",
      "bg_color": "#667eea"
    },
    "custom_domain": "lootbox1.com"
  }'
```

#### 3. Deploy Domain

```bash
bash deploy/deploy-domain.sh lootbox1.com LANDING_ID
```

**What this does:**
1. Creates Nginx server block for lootbox1.com
2. Reloads Nginx
3. Gets SSL certificate via certbot

#### 4. Repeat for other domains

```bash
bash deploy/deploy-domain.sh lootbox2.com LANDING_ID_2
bash deploy/deploy-domain.sh betting1.com LANDING_ID_3
```

---

## 🔒 SSL Configuration

### Automatic Renewal

Certbot auto-renews certificates. Verify:

```bash
sudo systemctl status certbot.timer
```

### Manual Renewal

```bash
sudo certbot renew
sudo nginx -t && sudo systemctl reload nginx
```

### Wildcard SSL (Advanced)

For `*.yourdomain.com`:

```bash
sudo certbot certonly --manual --preferred-challenges dns -d "*.yourdomain.com" -d yourdomain.com
```

Follow instructions to add DNS TXT record.

---

## 📊 Monitoring & Maintenance

### Check Service Status

```bash
# Docker containers
docker ps

# Logs
docker-compose -f deploy/docker-compose.prod.yml logs -f api
docker-compose -f deploy/docker-compose.prod.yml logs -f postgres
docker-compose -f deploy/docker-compose.prod.yml logs -f admin-bot

# Nginx
sudo nginx -t
sudo systemctl status nginx
```

### Database Backup

```bash
# Backup
docker exec utm-tracking-postgres pg_dump -U utm_user utm_tracking > backup_$(date +%Y%m%d).sql

# Restore
cat backup_20250107.sql | docker exec -i utm-tracking-postgres psql -U utm_user utm_tracking
```

### Disk Space

```bash
# Check disk usage
df -h

# Clean Docker
docker system prune -a
```

### Update System

```bash
cd /home/deploy/utm-tracking
git pull origin main
docker-compose -f deploy/docker-compose.prod.yml down
docker-compose -f deploy/docker-compose.prod.yml up -d --build
```

---

## 📈 Scaling

### Vertical Scaling (Single Server)

Upgrade VPS plan:

| Traffic | Plan | Specs | Cost |
|---------|------|-------|------|
| <10k/day | CPX11 | 2 vCPU, 2GB RAM | €4.51/month |
| 10-50k/day | CPX21 | 3 vCPU, 4GB RAM | €8.21/month |
| 50-200k/day | CPX31 | 4 vCPU, 8GB RAM | €15.41/month |
| 200k+/day | CPX51 | 16 vCPU, 32GB RAM | €56.41/month |

### Horizontal Scaling (Multiple Servers)

#### Load Balancer Setup:

```
Users → Cloudflare → Load Balancer → [Server 1, Server 2, Server 3]
                                        ↓
                                   PostgreSQL (Primary)
                                   Redis (Shared)
```

**Tools:**
- Cloudflare Load Balancing (free tier available)
- Nginx as load balancer
- HAProxy

---

## 🐛 Troubleshooting

### API Not Starting

```bash
# Check logs
docker-compose -f deploy/docker-compose.prod.yml logs api

# Common issues:
# 1. Port 8000 already in use
sudo lsof -i :8000
sudo kill -9 PID

# 2. Database not ready
docker-compose -f deploy/docker-compose.prod.yml restart postgres
docker-compose -f deploy/docker-compose.prod.yml restart api
```

### Nginx 502 Bad Gateway

```bash
# Check if API is running
curl http://localhost:8000/health

# Check Nginx config
sudo nginx -t

# Check logs
sudo tail -f /var/log/nginx/error.log
```

### SSL Certificate Issues

```bash
# Check expiry
sudo certbot certificates

# Force renewal
sudo certbot renew --force-renewal
sudo systemctl reload nginx
```

### Database Connection Errors

```bash
# Check PostgreSQL
docker exec -it utm-tracking-postgres psql -U utm_user -d utm_tracking

# Reset password
docker exec -it utm-tracking-postgres psql -U utm_user -c "ALTER USER utm_user WITH PASSWORD 'new_password';"

# Update .env with new password
```

---

## 🔧 Advanced Configuration

### Custom Domain for Each Landing

Edit `deploy/nginx-template.conf` to auto-generate configs.

### CDN Integration

Use Cloudflare:
1. Add domain to Cloudflare
2. Enable proxy (orange cloud)
3. Configure caching rules
4. Enable Brotli compression

### Database Read Replicas

For high traffic:

```yaml
# docker-compose.prod.yml
postgres-replica:
  image: postgres:15-alpine
  environment:
    POSTGRES_REPLICATION_MODE: slave
    POSTGRES_MASTER_SERVICE: postgres
```

---

## 📝 Checklist

### Pre-Launch

- [ ] Environment variables configured
- [ ] Database backed up
- [ ] SSL certificates active
- [ ] Monitoring setup (optional: UptimeRobot)
- [ ] Admin bot tested
- [ ] API health check passes
- [ ] Landing pages render correctly

### Post-Launch

- [ ] Monitor error logs
- [ ] Check database performance
- [ ] Verify SSL auto-renewal
- [ ] Setup daily backups (cron job)
- [ ] Document any custom configuration

---

## 🎓 Next Steps

- **Monitoring:** Setup [UptimeRobot](https://uptimerobot.com) (free)
- **Analytics:** Integrate with existing analytics dashboard
- **Backups:** Automate daily backups to S3
- **Scaling:** Add more servers when traffic grows
- **Security:** Enable fail2ban, firewall rules

---

**Need help?** Check troubleshooting section or open an issue on GitHub.

**Deployment time:** 5 min (automated) or 20 min (manual) ⏱️

