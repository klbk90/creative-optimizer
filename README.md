# 🎯 UTM Tracking & Analytics System

**Complete UTM tracking solution for TikTok → Telegram → Conversion funnel**

Built with FastAPI, PostgreSQL, Redis, and Telegram Admin Bot.

## ✨ Key Features

### 🔗 **Dual Link System**

1. **Landing Links** 🌐 - For TikTok/Instagram bio
   - Beautiful branded intermediate page
   - Auto-redirect to Telegram after 3 seconds
   - Track device, geo, time on page
   - Perfect for cold traffic

2. **Direct Links** 📱 - For Telegram reposts
   - Native Telegram deep links
   - No intermediate page
   - Higher conversion rates
   - Perfect for warm traffic

### 📊 **Advanced Analytics**

- Real-time dashboard with key metrics
- Conversion funnel analysis
- Link type comparison (landing vs direct)
- Device & geo breakdown
- Campaign performance tracking
- Time-series data with custom granularity

### 💰 **Conversion Tracking**

- Webhook endpoint for easy integration
- Support for Telegram Stars, Stripe, etc.
- Automatic time-to-conversion calculation
- Revenue attribution to traffic sources

### 🤖 **Telegram Admin Bot**

- Interactive UTM link generation
- Choose link type (landing/direct)
- View statistics (today/7d/30d)
- Campaign management
- Top performers tracking
- Daily automated reports

### 🔒 **Security & Privacy**

- JWT authentication
- CORS configuration
- Rate limiting
- Token encryption
- GeoIP lookup (optional)
- Security headers

## 🚀 Quick Start

See **[docs/IMPLEMENTATION_GUIDE.md](docs/IMPLEMENTATION_GUIDE.md)** for complete setup.

```bash
# 1. Install
pip install -r requirements.txt

# 2. Configure
cp .env.example .env

# 3. Start
docker-compose up -d
```

## 📚 Documentation

- **[Implementation Guide](docs/IMPLEMENTATION_GUIDE.md)** - Complete setup & integration
- [Quick Start](docs/QUICKSTART.md) - Fast setup guide
- [Admin Bot Guide](docs/ADMIN_BOT_README.md) - Bot usage & commands
- [System Overview](docs/SYSTEM_OVERVIEW.md) - Architecture & components
- [API Documentation](http://localhost:8000/docs) - Interactive API docs

## 🎯 Use Cases

### Scenario 1: TikTok → Telegram → Lootbox

```
1. Create video on TikTok
2. Generate landing link via Admin Bot
3. Add link to TikTok bio
4. User clicks → Beautiful landing page
5. Auto-redirect to Telegram channel
6. User joins channel → Opens bot
7. User buys lootbox → Conversion tracked
```

### Scenario 2: Telegram Repost → Bot

```
1. Repost message to channel
2. Add direct link with UTM
3. User clicks → Opens bot directly
4. User buys → Conversion tracked
```

## 🔧 Integration Examples

### User Bot (Lootbox)

```python
from telegram_bot_integration import track_click, track_conversion_webhook

@bot.message_handler(commands=['start'])
def handle_start(message):
    utm_id = message.text.split()[1] if len(message.text.split()) > 1 else None
    if utm_id:
        track_click(utm_id, message.from_user.id)

@bot.message_handler(commands=['buy'])
def handle_buy(message):
    # After successful payment
    track_conversion_webhook(
        utm_id=saved_utm_id,
        customer_id=f"telegram_{message.from_user.id}",
        amount=5000,  # $50 in cents
        product_name="Gold Lootbox"
    )
```

### tg-reposter

```python
from examples.tg_reposter_integration import add_utm_to_repost

enhanced_text = add_utm_to_repost(
    original_text="⚽️ Гол Месси!",
    source_channel="@football",
    campaign="repost_jan_2025",
    bot_username="your_bot"
)
# Result: "⚽️ Гол Месси!\n\n💰 Хочешь зарабатывать? → t.me/your_bot?start=tg_xyz"
```

## 📊 Analytics Example

```json
{
  "summary": {
    "total_clicks": 5432,
    "total_conversions": 678,
    "total_revenue": 33900.00,
    "conversion_rate": 12.5
  },
  "link_type_breakdown": [
    {
      "link_type": "landing",
      "clicks": 3200,
      "conversions": 320,
      "conversion_rate": 10.0
    },
    {
      "link_type": "direct",
      "clicks": 2232,
      "conversions": 358,
      "conversion_rate": 16.0
    }
  ]
}
```

**Key Insight:** Direct links have ~60% higher conversion rate!

## 🎨 Screenshots

### Admin Bot
<details>
<summary>Click to expand</summary>

```
/generate

✅ Campaign: football_jan_2025

Choose link type:
🌐 Landing Page (для TikTok bio)
📱 Direct Link (для репостов)

→ Selected: Landing Page

Choose source:
📱 TikTok  📷 Instagram
💬 Telegram  🌐 Other

✅ UTM link created!
🔗 Link: https://yourdomain.com/l/tiktok_abc123
```
</details>

### Landing Page
<details>
<summary>Click to expand</summary>

Beautiful gradient page with:
- Channel logo & name
- Feature highlights
- Member count stats
- Auto-redirect countdown
- Join button

Fully responsive & mobile-optimized!
</details>

## 🛠️ Installation

```bash
# Clone repository
git clone <repo-url>
cd utm-tracking

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
nano .env

# Run with Docker Compose
docker-compose up -d

# Or run manually
python api/main.py          # API
python bots/admin_bot.py   # Admin Bot
```

## 🌟 What's New in v2.0

- ✅ Dual link system (landing + direct)
- ✅ GeoIP country/city detection
- ✅ Security improvements (CORS, rate limiting, encryption)
- ✅ Webhook conversion endpoint
- ✅ Link type analytics
- ✅ Complete integration examples
- ✅ Comprehensive documentation

See [CHANGELOG.md](CHANGELOG.md) for details.

## Tech Stack

- **Backend:** FastAPI (Python 3.11+)
- **Database:** PostgreSQL
- **Cache:** Redis
- **Bots:** pyTelegramBotAPI
- **Security:** JWT, Cryptography, slowapi
- **GeoIP:** MaxMind GeoLite2
- **Deployment:** Docker, Docker Compose

## License

MIT

---

**Ready to track conversions? 🚀**

Start with [docs/IMPLEMENTATION_GUIDE.md](docs/IMPLEMENTATION_GUIDE.md)
