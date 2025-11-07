# Changelog

## [3.0.0] - 2025-01-07

### 🎉 Major Features: Markov Chain Creative Analysis

#### Creative Performance Prediction
- **Markov Chain Model**: Predict creative CVR BEFORE spending on ads
- **Pattern Extraction**: Automatically extract hooks, emotions, pacing from videos
- **Statistical Confidence**: Confidence intervals and sample size tracking
- **Bayesian Updates**: Predictions improve as you gather more data
- **Save 50-70% Testing Budget**: Filter out bad creatives before launch

#### New Database Models
- `Creative`: Store video creatives with patterns and performance
- `CreativePattern`: Extract and store patterns from creatives
- `PatternPerformance`: Aggregated performance by pattern combinations

#### New API Endpoints
- `POST /api/v1/creative/analyze`: Analyze creative and predict performance
- `POST /api/v1/creative/creatives`: Save creative to database
- `PUT /api/v1/creative/creatives/{id}`: Update creative performance
- `GET /api/v1/creative/patterns/top`: Get top performing patterns
- `POST /api/v1/creative/patterns/update`: Recalculate pattern performance
- `GET /api/v1/creative/creatives/{id}/similar`: Find similar creatives

#### New Utilities
- `utils/markov_chain.py`: Markov Chain predictor implementation
- `utils/creative_analyzer.py`: CLIP + Claude-based pattern extraction

#### Comprehensive Documentation
- **[CREATIVE_ANALYSIS_GUIDE.md](docs/CREATIVE_ANALYSIS_GUIDE.md)**: Complete Markov Chain guide
- **[UGC_BRIEFS.md](docs/UGC_BRIEFS.md)**: Ready-made UGC briefs for 6 product categories
- **[TIKTOK_SPARK_ADS.md](docs/TIKTOK_SPARK_ADS.md)**: Complete TikTok Spark Ads setup

### ✨ Improvements

- Updated `requirements.txt` with ML dependencies (numpy, scipy, anthropic)
- Added CLIP embeddings support (optional)
- Enhanced README with Markov Chain use cases
- Integrated creative analysis workflow with UTM tracking

### 📊 Pattern Library

Pre-defined patterns with performance benchmarks:
- **Hook Types**: wait, question, bold_claim, curiosity, urgency
- **Emotions**: excitement, fear, curiosity, greed, surprise
- **Pacing**: fast, medium, slow
- **CTA Types**: direct, soft, urgency, scarcity

### 🔧 Integration

- Seamless integration with existing UTM tracking
- Links creative performance to traffic sources
- Webhook support for automatic performance updates

---

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
