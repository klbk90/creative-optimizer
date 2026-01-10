"""
SQLAlchemy models for PostgreSQL database.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, ARRAY, JSON, BigInteger, Index, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base


class User(Base):
    """User model for SaaS multi-tenancy."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    telegram_id = Column(BigInteger, unique=True, nullable=True, index=True)
    subscription_tier = Column(String(50), default="free", nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    channels = relationship("Channel", back_populates="user", cascade="all, delete-orphan")
    posts = relationship("Post", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    api_usage = relationship("APIUsage", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class Subscription(Base):
    """User subscription and billing information."""

    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    plan = Column(String(50), nullable=False)  # free, starter, pro, enterprise
    status = Column(String(50), nullable=False)  # active, cancelled, expired, past_due
    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)
    cancel_at_period_end = Column(Boolean, default=False)
    stripe_subscription_id = Column(String(255), unique=True, nullable=True)
    stripe_customer_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="subscriptions")

    def __repr__(self):
        return f"<Subscription(id={self.id}, user_id={self.user_id}, plan={self.plan})>"


class Channel(Base):
    """Channel configuration (migrated from config.yaml)."""

    __tablename__ = "channels"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    source_channels = Column(ARRAY(String), nullable=False)  # [@channel1, @channel2]
    target_channel = Column(String(100), nullable=False)

    # Settings (JSONB for flexibility - keeps all existing config structure)
    settings = Column(JSON, nullable=False, default={})
    """
    Example settings structure:
    {
        "rewrite_style": "engaging",
        "generate_images": true,
        "image_generation_style": "football",
        "process_videos": true,
        "process_albums": "first_only",
        "min_text_length": 10,
        "message_effect": null,
        "filters": {
            "skip_forwarded": false,
            "skip_without_media": false,
            "keywords_blacklist": []
        }
    }
    """

    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="channels")
    posts = relationship("Post", back_populates="channel", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Channel(id={self.id}, name={self.name}, target={self.target_channel})>"


class Post(Base):
    """Post history (migrated from processed_posts.json)."""

    __tablename__ = "posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    channel_id = Column(UUID(as_uuid=True), ForeignKey("channels.id"), nullable=True)

    # Source info
    source_channel = Column(String(100), nullable=False)
    source_message_id = Column(BigInteger, nullable=False)

    # Target info
    target_channel = Column(String(100), nullable=False)
    target_message_id = Column(BigInteger, nullable=True)

    # Content
    original_text = Column(Text)
    rewritten_text = Column(Text)
    media_type = Column(String(50))  # photo, video, album, document, none

    # Status
    status = Column(String(50), nullable=False, index=True)  # pending, approved, rejected, published, failed
    moderation_status = Column(String(50))  # pending, approved, rejected

    # Metadata (JSONB for flexibility)
    extra_data = Column(JSON, default={})
    """
    Example extra_data:
    {
        "image_source_type": "search",
        "image_search_query": "football match",
        "image_generation_style": "sports_action",
        "is_forwarded": false,
        "media_path": "temp/photo.jpg"
    }
    """

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    moderated_at = Column(DateTime)
    published_at = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="posts")
    channel = relationship("Channel", back_populates="posts")

    def __repr__(self):
        return f"<Post(id={self.id}, status={self.status}, source={self.source_channel})>"


class APIUsage(Base):
    """API usage tracking for billing and quotas."""

    __tablename__ = "api_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    resource = Column(String(100), nullable=False)  # claude_api, replicate_api, google_search, etc
    usage_count = Column(Integer, default=0, nullable=False)

    # Billing period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    # Cost tracking (optional)
    cost_usd = Column(Integer, default=0)  # in cents

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="api_usage")

    def __repr__(self):
        return f"<APIUsage(user_id={self.user_id}, resource={self.resource}, count={self.usage_count})>"


# Index definitions for better query performance
from sqlalchemy import Index

# Post indexes for common queries
Index("idx_posts_user_status", Post.user_id, Post.status)
Index("idx_posts_created_at_desc", Post.created_at.desc())

# Channel indexes
Index("idx_channels_user_enabled", Channel.user_id, Channel.enabled)

# API Usage indexes
Index("idx_api_usage_user_period", APIUsage.user_id, APIUsage.period_start, APIUsage.period_end)


# ==================== TIKTOK TRACKING MODELS ====================

class TrafficSource(Base):
    """
    UTM tracking for traffic sources.
    Tracks where users come from (TikTok, Instagram, etc.)
    """

    __tablename__ = "traffic_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # Creative link (for testing creatives via influencers)
    creative_id = Column(UUID(as_uuid=True), ForeignKey("creatives.id"), nullable=True, index=True)

    # UTM parameters
    utm_source = Column(String(100), nullable=False, index=True)  # tiktok, instagram, youtube
    utm_medium = Column(String(100))  # social, video, paid
    utm_campaign = Column(String(200), index=True)  # football_jan_2025
    utm_content = Column(String(200))  # video_id or creative_variant
    utm_term = Column(String(200))  # keywords or targeting
    utm_id = Column(String(100), unique=True, index=True)  # unique tracking ID

    # Influencer data (for micro-influencer testing)
    influencer_handle = Column(String(100), nullable=True, index=True)
    influencer_email = Column(String(255), nullable=True)
    influencer_followers = Column(Integer, nullable=True)
    influencer_engagement_rate = Column(Integer, nullable=True)  # ER * 10000 (e.g., 350 = 3.5%)
    influencer_status = Column(String(50), nullable=True)  # potential, contacted, agreed, posted, rejected

    # Landing info
    landing_page = Column(String(500))  # URL where user landed
    referrer = Column(String(500))  # HTTP referrer

    # Request metadata
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(Text)
    device_type = Column(String(50))  # mobile, desktop, tablet
    browser = Column(String(100))
    os = Column(String(100))
    country = Column(String(2))  # ISO country code
    city = Column(String(100))

    # RudderStack tracking
    external_id = Column(String(255), nullable=True)  # RudderStack anonymousId

    # Engagement metrics
    clicks = Column(Integer, default=1, nullable=False)
    time_spent = Column(Integer, default=0)  # seconds on landing page

    # Conversion tracking
    conversions = Column(Integer, default=0)
    revenue = Column(Integer, default=0)  # in cents (USD)

    # Timestamps
    first_click = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_click = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User")
    conversion_events = relationship("Conversion", back_populates="traffic_source", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TrafficSource(utm_source={self.utm_source}, utm_campaign={self.utm_campaign}, clicks={self.clicks})>"


class Conversion(Base):
    """
    Conversion tracking (lootbox purchases, subscriptions, etc.)
    Links back to traffic source to measure ROI.
    """

    __tablename__ = "conversions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    traffic_source_id = Column(UUID(as_uuid=True), ForeignKey("traffic_sources.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)

    # Conversion details
    conversion_type = Column(String(50), nullable=False)  # purchase, signup, deposit
    customer_id = Column(String(100))  # External customer ID (from lootbox system)

    # Transaction details
    amount = Column(Integer, nullable=False)  # in cents
    currency = Column(String(3), default="USD")
    product_id = Column(String(100))
    product_name = Column(String(200))

    # Attribution
    time_to_conversion = Column(Integer)  # seconds from click to conversion

    # Metadata
    extra_data = Column(JSON, default={})
    """
    Example extra_data:
    {
        "lootbox_type": "gold",
        "payment_method": "stripe",
        "transaction_id": "txn_123",
        "coupon_code": "FIRST20"
    }
    """

    # RudderStack tracking
    external_id = Column(String(255), nullable=True)  # RudderStack anonymousId

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    traffic_source = relationship("TrafficSource", back_populates="conversion_events")
    user = relationship("User")

    def __repr__(self):
        return f"<Conversion(type={self.conversion_type}, amount=${self.amount/100:.2f})>"


class TikTokVideo(Base):
    """
    TikTok videos created and scheduled for posting.
    Part of the traffic generation funnel.
    """

    __tablename__ = "tiktok_videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("tiktok_accounts.id"), nullable=True)

    # Video info
    title = Column(String(200))
    caption = Column(Text)
    hashtags = Column(ARRAY(String))

    # File paths
    source_video_path = Column(String(500))  # Original video
    processed_video_path = Column(String(500))  # Processed/edited video
    thumbnail_path = Column(String(500))

    # TikTok IDs (after posting)
    tiktok_video_id = Column(String(100), unique=True, index=True)
    tiktok_share_url = Column(String(500))

    # UTM tracking (for links in bio/comments)
    utm_campaign = Column(String(200), index=True)
    utm_content = Column(String(200))  # video_id
    tracking_link = Column(String(500))  # Short link with UTM

    # Status
    status = Column(String(50), nullable=False, default="draft", index=True)
    # draft, ready, scheduled, publishing, published, failed, deleted

    # Performance metrics (updated via TikTok API)
    views = Column(BigInteger, default=0)
    likes = Column(BigInteger, default=0)
    comments = Column(BigInteger, default=0)
    shares = Column(BigInteger, default=0)
    engagement_rate = Column(Integer, default=0)  # percentage * 100

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    scheduled_at = Column(DateTime, index=True)
    published_at = Column(DateTime)
    last_stats_update = Column(DateTime)

    # Relationships
    user = relationship("User")
    account = relationship("TikTokAccount", back_populates="videos")

    def __repr__(self):
        return f"<TikTokVideo(id={self.id}, status={self.status}, views={self.views})>"


class TikTokAccount(Base):
    """
    TikTok accounts used for posting videos.
    Supports multi-account strategy.
    """

    __tablename__ = "tiktok_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # Account info
    username = Column(String(100), nullable=False, unique=True, index=True)
    display_name = Column(String(100))
    bio = Column(Text)
    profile_image_url = Column(String(500))

    # TikTok credentials (encrypted in production!)
    tiktok_user_id = Column(String(100), unique=True)
    access_token = Column(Text)  # Should be encrypted!
    refresh_token = Column(Text)  # Should be encrypted!
    token_expires_at = Column(DateTime)

    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)

    # Stats
    followers_count = Column(BigInteger, default=0)
    following_count = Column(BigInteger, default=0)
    total_views = Column(BigInteger, default=0)
    total_likes = Column(BigInteger, default=0)

    # Posting limits (daily/hourly limits to avoid bans)
    daily_post_limit = Column(Integer, default=5)
    posts_today = Column(Integer, default=0)
    last_post_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_stats_update = Column(DateTime)

    # Relationships
    user = relationship("User")
    videos = relationship("TikTokVideo", back_populates="account", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TikTokAccount(username={self.username}, followers={self.followers_count})>"


class ContentTemplate(Base):
    """
    Templates for generating viral TikTok content.
    Track which templates perform best.
    """

    __tablename__ = "content_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Template info
    name = Column(String(100), nullable=False)
    template_type = Column(String(50), nullable=False)  # caption, hashtag_set, hook, cta
    category = Column(String(50))  # sports, football, basketball, etc.

    # Template content
    template = Column(Text, nullable=False)
    """
    Example templates:
    - Caption: "{player_name} just did THAT! 🔥 {emoji} #fyp #sports"
    - Hook: "Wait for the end! 😱"
    - CTA: "Follow for daily highlights! ⚽"
    """

    variables = Column(ARRAY(String), default=[])  # [player_name, emoji, team]

    # Performance tracking
    times_used = Column(Integer, default=0)
    total_views = Column(BigInteger, default=0)
    total_engagement = Column(BigInteger, default=0)
    effectiveness_score = Column(Integer, default=0)  # calculated metric

    # A/B testing
    is_active = Column(Boolean, default=True)
    test_group = Column(String(10))  # A, B, C for A/B testing

    # Stats for impressions/clicks (if template includes CTA link)
    impressions = Column(BigInteger, default=0)
    clicks = Column(BigInteger, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<ContentTemplate(name={self.name}, effectiveness={self.effectiveness_score})>"


class Creative(Base):
    """
    Video creatives (UGC, micro-influencer content, ads).
    Stores metadata and performance for Markov Chain analysis.
    """

    __tablename__ = "creatives"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    traffic_source_id = Column(UUID(as_uuid=True), ForeignKey("traffic_sources.id"), nullable=True)

    # Creative info
    name = Column(String(200), nullable=False)
    creative_type = Column(String(50), nullable=False)  # ugc, micro_influencer, studio, spark_ad
    source_platform = Column(String(50))  # tiktok, instagram, youtube
    video_url = Column(String(500))
    thumbnail_url = Column(String(500))

    # Creative metadata
    duration_seconds = Column(Integer)  # video length
    aspect_ratio = Column(String(10))  # 9:16, 16:9, 1:1

    # Cost tracking
    production_cost = Column(Integer, default=0)  # in cents
    media_spend = Column(Integer, default=0)  # ad spend in cents

    # Testing info
    test_phase = Column(String(50))  # micro_test, ugc_test, small_ads, scale
    product_category = Column(String(100))  # lootbox, sports_betting, gambling, etc.
    campaign_tag = Column(String(100))  # Simple campaign tag for MVP tracking

    # EdTech-specific: Target audience pain point
    target_audience_pain = Column(String(100), nullable=True)  # no_time, too_expensive, fear_failure, etc.

    # Psychotype (определяется Claude Vision)
    psychotype = Column(String(100), nullable=True, index=True)  # Switcher, Status Seeker, Skill Upgrader, Freedom Hunter, Safety Seeker

    # CLIP embeddings for similarity analysis (stored as JSON array)
    clip_embedding = Column(JSON)  # 512-dimensional CLIP vector

    # Extracted patterns (populated by creative_analyzer.py)
    hook_type = Column(String(50))  # wait, question, bold_claim, curiosity, urgency
    emotion = Column(String(50))  # excitement, fear, curiosity, greed, fomo
    pacing = Column(String(50))  # fast, medium, slow
    cta_type = Column(String(50))  # direct, soft, urgency, scarcity
    has_text_overlay = Column(Boolean, default=False)
    has_voiceover = Column(Boolean, default=False)

    # AI-extracted features (from GPT-4V analysis)
    features = Column(JSON, default={})
    """
    Example features:
    {
        "has_face": true,
        "num_scenes": 3,
        "color_palette": ["#FF0000", "#00FF00"],
        "text_overlay_count": 2,
        "dominant_colors": ["red", "gold"],
        "visual_complexity": "high",
        "audio_energy": "high"
    }
    """

    # Performance metrics
    impressions = Column(BigInteger, default=0)
    clicks = Column(BigInteger, default=0)
    conversions = Column(Integer, default=0)
    revenue = Column(Integer, default=0)  # in cents

    # App funnel metrics (for white themes: edtech/fitness/finance)
    installs = Column(Integer, default=0)  # App installs
    trial_starts = Column(Integer, default=0)  # Trial activations
    paid_conversions = Column(Integer, default=0)  # Paid subscriptions

    # Calculated metrics
    ctr = Column(Integer, default=0)  # CTR * 10000 (e.g., 250 = 2.50%)
    cvr = Column(Integer, default=0)  # CVR * 10000 (e.g., 1500 = 15.00%)
    roas = Column(Integer, default=0)  # ROAS * 100 (e.g., 350 = 3.5x)
    cpa = Column(Integer, default=0)  # Cost per acquisition in cents

    # Funnel rates (for apps)
    install_rate = Column(Integer, default=0)  # Install rate * 10000
    trial_rate = Column(Integer, default=0)  # Trial activation rate * 10000
    trial_to_paid_rate = Column(Integer, default=0)  # Trial→Paid rate * 10000

    # LTV metrics
    predicted_ltv_d30 = Column(Integer, default=0)  # Predicted 30-day LTV in cents
    predicted_ltv_d90 = Column(Integer, default=0)  # Predicted 90-day LTV in cents
    predicted_ltv_d180 = Column(Integer, default=0)  # Predicted 180-day LTV in cents

    # Markov Chain predictions (before launch)
    predicted_cvr = Column(Integer)  # Predicted CVR * 10000
    predicted_roas = Column(Integer)  # Predicted ROAS * 100
    confidence_score = Column(Integer)  # Prediction confidence * 100

    # Status
    status = Column(String(50), default="draft")  # draft, testing, active, paused, archived
    is_winner = Column(Boolean, default=False)  # Marked as winning creative

    # Analysis tracking (Lazy Analysis Strategy)
    analysis_status = Column(String(20), default='pending')  # pending, processing, completed, failed, skipped
    is_benchmark = Column(Boolean, default=False)  # FB Ad Library benchmark videos
    is_public = Column(Boolean, default=False)  # Public benchmarks accessible to all users
    deeply_analyzed = Column(Boolean, default=False)  # Claude Vision analyzed
    ai_reasoning = Column(Text, nullable=True)  # Claude Vision reasoning
    analysis_cost_cents = Column(Integer, default=0)  # Cost of AI analysis
    analysis_triggered_at = Column(DateTime, nullable=True)
    analyzed_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    tested_at = Column(DateTime)  # When testing started
    last_stats_update = Column(DateTime)

    # Relationships
    user = relationship("User")
    traffic_source = relationship("TrafficSource", foreign_keys="[Creative.traffic_source_id]")
    patterns = relationship("CreativePattern", back_populates="creative", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Creative(name={self.name}, type={self.creative_type}, cvr={self.cvr/100:.2f}%)>"


class CreativePattern(Base):
    """
    Extracted patterns from creatives.
    One creative can have multiple patterns (e.g., hook at 0s, emotion at 2s, CTA at 8s).
    """

    __tablename__ = "creative_patterns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    creative_id = Column(UUID(as_uuid=True), ForeignKey("creatives.id"), nullable=False, index=True)

    # Pattern details
    pattern_type = Column(String(50), nullable=False, index=True)  # hook, emotion, pacing, cta, visual
    pattern_value = Column(String(100), nullable=False, index=True)  # specific pattern (e.g., "wait", "excitement")

    # Timing (when in video this pattern appears)
    start_time = Column(Integer)  # seconds from start
    end_time = Column(Integer)

    # Confidence from AI analysis
    confidence = Column(Integer, default=100)  # confidence * 100 (e.g., 8500 = 85%)

    # Additional metadata
    extra_data = Column(JSON, default={})
    """
    Example extra_data:
    {
        "text": "Wait for it...",
        "screen_position": "top",
        "font_size": "large",
        "color": "#FFFFFF"
    }
    """

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    creative = relationship("Creative", back_populates="patterns")

    def __repr__(self):
        return f"<CreativePattern(type={self.pattern_type}, value={self.pattern_value})>"


class PatternPerformance(Base):
    """
    Aggregated performance by pattern combinations.
    This is what the Markov Chain uses to predict new creatives.
    """

    __tablename__ = "pattern_performance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # Pattern hash (for quick lookup)
    pattern_hash = Column(String(255), nullable=True, index=True)

    # Pattern combination (can be single or multi-pattern)
    hook_type = Column(String(50), index=True)
    emotion = Column(String(50), index=True)
    pacing = Column(String(50), index=True)
    cta_type = Column(String(50))

    # EdTech-specific: Target audience pain point
    target_audience_pain = Column(String(100), nullable=True, index=True)

    # Psychotype (Switcher, Status Seeker, Skill Upgrader, Freedom Hunter, Safety Seeker)
    psychotype = Column(String(100), nullable=True, index=True)

    # Product category (patterns perform differently by product)
    product_category = Column(String(100), index=True)

    # Data source and weighting (for Market Intelligence)
    source = Column(String(50), default='client', index=True)  # 'benchmark' or 'client'
    weight = Column(Float, default=1.0)  # benchmark=2.0 (эталон), client=1.0
    market_longevity_days = Column(Integer, nullable=True)  # How long the ad ran in market
    bayesian_alpha = Column(Float, default=1.0)  # Bayesian prior alpha (successes)
    bayesian_beta = Column(Float, default=1.0)  # Bayesian prior beta (failures)

    # Aggregated metrics from all creatives with this pattern combo
    sample_size = Column(Integer, default=0)  # how many creatives tested
    total_impressions = Column(BigInteger, default=0)
    total_clicks = Column(BigInteger, default=0)
    total_conversions = Column(Integer, default=0)
    total_revenue = Column(Integer, default=0)

    # Average metrics
    avg_ctr = Column(Integer, default=0)  # Average CTR * 10000
    avg_cvr = Column(Integer, default=0)  # Average CVR * 10000
    avg_roas = Column(Integer, default=0)  # Average ROAS * 100

    # Statistical confidence
    confidence_interval_lower = Column(Integer)  # Lower bound of CVR confidence interval
    confidence_interval_upper = Column(Integer)  # Upper bound

    # Markov Chain probability
    transition_probability = Column(Integer)  # P(conversion | pattern) * 10000

    # Last updated (recalculated periodically)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<PatternPerformance(hook={self.hook_type}, emotion={self.emotion}, cvr={self.avg_cvr/100:.2f}%)>"


class LandingPage(Base):
    """
    Landing pages for multi-domain campaigns.
    Allows users to create custom landing pages with templates.
    """

    __tablename__ = "landing_pages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # Landing page info
    name = Column(String(200), nullable=False)
    template = Column(String(50), nullable=False)  # lootbox, betting, casino, generic, minimal
    slug = Column(String(100), unique=True, index=True)  # URL slug

    # Configuration (JSONB)
    config = Column(JSON, nullable=False, default={})
    """
    Example config:
    {
        "title": "Win $500!",
        "headline": "🎁 Win $500 from a $5 Lootbox!",
        "subheadline": "Join now and get instant access!",
        "description": "Limited time offer...",
        "logo_url": "https://...",
        "favicon": "https://...",
        "bg_color": "#667eea",
        "text_color": "#ffffff",
        "accent_color": "#ffd700",
        "emoji": "🎁",
        "redirect_message": "Opening Telegram in",
        "redirect_message_suffix": "seconds...",
        "custom_css": ".headline { font-size: 3rem; }",
        "custom_js": "console.log('Custom tracking');",
    }
    """

    # UTM tracking
    utm_campaign = Column(String(200), index=True)
    utm_source = Column(String(100))
    utm_medium = Column(String(100))

    # Redirect configuration
    redirect_type = Column(String(50), default="bot")  # bot, channel, website
    redirect_url = Column(String(500))  # Full redirect URL (t.me/bot?start={utm_id})
    redirect_delay = Column(Integer, default=3)  # Seconds before redirect

    # Domain configuration (optional - for multi-domain setup)
    custom_domain = Column(String(200), unique=True, index=True, nullable=True)
    is_domain_verified = Column(Boolean, default=False)

    # Status
    status = Column(String(50), default="draft")  # draft, active, paused, archived
    is_published = Column(Boolean, default=False)

    # Performance metrics
    views = Column(BigInteger, default=0)
    clicks = Column(BigInteger, default=0)
    conversions = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime)
    last_view_at = Column(DateTime)

    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<LandingPage(name={self.name}, template={self.template}, views={self.views})>"


class ModelMetrics(Base):
    """
    Метрики качества ML моделей для отслеживания точности.

    Используется для:
    - Отслеживание MAE (Mean Absolute Error)
    - Hit rate (% правильных предсказаний)
    - R² (correlation coefficient)
    - Сравнение версий моделей
    """

    __tablename__ = "model_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    product_category = Column(String(100), nullable=False, index=True)

    # Тип модели
    model_type = Column(String(50), nullable=False)  # markov_chain, gradient_boosting, ensemble

    # Метрики качества (умножены на 10000 для хранения)
    mae = Column(Integer, nullable=False)  # Mean Absolute Error * 10000
    hit_rate = Column(Integer, nullable=False)  # Hit rate * 10000 (0.75 = 7500)
    r_squared = Column(Integer, nullable=True)  # R² * 10000

    # Мета-информация
    sample_size = Column(Integer, nullable=False)  # Сколько креативов в test set
    improved = Column(Boolean, default=False)  # Улучшилась ли модель по сравнению с предыдущей
    model_metadata = Column(JSON, default={})  # Доп. информация (feature importance, etc)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<ModelMetrics(type={self.model_type}, mae={self.mae/10000:.3f}, hit_rate={self.hit_rate/10000:.2%})>"


class UserSession(Base):
    """
    Сессии пользователей для автоатрибуции конверсий.

    Связывает customer_id (из продукта) с utm_id (откуда пришел).
    Используется для автоматического определения какой креатив
    привел к покупке.

    Пример:
    - User приходит по ссылке utm_id="creative_abc"
    - Сохраняем: customer_id="email@example.com" → utm_id="creative_abc"
    - User покупает через неделю
    - Находим по customer_id что он пришел с creative_abc
    - ✅ Атрибутируем покупку к этому креативу!
    """

    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Идентификаторы
    customer_id = Column(String(255), nullable=False, index=True)  # email, telegram_123, user_id
    external_id = Column(String(255), nullable=True, index=True)   # RudderStack anonymousId
    utm_id = Column(String(100), nullable=False, index=True)

    # Связи
    traffic_source_id = Column(UUID(as_uuid=True), ForeignKey("traffic_sources.id"), nullable=True)
    creative_id = Column(UUID(as_uuid=True), ForeignKey("creatives.id"), nullable=True, index=True)

    # Timestamps
    first_interaction = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    last_interaction = Column(DateTime, default=datetime.utcnow, nullable=True)

    # Metadata
    device_type = Column(String(50), nullable=True)
    ip_address = Column(String(45), nullable=True)
    country = Column(String(2), nullable=True)

    # Multi-touch attribution
    touch_count = Column(Integer, default=1)

    # Relationships
    traffic_source = relationship("TrafficSource")
    creative = relationship("Creative")

    # Constraints
    __table_args__ = (
        Index('idx_user_sessions_customer_utm', 'customer_id', 'utm_id', unique=True),
    )

    def __repr__(self):
        return f"<UserSession(customer={self.customer_id}, utm={self.utm_id}, touches={self.touch_count})>"


# Additional indexes for TikTok tracking (commented for MVP)
# Index("idx_traffic_sources_utm_lookup", TrafficSource.utm_source, TrafficSource.utm_campaign, TrafficSource.created_at.desc())
# Index("idx_conversions_created_at_desc", Conversion.created_at.desc())
Index("idx_tiktok_videos_status_scheduled", TikTokVideo.status, TikTokVideo.scheduled_at)
Index("idx_tiktok_accounts_active", TikTokAccount.user_id, TikTokAccount.is_active)

# Creative analysis indexes
Index("idx_creatives_user_status", Creative.user_id, Creative.status)
Index("idx_creatives_product_category", Creative.product_category, Creative.cvr.desc())
Index("idx_creatives_performance", Creative.user_id, Creative.cvr.desc(), Creative.conversions.desc())
Index("idx_pattern_performance_lookup", PatternPerformance.user_id, PatternPerformance.product_category, PatternPerformance.hook_type, PatternPerformance.emotion)
Index("idx_creative_patterns_type_value", CreativePattern.pattern_type, CreativePattern.pattern_value)

# Landing pages indexes
Index("idx_landing_pages_user_status", LandingPage.user_id, LandingPage.status)
Index("idx_landing_pages_slug", LandingPage.slug)
Index("idx_landing_pages_domain", LandingPage.custom_domain)

# Model metrics indexes
Index("idx_model_metrics_user_type", ModelMetrics.user_id, ModelMetrics.model_type, ModelMetrics.created_at.desc())
Index("idx_model_metrics_product", ModelMetrics.product_category, ModelMetrics.model_type)
