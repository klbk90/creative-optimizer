#!/bin/bash

##############################################################################
# UTM Tracking System - Automated VPS Setup
#
# This script automatically sets up a production-ready environment:
# - Installs Docker & Docker Compose
# - Clones repository
# - Configures environment
# - Starts all services
# - Sets up Nginx + SSL
#
# Usage: bash <(curl -s https://raw.githubusercontent.com/klbk88/utm-tracking/main/deploy/setup-vps.sh)
##############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}"
echo "================================"
echo "  UTM Tracking System Setup"
echo "================================"
echo -e "${NC}"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root${NC}"
   exit 1
fi

# Get user input
read -p "Enter your domain (e.g., api.yourdomain.com): " DOMAIN
read -p "Enter your email for SSL certificates: " EMAIL
read -p "Enter Telegram Bot Token: " BOT_TOKEN
read -p "Enter your Telegram User ID: " ADMIN_ID

echo -e "\n${YELLOW}Starting setup...${NC}\n"

# ==================== Step 1: Update System ====================
echo -e "${GREEN}[1/8] Updating system...${NC}"
apt update && apt upgrade -y

# ==================== Step 2: Install Docker ====================
echo -e "${GREEN}[2/8] Installing Docker...${NC}"

if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    echo -e "${GREEN}✓ Docker installed${NC}"
else
    echo -e "${YELLOW}✓ Docker already installed${NC}"
fi

# ==================== Step 3: Install Docker Compose ====================
echo -e "${GREEN}[3/8] Installing Docker Compose...${NC}"

if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}✓ Docker Compose installed${NC}"
else
    echo -e "${YELLOW}✓ Docker Compose already installed${NC}"
fi

# ==================== Step 4: Create Deploy User ====================
echo -e "${GREEN}[4/8] Setting up deploy user...${NC}"

if ! id "deploy" &>/dev/null; then
    useradd -m -s /bin/bash deploy
    usermod -aG sudo,docker deploy
    echo -e "${GREEN}✓ Deploy user created${NC}"
else
    echo -e "${YELLOW}✓ Deploy user already exists${NC}"
fi

# ==================== Step 5: Clone Repository ====================
echo -e "${GREEN}[5/8] Cloning repository...${NC}"

cd /home/deploy

if [ ! -d "utm-tracking" ]; then
    sudo -u deploy git clone https://github.com/klbk88/utm-tracking.git
    echo -e "${GREEN}✓ Repository cloned${NC}"
else
    echo -e "${YELLOW}✓ Repository already exists${NC}"
    cd utm-tracking
    sudo -u deploy git pull origin main
fi

cd utm-tracking

# ==================== Step 6: Configure Environment ====================
echo -e "${GREEN}[6/8] Configuring environment...${NC}"

# Generate secrets
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
DB_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))")
ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Create .env
cat > .env <<EOF
# === DATABASE ===
DATABASE_URL=postgresql://utm_user:${DB_PASSWORD}@postgres:5432/utm_tracking
POSTGRES_USER=utm_user
POSTGRES_PASSWORD=${DB_PASSWORD}
POSTGRES_DB=utm_tracking

# === REDIS ===
REDIS_URL=redis://redis:6379/0

# === API ===
SECRET_KEY=${SECRET_KEY}
LANDING_BASE_URL=https://${DOMAIN}
TELEGRAM_BOT_USERNAME=your_bot

# === TELEGRAM ADMIN BOT ===
ADMIN_BOT_TOKEN=${BOT_TOKEN}
ADMIN_USER_IDS=${ADMIN_ID}

# === LANDING PAGE ===
LANDING_REDIRECT_TYPE=bot
LANDING_REDIRECT_DELAY=3

# === SECURITY ===
ALLOWED_ORIGINS=https://${DOMAIN}
ENCRYPTION_KEY=${ENCRYPTION_KEY}

# === OPTIONAL: ANTHROPIC ===
# ANTHROPIC_API_KEY=your_key_here
EOF

chown deploy:deploy .env
echo -e "${GREEN}✓ Environment configured${NC}"

# ==================== Step 7: Start Services ====================
echo -e "${GREEN}[7/8] Starting services...${NC}"

sudo -u deploy docker-compose -f deploy/docker-compose.prod.yml up -d

echo -e "${YELLOW}Waiting for services to start...${NC}"
sleep 10

echo -e "${GREEN}✓ Services started${NC}"

# ==================== Step 8: Setup Nginx + SSL ====================
echo -e "${GREEN}[8/8] Setting up Nginx and SSL...${NC}"

# Install Nginx and Certbot
apt install -y nginx certbot python3-certbot-nginx

# Create Nginx config
cat > /etc/nginx/sites-available/utm-tracking <<EOF
server {
    server_name ${DOMAIN};

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias /home/deploy/utm-tracking/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/utm-tracking /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test and reload Nginx
nginx -t
systemctl restart nginx

# Get SSL certificate
certbot --nginx -d ${DOMAIN} --email ${EMAIL} --agree-tos --non-interactive --redirect

echo -e "${GREEN}✓ Nginx and SSL configured${NC}"

# ==================== Final Steps ====================
echo -e "\n${GREEN}================================${NC}"
echo -e "${GREEN}   Setup Complete! 🎉${NC}"
echo -e "${GREEN}================================${NC}\n"

echo -e "Your UTM Tracking System is now running at:"
echo -e "${YELLOW}  API:  https://${DOMAIN}${NC}"
echo -e "${YELLOW}  Docs: https://${DOMAIN}/docs${NC}\n"

echo -e "Next steps:"
echo -e "  1. Visit https://${DOMAIN}/health to verify"
echo -e "  2. Check logs: ${YELLOW}docker-compose -f deploy/docker-compose.prod.yml logs -f${NC}"
echo -e "  3. Start Telegram Admin Bot: ${YELLOW}docker-compose -f deploy/docker-compose.prod.yml restart admin-bot${NC}\n"

echo -e "${GREEN}Credentials saved to: /home/deploy/utm-tracking/.env${NC}\n"
