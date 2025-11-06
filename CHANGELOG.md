# Changelog

## [2.0.0] - 2025-01-06

### 🎉 Major Features

#### Two Link Types Support
- **Landing Links**: For TikTok/Instagram bio with beautiful intermediate page
- **Direct Links**: For Telegram reposts with native experience
- Admin Bot now asks which type to generate

#### Enhanced Tracking
- **GeoIP Support**: Automatic country/city detection from IP
- **Device Fingerprinting**: Track device type, browser, OS
- **Time on Page**: Track how long users spend on landing pages
- **Link Type Analytics**: Separate stats for landing vs direct links

#### Security Improvements
- **CORS Configuration**: Proper origin whitelisting
- **Rate Limiting**: Protection against abuse
- **Encryption Service**: Encrypt sensitive tokens (TikTok access tokens)
- **Security Headers**: X-Content-Type-Options, X-Frame-Options, etc.

#### Better Integration
- **Webhook Endpoint**: Easy conversion tracking without auth
- **User Bot Examples**: Complete integration examples for lootbox bots
- **tg-reposter Integration**: Example showing how to add UTM to reposts
- **Telegram Stars Support**: Native Telegram payments integration

### ✨ New Components

- `utils/geoip.py` - GeoIP lookup service
- `utils/security.py` - Encryption and security utilities
- `telegram_bot_integration.py` - Complete integration examples
- `examples/tg_reposter_integration.py` - tg-reposter integration
- `docs/IMPLEMENTATION_GUIDE.md` - Comprehensive setup guide

### 🔧 Improvements

- **Admin Bot**: Added link type selection with visual indicators
- **Analytics API**: Added link_type_breakdown to dashboard
- **utm.py**: Supports both landing and direct link generation
- **landing.py**: Beautiful landing pages with auto-redirect
- **Requirements**: Added geoip2, cryptography, slowapi

### 📊 Analytics Enhancements

- Link type breakdown (landing vs direct)
- Conversion rate comparison
- Device breakdown
- Campaign performance tracking
- Time-series analysis with custom granularity

### 🐛 Bug Fixes

- Fixed missing dependencies (cache.py, queue.py, utils/logger.py)
- Fixed missing schemas in database/schemas.py
- Fixed CORS configuration (was allowing all origins)
- Fixed user-agent parsing for better device detection

### 📝 Documentation

- Added comprehensive IMPLEMENTATION_GUIDE.md
- Updated SYSTEM_OVERVIEW.md
- Added inline code documentation
- Created integration examples

---

## [1.0.0] - Initial Release

### Features

- Basic UTM tracking
- PostgreSQL database
- Admin Bot for link generation
- Analytics dashboard
- Landing pages
- Conversion tracking
- TikTok video management

### Components

- FastAPI backend
- Telegram Admin Bot
- PostgreSQL + Redis
- Docker Compose setup

---

## Future Roadmap

### v2.1.0 (Planned)
- [ ] Web dashboard (React)
- [ ] A/B testing for landing pages
- [ ] Automated reports via email
- [ ] TikTok API integration
- [ ] Multi-user support with roles

### v2.2.0 (Planned)
- [ ] Webhook integrations (Slack, Discord)
- [ ] Advanced attribution models
- [ ] Cohort analysis
- [ ] Predictive analytics
- [ ] Export to CSV/Excel

### v3.0.0 (Future)
- [ ] SaaS multi-tenancy
- [ ] Billing & subscriptions
- [ ] White-label solution
- [ ] Mobile app
- [ ] API SDK (Python, Node.js)
