"""
UTM tracking router for traffic source attribution.
Generates UTM links and tracks clicks/conversions.
"""

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime
import uuid
import hashlib

from database.base import get_db
from database.models import TrafficSource, Conversion, User
from database.schemas import (
    UTMGenerateRequest,
    UTMGenerateResponse,
    TrackClickRequest,
    TrackClickResponse,
    ConversionCreate,
    ConversionResponse,
    TrafficSourceResponse,
    WebhookConversion,
)
from api.dependencies import get_current_user
from utils.logger import setup_logger
from utils.geoip import get_location_from_ip

logger = setup_logger(__name__)
router = APIRouter()


def generate_utm_id(source: str, campaign: Optional[str], content: Optional[str]) -> str:
    """
    Generate unique UTM ID.

    Format: {source}_{campaign_hash}_{random}
    Example: tiktok_a7b3c_8f2e1
    """
    parts = [source]

    if campaign:
        # Hash campaign name to 5 chars
        campaign_hash = hashlib.md5(campaign.encode()).hexdigest()[:5]
        parts.append(campaign_hash)

    # Add random component
    random_id = uuid.uuid4().hex[:5]
    parts.append(random_id)

    return "_".join(parts)


def parse_user_agent(user_agent: str) -> dict:
    """
    Parse user agent to extract device type, browser, OS.
    Simple implementation - in production use a library like user-agents.
    """
    ua_lower = user_agent.lower()

    # Device type
    if "mobile" in ua_lower or "android" in ua_lower or "iphone" in ua_lower:
        device_type = "mobile"
    elif "tablet" in ua_lower or "ipad" in ua_lower:
        device_type = "tablet"
    else:
        device_type = "desktop"

    # Browser
    if "chrome" in ua_lower:
        browser = "Chrome"
    elif "safari" in ua_lower:
        browser = "Safari"
    elif "firefox" in ua_lower:
        browser = "Firefox"
    elif "edge" in ua_lower:
        browser = "Edge"
    else:
        browser = "Other"

    # OS
    if "windows" in ua_lower:
        os = "Windows"
    elif "mac" in ua_lower or "ios" in ua_lower:
        os = "macOS/iOS"
    elif "android" in ua_lower:
        os = "Android"
    elif "linux" in ua_lower:
        os = "Linux"
    else:
        os = "Other"

    return {
        "device_type": device_type,
        "browser": browser,
        "os": os,
    }


@router.post("/generate", response_model=UTMGenerateResponse)
async def generate_utm_link(
    request: UTMGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate UTM tracking link.

    Supports two link types:
    1. 'landing' - Short link to landing page (yourdomain.com/l/{utm_id})
    2. 'direct' - Direct Telegram link with UTM parameters (t.me/bot?start={utm_id})

    Example:
    ```
    POST /api/v1/utm/generate
    {
        "base_url": "https://t.me/sportschannel",
        "source": "tiktok",
        "campaign": "football_jan_2025",
        "content": "video_123",
        "link_type": "landing"
    }
    ```

    Returns:
    ```
    {
        "success": true,
        "utm_link": "https://yourdomain.com/l/tiktok_a7b3c_8f2e1",
        "utm_id": "tiktok_a7b3c_8f2e1",
        "link_type": "landing"
    }
    ```
    """
    # Generate unique UTM ID
    utm_id = generate_utm_id(request.source, request.campaign, request.content)

    # Determine link type and generate appropriate URL
    if request.link_type == "landing":
        # Landing page link (will redirect to base_url after tracking)
        import os
        landing_base_url = os.getenv("LANDING_BASE_URL", "http://localhost:8000/api/v1/landing/l")
        utm_link = f"{landing_base_url}/{utm_id}"

    elif request.link_type == "direct":
        # Direct Telegram link with /start parameter
        # For bots: t.me/your_bot?start={utm_id}
        # For channels with description: base_url with utm params
        if "t.me" in request.base_url and "@" not in request.base_url:
            # It's a bot link
            separator = "?start=" if "/start" not in request.base_url else "&start="
            utm_link = f"{request.base_url.split('?')[0]}{separator}{utm_id}"
        else:
            # Regular URL with UTM parameters
            utm_params = [
                f"utm_source={request.source}",
                f"utm_medium={request.medium}",
            ]
            if request.campaign:
                utm_params.append(f"utm_campaign={request.campaign}")
            if request.content:
                utm_params.append(f"utm_content={request.content}")
            if request.term:
                utm_params.append(f"utm_term={request.term}")
            utm_params.append(f"utm_id={utm_id}")

            separator = "&" if "?" in request.base_url else "?"
            utm_link = f"{request.base_url}{separator}{'&'.join(utm_params)}"
    else:
        raise HTTPException(status_code=400, detail=f"Invalid link_type: {request.link_type}. Use 'landing' or 'direct'")

    # Create traffic source record (pre-create for this utm_id)
    traffic_source = TrafficSource(
        user_id=current_user.id,
        utm_source=request.source,
        utm_medium=request.medium,
        utm_campaign=request.campaign,
        utm_content=request.content,
        utm_term=request.term,
        utm_id=utm_id,
        clicks=0,  # Will be incremented on first click
        landing_page=request.base_url if request.link_type == "landing" else None,
        referrer=f"{request.link_type}_link",  # Track link type
    )

    db.add(traffic_source)
    db.commit()

    logger.info(f"Generated {request.link_type} UTM link: {utm_id} for user {current_user.email}")

    return UTMGenerateResponse(
        success=True,
        utm_link=utm_link,
        utm_id=utm_id,
        link_type=request.link_type,
    )


@router.post("/track/click", response_model=TrackClickResponse)
async def track_click(
    request: TrackClickRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    """
    Track a click on UTM link.

    Called when user clicks on a TikTok link and lands on your page.
    This is typically called from your landing page JavaScript.

    Example:
    ```
    POST /api/v1/utm/track/click
    {
        "utm_id": "tiktok_a7b3c_8f2e1",
        "landing_page": "https://yourdomain.com/landing",
        "referrer": "https://tiktok.com"
    }
    ```
    """
    # Find traffic source by utm_id
    traffic_source = db.query(TrafficSource).filter(
        TrafficSource.utm_id == request.utm_id
    ).first()

    if not traffic_source:
        raise HTTPException(status_code=404, detail="UTM ID not found")

    # Parse user agent
    user_agent = http_request.headers.get("User-Agent", "")
    ua_info = parse_user_agent(user_agent)

    # Get IP address (handle proxy headers)
    ip_address = (
        http_request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or http_request.headers.get("X-Real-IP", "")
        or http_request.client.host
    )

    # Update traffic source
    traffic_source.clicks += 1
    traffic_source.last_click = datetime.utcnow()

    # Update metadata if first click
    if traffic_source.clicks == 1:
        traffic_source.ip_address = ip_address
        traffic_source.user_agent = user_agent
        traffic_source.device_type = ua_info["device_type"]
        traffic_source.browser = ua_info["browser"]
        traffic_source.os = ua_info["os"]

        # GeoIP lookup for country and city
        country, city = get_location_from_ip(ip_address)
        if country:
            traffic_source.country = country
            traffic_source.city = city

    if request.landing_page:
        traffic_source.landing_page = request.landing_page
    if request.referrer:
        traffic_source.referrer = request.referrer

    db.commit()

    logger.info(f"Click tracked: {request.utm_id} (total: {traffic_source.clicks})")

    return TrackClickResponse(
        success=True,
        tracking_id=str(traffic_source.id),
        message=f"Click #{traffic_source.clicks} tracked successfully",
    )


@router.post("/track/conversion", response_model=ConversionResponse)
async def track_conversion(
    request: ConversionCreate,
    db: Session = Depends(get_db),
):
    """
    Track a conversion (lootbox purchase).

    Called from your lootbox system when a user makes a purchase.
    Uses webhook or direct API call.

    Example:
    ```
    POST /api/v1/utm/track/conversion
    {
        "traffic_source_id": "uuid-here",
        "conversion_type": "purchase",
        "amount": 5000,  // $50.00 in cents
        "currency": "USD",
        "product_id": "lootbox_gold",
        "product_name": "Gold Lootbox",
        "customer_id": "customer_123",
        "metadata": {
            "payment_method": "stripe",
            "transaction_id": "txn_abc123"
        }
    }
    ```
    """
    # Find traffic source
    traffic_source = db.query(TrafficSource).filter(
        TrafficSource.id == request.traffic_source_id
    ).first()

    if not traffic_source:
        raise HTTPException(status_code=404, detail="Traffic source not found")

    # Calculate time to conversion
    time_to_conversion = int((datetime.utcnow() - traffic_source.first_click).total_seconds())

    # Create conversion record
    conversion = Conversion(
        traffic_source_id=request.traffic_source_id,
        user_id=traffic_source.user_id,
        conversion_type=request.conversion_type,
        customer_id=request.customer_id,
        amount=request.amount,
        currency=request.currency,
        product_id=request.product_id,
        product_name=request.product_name,
        time_to_conversion=time_to_conversion,
        metadata=request.metadata or {},
    )

    db.add(conversion)

    # Update traffic source conversion stats
    traffic_source.conversions += 1
    traffic_source.revenue += request.amount

    db.commit()
    db.refresh(conversion)

    logger.info(
        f"Conversion tracked: {request.conversion_type} "
        f"${request.amount/100:.2f} for {traffic_source.utm_id}"
    )

    return ConversionResponse(
        id=conversion.id,
        traffic_source_id=conversion.traffic_source_id,
        user_id=conversion.user_id,
        conversion_type=conversion.conversion_type,
        customer_id=conversion.customer_id,
        amount=conversion.amount,
        currency=conversion.currency,
        product_id=conversion.product_id,
        product_name=conversion.product_name,
        time_to_conversion=conversion.time_to_conversion,
        metadata=conversion.metadata,
        created_at=conversion.created_at,
    )


@router.get("/sources", response_model=list[TrafficSourceResponse])
async def list_traffic_sources(
    skip: int = 0,
    limit: int = 100,
    utm_source: Optional[str] = None,
    utm_campaign: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all traffic sources for current user.

    Optional filters:
    - utm_source: Filter by source (tiktok, instagram, etc.)
    - utm_campaign: Filter by campaign name
    """
    query = db.query(TrafficSource).filter(TrafficSource.user_id == current_user.id)

    if utm_source:
        query = query.filter(TrafficSource.utm_source == utm_source)
    if utm_campaign:
        query = query.filter(TrafficSource.utm_campaign == utm_campaign)

    traffic_sources = query.order_by(TrafficSource.created_at.desc()).offset(skip).limit(limit).all()

    return traffic_sources


@router.get("/sources/{utm_id}", response_model=TrafficSourceResponse)
async def get_traffic_source(
    utm_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get specific traffic source by UTM ID.
    """
    traffic_source = db.query(TrafficSource).filter(
        TrafficSource.utm_id == utm_id,
        TrafficSource.user_id == current_user.id,
    ).first()

    if not traffic_source:
        raise HTTPException(status_code=404, detail="Traffic source not found")

    return traffic_source


@router.get("/conversions", response_model=list[ConversionResponse])
async def list_conversions(
    skip: int = 0,
    limit: int = 100,
    conversion_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all conversions for current user.

    Optional filters:
    - conversion_type: Filter by type (purchase, signup, etc.)
    """
    query = db.query(Conversion).filter(Conversion.user_id == current_user.id)

    if conversion_type:
        query = query.filter(Conversion.conversion_type == conversion_type)

    conversions = query.order_by(Conversion.created_at.desc()).offset(skip).limit(limit).all()

    return conversions


@router.post("/webhook/conversion", response_model=ConversionResponse)
async def webhook_track_conversion(
    request: WebhookConversion,
    db: Session = Depends(get_db),
):
    """
    Webhook endpoint for tracking conversions from external systems.

    This endpoint is designed for easy integration with User Bots.
    No authentication required - uses utm_id to find traffic source.

    Example from Telegram Bot:
    ```python
    import requests

    # When user makes purchase
    requests.post("https://your-api.com/api/v1/utm/webhook/conversion", json={
        "utm_id": "tiktok_a7b3c_8f2e1",  # from /start parameter
        "customer_id": f"telegram_{user_id}",
        "amount": 5000,  # $50.00
        "product_name": "Gold Lootbox"
    })
    ```
    """
    # Find traffic source by utm_id
    traffic_source = db.query(TrafficSource).filter(
        TrafficSource.utm_id == request.utm_id
    ).first()

    if not traffic_source:
        raise HTTPException(status_code=404, detail=f"UTM ID not found: {request.utm_id}")

    # Calculate time to conversion
    time_to_conversion = int((datetime.utcnow() - traffic_source.first_click).total_seconds())

    # Create conversion record
    conversion = Conversion(
        traffic_source_id=traffic_source.id,
        user_id=traffic_source.user_id,
        conversion_type=request.conversion_type,
        customer_id=request.customer_id,
        amount=request.amount,
        currency=request.currency,
        product_id=request.product_id,
        product_name=request.product_name,
        time_to_conversion=time_to_conversion,
        metadata=request.metadata or {},
    )

    db.add(conversion)

    # Update traffic source conversion stats
    traffic_source.conversions += 1
    traffic_source.revenue += request.amount

    db.commit()
    db.refresh(conversion)

    logger.info(
        f"Webhook conversion tracked: {request.conversion_type} "
        f"${request.amount/100:.2f} for {request.utm_id} (customer: {request.customer_id})"
    )

    return ConversionResponse(
        id=conversion.id,
        traffic_source_id=conversion.traffic_source_id,
        user_id=conversion.user_id,
        conversion_type=conversion.conversion_type,
        customer_id=conversion.customer_id,
        amount=conversion.amount,
        currency=conversion.currency,
        product_id=conversion.product_id,
        product_name=conversion.product_name,
        time_to_conversion=conversion.time_to_conversion,
        metadata=conversion.metadata,
        created_at=conversion.created_at,
    )
