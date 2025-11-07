# 🚀 UTM Tracking Implementation Guide

## 📋 Overview

This guide covers the complete implementation of the UTM tracking system with **two link types**:

1. **Landing Links** - For TikTok/Instagram bio (промежуточная страница)
2. **Direct Links** - For Telegram reposts (прямые ссылки)

---

## 🎯 Two Link Types Explained

### 🌐 Landing Link (для TikTok bio)

**Use case:** TikTok bio, Instagram bio, external traffic

**Flow:**
```
TikTok → yourdomain.com/l/tiktok_abc123 → Landing Page → Telegram → Bot
```

**Advantages:**
- ✅ Beautiful branded page
- ✅ Track device/geo/time on page
- ✅ Add additional info/CTA
- ✅ Doesn't violate TikTok ToS

**Example:**
```bash
# Generate landing link via Admin Bot
/generate
→ football_jan_2025
→ Landing Page (для TikTok bio)
→ TikTok
→ video_123

# Result:
https://yourdomain.com/l/tiktok_abc123
```

### 📱 Direct Link (для Telegram репостов)

**Use case:** Telegram channel posts, tg-reposter, internal links

**Flow:**
```
Telegram post → t.me/your_bot?start=tg_xyz789 → Bot
```

**Advantages:**
- ✅ Faster (no intermediate page)
- ✅ Native Telegram experience
- ✅ Higher conversion rate
- ✅ No external redirect

**Example:**
```bash
# Generate direct link via Admin Bot
/generate
→ repost_jan_2025
→ Direct Link (для репостов)
→ Telegram
→ repost_channel_1

# Result:
t.me/your_bot?start=tg_xyz789
```

---

## 🛠️ Setup Instructions

### 1. Install Dependencies

```bash
cd utm-tracking
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

**Required variables:**

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/utm_tracking

# Admin Bot
ADMIN_BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789,987654321

# Tracking API
LANDING_BASE_URL=https://yourdomain.com/api/v1/landing/l
DEFAULT_TELEGRAM_CHANNEL=https://t.me/your_channel

# Security
JWT_SECRET_KEY=your-secret-key
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Optional: GeoIP
GEOIP_DB_PATH=/path/to/GeoLite2-City.mmdb

# Optional: Encryption
ENCRYPTION_KEY=generate_with_fernet
```

### 3. Setup Database

```bash
# Create database
createdb utm_tracking

# Run migrations
alembic upgrade head

# Or create tables directly
python -c "from database.base import Base, engine; from database.models import *; Base.metadata.create_all(bind=engine)"
```

### 4. Start Services

#### Option A: Docker Compose (Recommended)

```bash
docker-compose up -d
```

Services will start:
- PostgreSQL on :5432
- Redis on :6379
- Tracking API on :8000
- Admin Bot (background)

#### Option B: Manual

```bash
# Terminal 1: API
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Admin Bot
python bots/admin_bot.py
```

---

## 📊 Using the Admin Bot

### Generate UTM Links

```
/generate

→ Enter campaign name: football_jan_2025

→ Choose link type:
  🌐 Landing Page (для TikTok bio)
  📱 Direct Link (для репостов)

→ Choose source:
  📱 TikTok
  💬 Telegram
  📷 Instagram

→ Enter content ID: video_123 (or - to skip)

✅ UTM link created!
🔗 Link: https://yourdomain.com/l/tiktok_abc123
```

### View Statistics

```
/stats

→ Choose period:
  • Today
  • 7 days
  • 30 days

📊 Statistics for 7 days:
👆 Clicks: 1,234
💰 Conversions: 156 (CR: 12.6%)
💵 Revenue: $7,800
📈 AOV: $50.00

🏆 Top sources:
1. TIKTOK - 98 conv, $4,900
2. TELEGRAM - 58 conv, $2,900
```

### View Campaigns

```
/campaigns

📁 Active campaigns:

1. football_jan_2025
   👆 856 | 💰 102 (11.9%) | 💵 $5,100

2. basketball_dec_2024
   👆 378 | 💰 54 (14.3%) | 💵 $2,700
```

---

## 🔗 Integrating with User Bot

### Step 1: Handle /start with UTM

```python
from telegram_bot_integration import track_click, user_utm_mapping

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id

    # Extract UTM ID from /start parameter
    args = message.text.split(maxsplit=1)
    utm_id = args[1] if len(args) > 1 else None

    if utm_id and utm_id.startswith(("tiktok_", "tg_", "ig_")):
        # Save UTM for this user
        user_utm_mapping[user_id] = utm_id

        # Track click
        track_click(utm_id, user_id, referrer="telegram_bot_start")

        bot.send_message(
            message.chat.id,
            "👋 Welcome! Opening lootbox menu..."
        )
```

### Step 2: Track Conversion on Purchase

```python
from telegram_bot_integration import track_conversion_webhook, user_utm_mapping

@bot.message_handler(commands=['buy'])
def handle_buy(message):
    user_id = message.from_user.id

    # ... your payment logic ...

    # After successful payment
    amount_cents = 5000  # $50.00

    # Track conversion
    if user_id in user_utm_mapping:
        utm_id = user_utm_mapping[user_id]
        track_conversion_webhook(
            utm_id=utm_id,
            customer_id=f"telegram_{user_id}",
            amount=amount_cents,
            product_name="Gold Lootbox",
            product_id="lootbox_gold"
        )

    bot.send_message(message.chat.id, "✅ Purchase successful!")
```

### Step 3: Telegram Stars Payment Example

```python
from telebot.types import LabeledPrice

@bot.message_handler(commands=['buy_stars'])
def buy_with_stars(message):
    prices = [LabeledPrice(label="Gold Lootbox", amount=5000)]

    bot.send_invoice(
        message.chat.id,
        title="Gold Lootbox",
        description="Premium lootbox!",
        invoice_payload=f"lootbox_gold_{message.from_user.id}",
        provider_token="",  # Empty for Stars
        currency="XTR",
        prices=prices
    )

@bot.message_handler(content_types=['successful_payment'])
def successful_payment(message):
    user_id = message.from_user.id

    # Track conversion
    if user_id in user_utm_mapping:
        utm_id = user_utm_mapping[user_id]
        track_conversion_webhook(
            utm_id=utm_id,
            customer_id=f"telegram_{user_id}",
            amount=message.successful_payment.total_amount * 100,
            product_name="Gold Lootbox",
            metadata={"payment_method": "telegram_stars"}
        )
```

---

## 📝 Integrating with tg-reposter

### Add UTM Links to Reposts

```python
from examples.tg_reposter_integration import add_utm_to_repost

# When reposting message
original_text = event.message.text
source_channel = "@football_news"

# Add UTM link
enhanced_text = add_utm_to_repost(
    original_text=original_text,
    source_channel=source_channel,
    campaign="repost_jan_2025",
    bot_username="your_bot",
    add_cta=True
)

# Send to target channel
await client.send_message(TARGET_CHANNEL, enhanced_text)
```

**Result:**
```
⚽️ Гол Месси в ворота Реала!

💰 Хочешь зарабатывать? → t.me/your_bot?start=tg_xyz789
```

---

## 📈 Analytics & Reporting

### Dashboard API

```bash
GET /api/v1/analytics/dashboard?date_from=2025-01-01&date_to=2025-01-31
```

**Response:**
```json
{
  "success": true,
  "summary": {
    "total_clicks": 5432,
    "total_conversions": 678,
    "total_revenue": 33900.00,
    "conversion_rate": 12.5,
    "avg_order_value": 50.00
  },
  "link_type_breakdown": [
    {
      "link_type": "landing",
      "clicks": 3200,
      "conversions": 320,
      "revenue": 16000.00,
      "conversion_rate": 10.0
    },
    {
      "link_type": "direct",
      "clicks": 2232,
      "conversions": 358,
      "revenue": 17900.00,
      "conversion_rate": 16.0
    }
  ],
  "device_breakdown": [
    {"device": "mobile", "clicks": 4100},
    {"device": "desktop", "clicks": 1332}
  ]
}
```

### Key Insights

**Landing vs Direct:**
- Landing links: Better for cold traffic (TikTok, Instagram)
- Direct links: Better for warm traffic (Telegram, retargeting)
- Direct links typically have 1.5-2x higher conversion rate

---

## 🔒 Security Best Practices

### 1. Set Strong Secrets

```bash
# Generate JWT secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 2. Configure CORS

```env
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### 3. Enable GeoIP (Optional)

```bash
# Download GeoLite2 database
wget https://git.io/GeoLite2-City.mmdb

# Set path in .env
GEOIP_DB_PATH=./GeoLite2-City.mmdb
```

### 4. Use HTTPS in Production

```nginx
# Nginx config
server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 🐛 Troubleshooting

### Admin Bot не отвечает

```bash
# Check bot token
echo $ADMIN_BOT_TOKEN

# Test bot
curl https://api.telegram.org/bot$ADMIN_BOT_TOKEN/getMe

# Check admin IDs
echo $ADMIN_IDS
```

### Database connection error

```bash
# Test connection
psql $DATABASE_URL

# Run migrations
alembic upgrade head
```

### GeoIP not working

```bash
# Check if database exists
ls -lh $GEOIP_DB_PATH

# Download if missing
# See: https://dev.maxmind.com/geoip/geolite2-free-geolocation-data
```

---

## 📚 API Reference

Full API documentation: `http://localhost:8000/docs`

### Key Endpoints

**Generate UTM:**
```
POST /api/v1/utm/generate
```

**Track Click:**
```
POST /api/v1/utm/track/click
```

**Track Conversion (Webhook):**
```
POST /api/v1/utm/webhook/conversion
```

**Dashboard:**
```
GET /api/v1/analytics/dashboard
```

**Landing Page:**
```
GET /api/v1/landing/l/{utm_id}
```

---

## 🎓 Best Practices

### Campaign Naming

```
Format: {vertical}_{period}_{variant}
Examples:
- football_jan_2025
- crypto_dec_2024_v2
- repost_week52_2024
```

### Content ID

```
Format: {type}_{identifier}
Examples:
- video_messi_goal
- post_12345
- repost_sports_channel
```

### Link Placement

**TikTok:**
- Use landing links in bio
- Track video ID in content parameter
- Update link weekly

**Telegram:**
- Use direct links in posts
- Add CTA to reposts
- Track source channel

---

## 💡 Pro Tips

1. **Test links before sharing**
   - Use `/api/v1/landing/preview` to test landing page
   - Send test message with UTM to verify tracking

2. **Monitor conversion rates**
   - Track CR by link type
   - A/B test different CTAs
   - Optimize based on data

3. **Use smart CTAs**
   - Match CTA to content
   - Sports: "⚽️ Обсудить матч"
   - Crypto: "💰 Получи бонус"
   - News: "📰 Больше новостей"

4. **Clean up old UTMs**
   - Archive campaigns after 90 days
   - Keep top performers for analysis

---

## 🚀 Going to Production

### Checklist

- [ ] Set strong JWT_SECRET_KEY
- [ ] Configure ALLOWED_ORIGINS
- [ ] Enable HTTPS
- [ ] Set up database backups
- [ ] Configure error monitoring (Sentry)
- [ ] Enable rate limiting
- [ ] Set up logging
- [ ] Configure GeoIP
- [ ] Test all flows
- [ ] Document custom integrations

---

## 📞 Support

**Documentation:**
- [System Overview](./SYSTEM_OVERVIEW.md)
- [Admin Bot Guide](./ADMIN_BOT_README.md)
- [API Documentation](http://localhost:8000/docs)

**Issues:**
- Create issue in repository
- Include logs and error messages
- Describe expected vs actual behavior

---

Ready to track! 🎯
