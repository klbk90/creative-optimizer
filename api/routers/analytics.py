"""
Analytics router for campaign performance and metrics.
Dashboard data for tracking ROI and optimization.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict

from database.base import get_db
from database.models import TrafficSource, Conversion, TikTokVideo, TikTokAccount, User
from database.schemas import AnalyticsSummary, CampaignPerformance
from api.dependencies import get_current_user
from utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()


@router.get("/dashboard", response_model=Dict[str, Any])
async def get_dashboard(
    date_from: Optional[datetime] = Query(None, description="Start date for analytics"),
    date_to: Optional[datetime] = Query(None, description="End date for analytics"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get comprehensive dashboard analytics.

    Returns:
    - Summary metrics (clicks, conversions, revenue)
    - Top sources and campaigns
    - Daily stats
    - TikTok video performance
    """
    # Default to last 30 days
    if not date_from:
        date_from = datetime.utcnow() - timedelta(days=30)
    if not date_to:
        date_to = datetime.utcnow()

    # Query traffic sources in date range
    traffic_sources = db.query(TrafficSource).filter(
        and_(
            TrafficSource.user_id == current_user.id,
            TrafficSource.first_click >= date_from,
            TrafficSource.first_click <= date_to,
        )
    ).all()

    # Calculate summary
    total_clicks = sum(ts.clicks for ts in traffic_sources)
    total_conversions = sum(ts.conversions for ts in traffic_sources)
    total_revenue = sum(ts.revenue for ts in traffic_sources)

    conversion_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
    avg_order_value = (total_revenue / total_conversions / 100) if total_conversions > 0 else 0

    # Top sources
    source_stats = defaultdict(lambda: {"clicks": 0, "conversions": 0, "revenue": 0})
    for ts in traffic_sources:
        source_stats[ts.utm_source]["clicks"] += ts.clicks
        source_stats[ts.utm_source]["conversions"] += ts.conversions
        source_stats[ts.utm_source]["revenue"] += ts.revenue

    top_sources = [
        {
            "source": source,
            "clicks": stats["clicks"],
            "conversions": stats["conversions"],
            "revenue": stats["revenue"] / 100,
            "conversion_rate": (stats["conversions"] / stats["clicks"] * 100) if stats["clicks"] > 0 else 0,
        }
        for source, stats in sorted(
            source_stats.items(),
            key=lambda x: x[1]["revenue"],
            reverse=True
        )
    ]

    # Top campaigns
    campaign_stats = defaultdict(lambda: {"clicks": 0, "conversions": 0, "revenue": 0})
    for ts in traffic_sources:
        if ts.utm_campaign:
            campaign_stats[ts.utm_campaign]["clicks"] += ts.clicks
            campaign_stats[ts.utm_campaign]["conversions"] += ts.conversions
            campaign_stats[ts.utm_campaign]["revenue"] += ts.revenue

    top_campaigns = [
        {
            "campaign": campaign,
            "clicks": stats["clicks"],
            "conversions": stats["conversions"],
            "revenue": stats["revenue"] / 100,
            "conversion_rate": (stats["conversions"] / stats["clicks"] * 100) if stats["clicks"] > 0 else 0,
        }
        for campaign, stats in sorted(
            campaign_stats.items(),
            key=lambda x: x[1]["revenue"],
            reverse=True
        )[:10]
    ]

    # Daily stats
    daily_stats = defaultdict(lambda: {"clicks": 0, "conversions": 0, "revenue": 0})
    for ts in traffic_sources:
        date_key = ts.first_click.date().isoformat()
        daily_stats[date_key]["clicks"] += ts.clicks
        daily_stats[date_key]["conversions"] += ts.conversions
        daily_stats[date_key]["revenue"] += ts.revenue

    daily_chart = [
        {
            "date": date,
            "clicks": stats["clicks"],
            "conversions": stats["conversions"],
            "revenue": stats["revenue"] / 100,
        }
        for date, stats in sorted(daily_stats.items())
    ]

    # TikTok stats
    tiktok_videos = db.query(TikTokVideo).filter(
        and_(
            TikTokVideo.user_id == current_user.id,
            TikTokVideo.created_at >= date_from,
            TikTokVideo.created_at <= date_to,
        )
    ).all()

    total_videos = len(tiktok_videos)
    published_videos = len([v for v in tiktok_videos if v.status == "published"])
    total_video_views = sum(v.views for v in tiktok_videos)
    total_video_engagement = sum(v.likes + v.comments + v.shares for v in tiktok_videos)

    # Device breakdown
    device_stats = defaultdict(int)
    for ts in traffic_sources:
        if ts.device_type:
            device_stats[ts.device_type] += ts.clicks

    device_breakdown = [
        {"device": device, "clicks": clicks}
        for device, clicks in device_stats.items()
    ]

    return {
        "success": True,
        "period": {
            "from": date_from.isoformat(),
            "to": date_to.isoformat(),
        },
        "summary": {
            "total_clicks": total_clicks,
            "total_conversions": total_conversions,
            "total_revenue": total_revenue / 100,
            "conversion_rate": round(conversion_rate, 2),
            "avg_order_value": round(avg_order_value, 2),
        },
        "tiktok": {
            "total_videos": total_videos,
            "published_videos": published_videos,
            "total_views": total_video_views,
            "total_engagement": total_video_engagement,
            "avg_views_per_video": (total_video_views / published_videos) if published_videos > 0 else 0,
        },
        "top_sources": top_sources,
        "top_campaigns": top_campaigns,
        "daily_stats": daily_chart,
        "device_breakdown": device_breakdown,
    }


@router.get("/campaign/{campaign_name}", response_model=Dict[str, Any])
async def get_campaign_analytics(
    campaign_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get detailed analytics for a specific campaign.

    Includes:
    - Traffic source breakdown
    - Conversion funnel
    - TikTok video performance
    - ROI calculation
    """
    # Get traffic sources for this campaign
    traffic_sources = db.query(TrafficSource).filter(
        and_(
            TrafficSource.user_id == current_user.id,
            TrafficSource.utm_campaign == campaign_name,
        )
    ).all()

    if not traffic_sources:
        return {
            "success": False,
            "message": f"No data found for campaign: {campaign_name}",
        }

    # Calculate metrics
    total_clicks = sum(ts.clicks for ts in traffic_sources)
    total_conversions = sum(ts.conversions for ts in traffic_sources)
    total_revenue = sum(ts.revenue for ts in traffic_sources)

    # Get TikTok videos for this campaign
    videos = db.query(TikTokVideo).filter(
        and_(
            TikTokVideo.user_id == current_user.id,
            TikTokVideo.utm_campaign == campaign_name,
        )
    ).all()

    total_videos = len(videos)
    published_videos = len([v for v in videos if v.status == "published"])
    total_views = sum(v.views for v in videos)
    total_engagement = sum(v.likes + v.comments + v.shares for v in videos)

    # Top performing videos
    top_videos = sorted(videos, key=lambda v: v.views, reverse=True)[:10]
    top_videos_data = [
        {
            "id": str(v.id),
            "title": v.title or "Untitled",
            "views": v.views,
            "likes": v.likes,
            "comments": v.comments,
            "shares": v.shares,
            "engagement_rate": v.engagement_rate / 100,
            "tracking_link": v.tracking_link,
            "published_at": v.published_at.isoformat() if v.published_at else None,
        }
        for v in top_videos
    ]

    # Traffic source breakdown
    source_breakdown = {}
    for ts in traffic_sources:
        if ts.utm_source not in source_breakdown:
            source_breakdown[ts.utm_source] = {
                "clicks": 0,
                "conversions": 0,
                "revenue": 0,
            }
        source_breakdown[ts.utm_source]["clicks"] += ts.clicks
        source_breakdown[ts.utm_source]["conversions"] += ts.conversions
        source_breakdown[ts.utm_source]["revenue"] += ts.revenue

    # ROI calculation (simplified - assumes ad spend is tracked elsewhere)
    # For now, show revenue per video and revenue per click
    revenue_per_video = (total_revenue / published_videos / 100) if published_videos > 0 else 0
    revenue_per_click = (total_revenue / total_clicks / 100) if total_clicks > 0 else 0

    return {
        "success": True,
        "campaign_name": campaign_name,
        "summary": {
            "total_videos": total_videos,
            "published_videos": published_videos,
            "total_views": total_views,
            "total_engagement": total_engagement,
            "total_clicks": total_clicks,
            "total_conversions": total_conversions,
            "total_revenue": total_revenue / 100,
            "conversion_rate": (total_conversions / total_clicks * 100) if total_clicks > 0 else 0,
            "avg_order_value": (total_revenue / total_conversions / 100) if total_conversions > 0 else 0,
        },
        "performance": {
            "revenue_per_video": round(revenue_per_video, 2),
            "revenue_per_click": round(revenue_per_click, 2),
            "views_to_click_rate": (total_clicks / total_views * 100) if total_views > 0 else 0,
        },
        "top_videos": top_videos_data,
        "traffic_sources": [
            {
                "source": source,
                "clicks": data["clicks"],
                "conversions": data["conversions"],
                "revenue": data["revenue"] / 100,
            }
            for source, data in source_breakdown.items()
        ],
    }


@router.get("/funnel", response_model=Dict[str, Any])
async def get_conversion_funnel(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    utm_campaign: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get conversion funnel analysis.

    Shows:
    TikTok Views → Clicks → Conversions

    Calculate drop-off rates at each stage.
    """
    # Default to last 30 days
    if not date_from:
        date_from = datetime.utcnow() - timedelta(days=30)
    if not date_to:
        date_to = datetime.utcnow()

    # Query videos
    video_query = db.query(TikTokVideo).filter(
        and_(
            TikTokVideo.user_id == current_user.id,
            TikTokVideo.created_at >= date_from,
            TikTokVideo.created_at <= date_to,
        )
    )

    if utm_campaign:
        video_query = video_query.filter(TikTokVideo.utm_campaign == utm_campaign)

    videos = video_query.all()

    # Query traffic sources
    traffic_query = db.query(TrafficSource).filter(
        and_(
            TrafficSource.user_id == current_user.id,
            TrafficSource.first_click >= date_from,
            TrafficSource.first_click <= date_to,
        )
    )

    if utm_campaign:
        traffic_query = traffic_query.filter(TrafficSource.utm_campaign == utm_campaign)

    traffic_sources = traffic_query.all()

    # Calculate funnel
    total_views = sum(v.views for v in videos)
    total_clicks = sum(ts.clicks for ts in traffic_sources)
    total_conversions = sum(ts.conversions for ts in traffic_sources)

    # Calculate rates
    view_to_click_rate = (total_clicks / total_views * 100) if total_views > 0 else 0
    click_to_conversion_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
    overall_conversion_rate = (total_conversions / total_views * 100) if total_views > 0 else 0

    return {
        "success": True,
        "period": {
            "from": date_from.isoformat(),
            "to": date_to.isoformat(),
        },
        "campaign": utm_campaign,
        "funnel": {
            "views": {
                "count": total_views,
                "percentage": 100,
            },
            "clicks": {
                "count": total_clicks,
                "percentage": view_to_click_rate,
                "drop_off": 100 - view_to_click_rate,
            },
            "conversions": {
                "count": total_conversions,
                "percentage": click_to_conversion_rate,
                "drop_off": 100 - click_to_conversion_rate,
            },
        },
        "overall_conversion_rate": round(overall_conversion_rate, 2),
    }


@router.get("/sources/compare", response_model=Dict[str, Any])
async def compare_traffic_sources(
    sources: List[str] = Query(..., description="List of sources to compare (e.g., tiktok,instagram)"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Compare performance across different traffic sources.

    Example:
    GET /api/v1/analytics/sources/compare?sources=tiktok&sources=instagram
    """
    # Default to last 30 days
    if not date_from:
        date_from = datetime.utcnow() - timedelta(days=30)
    if not date_to:
        date_to = datetime.utcnow()

    comparison = {}

    for source in sources:
        traffic_sources = db.query(TrafficSource).filter(
            and_(
                TrafficSource.user_id == current_user.id,
                TrafficSource.utm_source == source,
                TrafficSource.first_click >= date_from,
                TrafficSource.first_click <= date_to,
            )
        ).all()

        total_clicks = sum(ts.clicks for ts in traffic_sources)
        total_conversions = sum(ts.conversions for ts in traffic_sources)
        total_revenue = sum(ts.revenue for ts in traffic_sources)

        comparison[source] = {
            "clicks": total_clicks,
            "conversions": total_conversions,
            "revenue": total_revenue / 100,
            "conversion_rate": (total_conversions / total_clicks * 100) if total_clicks > 0 else 0,
            "avg_order_value": (total_revenue / total_conversions / 100) if total_conversions > 0 else 0,
        }

    # Find best performer
    best_by_revenue = max(comparison.items(), key=lambda x: x[1]["revenue"]) if comparison else None
    best_by_conversion = max(comparison.items(), key=lambda x: x[1]["conversion_rate"]) if comparison else None

    return {
        "success": True,
        "period": {
            "from": date_from.isoformat(),
            "to": date_to.isoformat(),
        },
        "sources": comparison,
        "best_performers": {
            "revenue": best_by_revenue[0] if best_by_revenue else None,
            "conversion_rate": best_by_conversion[0] if best_by_conversion else None,
        },
    }


@router.get("/time-series", response_model=Dict[str, Any])
async def get_time_series(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    granularity: str = Query("day", regex="^(hour|day|week|month)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get time-series analytics data.

    Granularity options:
    - hour: Hourly breakdown
    - day: Daily breakdown (default)
    - week: Weekly breakdown
    - month: Monthly breakdown
    """
    # Default to last 30 days
    if not date_from:
        date_from = datetime.utcnow() - timedelta(days=30)
    if not date_to:
        date_to = datetime.utcnow()

    # Query traffic sources
    traffic_sources = db.query(TrafficSource).filter(
        and_(
            TrafficSource.user_id == current_user.id,
            TrafficSource.first_click >= date_from,
            TrafficSource.first_click <= date_to,
        )
    ).all()

    # Group by time period
    time_buckets = defaultdict(lambda: {"clicks": 0, "conversions": 0, "revenue": 0})

    for ts in traffic_sources:
        # Format date based on granularity
        if granularity == "hour":
            key = ts.first_click.strftime("%Y-%m-%d %H:00")
        elif granularity == "day":
            key = ts.first_click.strftime("%Y-%m-%d")
        elif granularity == "week":
            # ISO week number
            key = ts.first_click.strftime("%Y-W%U")
        elif granularity == "month":
            key = ts.first_click.strftime("%Y-%m")

        time_buckets[key]["clicks"] += ts.clicks
        time_buckets[key]["conversions"] += ts.conversions
        time_buckets[key]["revenue"] += ts.revenue

    # Format for chart
    time_series = [
        {
            "period": period,
            "clicks": data["clicks"],
            "conversions": data["conversions"],
            "revenue": data["revenue"] / 100,
            "conversion_rate": (data["conversions"] / data["clicks"] * 100) if data["clicks"] > 0 else 0,
        }
        for period, data in sorted(time_buckets.items())
    ]

    return {
        "success": True,
        "period": {
            "from": date_from.isoformat(),
            "to": date_to.isoformat(),
        },
        "granularity": granularity,
        "data": time_series,
    }
