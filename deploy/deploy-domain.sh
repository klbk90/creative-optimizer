#!/bin/bash

##############################################################################
# Deploy New Domain for Landing Page
#
# Usage: bash deploy/deploy-domain.sh <domain> <landing_id>
# Example: bash deploy/deploy-domain.sh lootbox1.com abc-123-def-456
##############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check arguments
if [ $# -ne 2 ]; then
    echo -e "${RED}Usage: $0 <domain> <landing_id>${NC}"
    echo -e "Example: $0 lootbox1.com abc-123-def-456"
    exit 1
fi

DOMAIN=$1
LANDING_ID=$2

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}  Deploying Domain: $DOMAIN${NC}"
echo -e "${GREEN}  Landing ID: $LANDING_ID${NC}"
echo -e "${GREEN}================================${NC}\n"

# Check if running as root or sudo
if [[ $EUID -ne 0 ]]; then
   echo -e "${YELLOW}This script requires sudo privileges. Running with sudo...${NC}"
   exec sudo "$0" "$@"
fi

# ==================== Step 1: Check DNS ====================
echo -e "${GREEN}[1/4] Checking DNS configuration...${NC}"

CURRENT_IP=$(curl -s ifconfig.me)
DOMAIN_IP=$(dig +short $DOMAIN | tail -n1)

if [ -z "$DOMAIN_IP" ]; then
    echo -e "${RED}✗ No DNS record found for $DOMAIN${NC}"
    echo -e "${YELLOW}Please add an A record pointing to: $CURRENT_IP${NC}"
    read -p "Press Enter when DNS is configured..."
fi

echo -e "${GREEN}✓ DNS check passed${NC}"

# ==================== Step 2: Create Nginx Config ====================
echo -e "${GREEN}[2/4] Creating Nginx configuration...${NC}"

NGINX_CONF="/etc/nginx/sites-available/$DOMAIN"

cat > $NGINX_CONF <<EOF
# Landing Page: $DOMAIN
# Landing ID: $LANDING_ID

server {
    server_name $DOMAIN www.$DOMAIN;

    # Serve landing page
    location / {
        proxy_pass http://localhost:8000/landings/$LANDING_ID;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Static files
    location /static {
        alias /home/deploy/utm-tracking/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Health check
    location /health {
        proxy_pass http://localhost:8000/health;
    }
}
EOF

echo -e "${GREEN}✓ Nginx config created${NC}"

# ==================== Step 3: Enable Site ====================
echo -e "${GREEN}[3/4] Enabling site...${NC}"

# Create symlink
ln -sf $NGINX_CONF /etc/nginx/sites-enabled/$DOMAIN

# Test Nginx config
nginx -t

# Reload Nginx
systemctl reload nginx

echo -e "${GREEN}✓ Site enabled${NC}"

# ==================== Step 4: Get SSL Certificate ====================
echo -e "${GREEN}[4/4] Getting SSL certificate...${NC}"

# Check if certbot is installed
if ! command -v certbot &> /dev/null; then
    echo -e "${YELLOW}Installing certbot...${NC}"
    apt update
    apt install -y certbot python3-certbot-nginx
fi

# Get SSL certificate
certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --redirect --email admin@$DOMAIN || {
    echo -e "${YELLOW}Failed to get SSL for www.$DOMAIN, trying without www...${NC}"
    certbot --nginx -d $DOMAIN --non-interactive --agree-tos --redirect --email admin@$DOMAIN
}

echo -e "${GREEN}✓ SSL certificate obtained${NC}"

# ==================== Success ====================
echo -e "\n${GREEN}================================${NC}"
echo -e "${GREEN}   Deployment Complete! 🎉${NC}"
echo -e "${GREEN}================================${NC}\n"

echo -e "Your landing page is now live at:"
echo -e "${YELLOW}  https://$DOMAIN${NC}\n"

echo -e "To update the landing page:"
echo -e "  ${YELLOW}PUT /api/v1/landings/$LANDING_ID${NC} with new config\n"

echo -e "To remove this domain:"
echo -e "  ${YELLOW}sudo rm /etc/nginx/sites-enabled/$DOMAIN${NC}"
echo -e "  ${YELLOW}sudo systemctl reload nginx${NC}"
echo -e "  ${YELLOW}sudo certbot delete --cert-name $DOMAIN${NC}\n"
