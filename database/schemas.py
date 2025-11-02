"""
Pydantic schemas for API request/response validation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


# ============================================================================
# User Schemas
# ============================================================================

class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=8)
    telegram_id: Optional[int] = None


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Schema for user profile update."""
    email: Optional[EmailStr] = None
    telegram_id: Optional[int] = None


class UserResponse(UserBase):
    """Schema for user response."""
    id: UUID
    telegram_id: Optional[int]
    subscription_tier: str
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Auth Schemas
# ============================================================================

class Token(BaseModel):
    """JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data."""
    user_id: str
    email: str


# ============================================================================
# Channel Schemas
# ============================================================================

class ChannelSettings(BaseModel):
    """Channel settings (from config.yaml)."""
    rewrite_style: str = "original"
    generate_images: bool = True
    image_generation_style: Optional[str] = None
    process_videos: bool = True
    process_albums: str = "first_only"
    min_text_length: int = 10
    message_effect: Optional[int] = None
    filters: Dict[str, Any] = Field(default_factory=dict)


class ChannelBase(BaseModel):
    """Base channel schema."""
    name: str = Field(..., min_length=1, max_length=100)
    source_channels: List[str] = Field(..., min_items=1)
    target_channel: str = Field(..., min_length=1)
    settings: ChannelSettings = Field(default_factory=ChannelSettings)


class ChannelCreate(ChannelBase):
    """Schema for creating a channel."""
    pass


class ChannelUpdate(BaseModel):
    """Schema for updating a channel."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    source_channels: Optional[List[str]] = None
    target_channel: Optional[str] = None
    settings: Optional[ChannelSettings] = None
    enabled: Optional[bool] = None


class ChannelResponse(ChannelBase):
    """Schema for channel response."""
    id: UUID
    user_id: UUID
    enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Post Schemas
# ============================================================================

class PostBase(BaseModel):
    """Base post schema."""
    source_channel: str
    target_channel: str
    original_text: Optional[str] = None
    media_type: Optional[str] = None


class PostCreate(PostBase):
    """Schema for creating a post."""
    channel_id: Optional[UUID] = None
    source_message_id: int


class PostUpdate(BaseModel):
    """Schema for updating a post."""
    rewritten_text: Optional[str] = None
    status: Optional[str] = None
    moderation_status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PostResponse(PostBase):
    """Schema for post response."""
    id: UUID
    user_id: UUID
    channel_id: Optional[UUID]
    source_message_id: int
    target_message_id: Optional[int]
    rewritten_text: Optional[str]
    status: str
    moderation_status: Optional[str]
    metadata: Dict[str, Any]
    created_at: datetime
    moderated_at: Optional[datetime]
    published_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============================================================================
# Subscription Schemas
# ============================================================================

class SubscriptionBase(BaseModel):
    """Base subscription schema."""
    plan: str = Field(..., pattern="^(free|starter|pro|enterprise)$")


class SubscriptionCreate(SubscriptionBase):
    """Schema for creating subscription."""
    payment_method_id: Optional[str] = None  # Stripe payment method


class SubscriptionResponse(SubscriptionBase):
    """Schema for subscription response."""
    id: UUID
    user_id: UUID
    status: str
    current_period_start: Optional[datetime]
    current_period_end: Optional[datetime]
    cancel_at_period_end: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# API Usage Schemas
# ============================================================================

class APIUsageResponse(BaseModel):
    """Schema for API usage response."""
    resource: str
    usage_count: int
    period_start: datetime
    period_end: datetime
    cost_usd: int

    class Config:
        from_attributes = True


class UsageSummary(BaseModel):
    """Summary of all API usage for a user."""
    total_posts: int
    total_ai_generations: int
    total_searches: int
    current_period_start: datetime
    current_period_end: datetime
    plan_limits: Dict[str, int]


# ============================================================================
# Analytics Schemas
# ============================================================================

class ChannelStats(BaseModel):
    """Statistics for a channel."""
    channel_id: UUID
    channel_name: str
    total_posts: int
    approved_posts: int
    rejected_posts: int
    published_posts: int
    avg_processing_time: Optional[float]


class UserStats(BaseModel):
    """Overall user statistics."""
    total_channels: int
    total_posts: int
    posts_this_month: int
    channels: List[ChannelStats]


# ============================================================================
# Pagination
# ============================================================================

class PaginationParams(BaseModel):
    """Pagination parameters."""
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""
    items: List[Any]
    total: int
    skip: int
    limit: int
    has_more: bool


# ============================================================================
# TikTok Tracking Schemas
# ============================================================================

class TrafficSourceBase(BaseModel):
    """Base traffic source schema."""
    utm_source: str
    utm_medium: Optional[str] = "social"
    utm_campaign: Optional[str] = None
    utm_content: Optional[str] = None
    utm_term: Optional[str] = None


class TrafficSourceCreate(TrafficSourceBase):
    """Schema for creating a traffic source."""
    landing_page: Optional[str] = None
    referrer: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class TrafficSourceResponse(TrafficSourceBase):
    """Schema for traffic source response."""
    id: UUID
    user_id: UUID
    utm_id: str
    clicks: int
    conversions: int
    revenue: int
    first_click: datetime
    last_click: datetime
    device_type: Optional[str]
    country: Optional[str]

    class Config:
        from_attributes = True


class ConversionBase(BaseModel):
    """Base conversion schema."""
    conversion_type: str
    amount: int
    currency: str = "USD"
    product_id: Optional[str] = None
    product_name: Optional[str] = None


class ConversionCreate(ConversionBase):
    """Schema for creating a conversion."""
    traffic_source_id: UUID
    customer_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ConversionResponse(ConversionBase):
    """Schema for conversion response."""
    id: UUID
    traffic_source_id: UUID
    user_id: Optional[UUID]
    customer_id: Optional[str]
    time_to_conversion: Optional[int]
    metadata: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class TikTokVideoBase(BaseModel):
    """Base TikTok video schema."""
    title: Optional[str] = None
    caption: Optional[str] = None
    hashtags: Optional[List[str]] = None


class TikTokVideoCreate(TikTokVideoBase):
    """Schema for creating a TikTok video."""
    account_id: Optional[UUID] = None
    source_video_path: str
    utm_campaign: Optional[str] = None


class TikTokVideoUpdate(BaseModel):
    """Schema for updating a TikTok video."""
    title: Optional[str] = None
    caption: Optional[str] = None
    hashtags: Optional[List[str]] = None
    status: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    tiktok_video_id: Optional[str] = None
    views: Optional[int] = None
    likes: Optional[int] = None
    comments: Optional[int] = None
    shares: Optional[int] = None


class TikTokVideoResponse(TikTokVideoBase):
    """Schema for TikTok video response."""
    id: UUID
    user_id: UUID
    account_id: Optional[UUID]
    status: str
    utm_campaign: Optional[str]
    tracking_link: Optional[str]
    views: int
    likes: int
    comments: int
    shares: int
    engagement_rate: int
    created_at: datetime
    scheduled_at: Optional[datetime]
    published_at: Optional[datetime]

    class Config:
        from_attributes = True


class TikTokAccountBase(BaseModel):
    """Base TikTok account schema."""
    username: str
    display_name: Optional[str] = None
    bio: Optional[str] = None


class TikTokAccountCreate(TikTokAccountBase):
    """Schema for creating a TikTok account."""
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None


class TikTokAccountUpdate(BaseModel):
    """Schema for updating a TikTok account."""
    display_name: Optional[str] = None
    bio: Optional[str] = None
    is_active: Optional[bool] = None
    daily_post_limit: Optional[int] = None


class TikTokAccountResponse(TikTokAccountBase):
    """Schema for TikTok account response."""
    id: UUID
    user_id: UUID
    is_active: bool
    is_verified: bool
    is_banned: bool
    followers_count: int
    following_count: int
    total_views: int
    total_likes: int
    daily_post_limit: int
    posts_today: int
    created_at: datetime

    class Config:
        from_attributes = True


class ContentTemplateBase(BaseModel):
    """Base content template schema."""
    name: str
    template_type: str
    category: Optional[str] = None
    template: str
    variables: Optional[List[str]] = None


class ContentTemplateCreate(ContentTemplateBase):
    """Schema for creating a content template."""
    test_group: Optional[str] = None


class ContentTemplateUpdate(BaseModel):
    """Schema for updating a content template."""
    name: Optional[str] = None
    template: Optional[str] = None
    is_active: Optional[bool] = None
    effectiveness_score: Optional[int] = None


class ContentTemplateResponse(ContentTemplateBase):
    """Schema for content template response."""
    id: UUID
    user_id: Optional[UUID]
    times_used: int
    total_views: int
    total_engagement: int
    effectiveness_score: int
    is_active: bool
    impressions: int
    clicks: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# UTM & Analytics Schemas
# ============================================================================

class UTMGenerateRequest(BaseModel):
    """Request for generating UTM link."""
    base_url: str = Field(..., example="https://t.me/sportschannel")
    source: str = Field(..., example="tiktok")
    medium: str = Field(default="social", example="social")
    campaign: Optional[str] = Field(None, example="football_jan_2025")
    content: Optional[str] = Field(None, example="video_123")
    term: Optional[str] = Field(None, example="evening_post")


class UTMGenerateResponse(BaseModel):
    """Response for UTM link generation."""
    success: bool
    utm_link: str
    utm_id: str
    short_link: Optional[str] = None


class TrackClickRequest(BaseModel):
    """Request for tracking a click."""
    utm_id: str
    landing_page: Optional[str] = None
    referrer: Optional[str] = None


class TrackClickResponse(BaseModel):
    """Response for click tracking."""
    success: bool
    tracking_id: str
    message: str = "Click tracked successfully"


class AnalyticsSummary(BaseModel):
    """Analytics summary."""
    period: Dict[str, Optional[str]]
    total_clicks: int
    total_conversions: int
    total_revenue: float
    conversion_rate: float
    avg_order_value: float
    top_sources: List[Dict[str, Any]]
    daily_stats: List[Dict[str, Any]]


class CampaignPerformance(BaseModel):
    """Campaign performance metrics."""
    campaign_name: str
    total_videos: int
    published_videos: int
    total_views: int
    total_engagement: int
    total_clicks: int
    total_conversions: int
    total_revenue: float
    roi: float  # Return on Investment
