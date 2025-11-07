"""
Landing Page Builder API

Create, preview, and deploy custom landing pages with templates.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
import os
import re

from database.base import get_db
from database.models import LandingPage, TrafficSource
from api.dependencies import get_current_user


router = APIRouter(prefix="/api/v1/landings", tags=["Landing Pages"])

# Jinja2 templates
templates = Jinja2Templates(directory="templates")


# ==================== SCHEMAS ====================

class LandingPageConfig(BaseModel):
    """Landing page configuration."""

    title: Optional[str] = None
    headline: Optional[str] = None
    subheadline: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    favicon: Optional[str] = None
    bg_color: Optional[str] = None
    text_color: Optional[str] = None
    accent_color: Optional[str] = None
    emoji: Optional[str] = None
    redirect_message: Optional[str] = None
    redirect_message_suffix: Optional[str] = None
    custom_css: Optional[str] = None
    custom_js: Optional[str] = None


class LandingCreateRequest(BaseModel):
    """Request to create a landing page."""

    name: str = Field(..., description="Landing page name (internal)")
    template: str = Field(..., description="Template: lootbox, betting, casino, generic, minimal")
    utm_campaign: str = Field(..., description="UTM campaign name")
    utm_source: Optional[str] = "tiktok"
    utm_medium: Optional[str] = "social"

    config: LandingPageConfig = Field(default_factory=LandingPageConfig)

    redirect_delay: int = Field(default=3, description="Seconds before redirect")
    redirect_type: str = Field(default="bot", description="bot, channel, or website")
    redirect_url: Optional[str] = None  # If None, will auto-generate bot URL

    custom_domain: Optional[str] = None


class LandingUpdateRequest(BaseModel):
    """Request to update landing page."""

    name: Optional[str] = None
    config: Optional[LandingPageConfig] = None
    redirect_delay: Optional[int] = None
    redirect_url: Optional[str] = None
    status: Optional[str] = None  # draft, active, paused, archived


class LandingDeployRequest(BaseModel):
    """Request to deploy landing page to domain."""

    landing_id: str
    custom_domain: str = Field(..., description="Domain to deploy to (e.g., lootbox1.com)")


class LandingPageResponse(BaseModel):
    """Response with landing page info."""

    id: str
    name: str
    template: str
    slug: str
    status: str
    is_published: bool
    preview_url: str
    utm_link: str
    custom_domain: Optional[str]
    views: int
    clicks: int
    conversions: int
    created_at: datetime


# ==================== HELPER FUNCTIONS ====================

def generate_slug(name: str) -> str:
    """Generate URL-safe slug from name."""
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9-]', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')

    # Add random suffix to ensure uniqueness
    suffix = str(uuid.uuid4())[:8]
    return f"{slug}-{suffix}"


def validate_template(template: str) -> bool:
    """Validate template exists."""
    valid_templates = ["lootbox", "betting", "casino", "generic", "minimal"]
    return template in valid_templates


# ==================== ENDPOINTS ====================

@router.post("/create", response_model=LandingPageResponse, status_code=status.HTTP_201_CREATED)
def create_landing_page(
    request: LandingCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new landing page.

    **Example:**
    ```json
    {
      "name": "Lootbox Campaign Jan 2025",
      "template": "lootbox",
      "utm_campaign": "lootbox_jan_2025",
      "config": {
        "headline": "🎁 Win $500 from a $5 Lootbox!",
        "subheadline": "Join now and get instant access!",
        "logo_url": "https://i.imgur.com/logo.png",
        "bg_color": "#667eea"
      },
      "redirect_delay": 3
    }
    ```

    **Returns:**
    - `landing_id`: UUID of created landing
    - `preview_url`: URL to preview landing
    - `utm_link`: Full UTM tracking link
    """

    user_id = current_user["user_id"]

    # Validate template
    if not validate_template(request.template):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid template. Valid options: lootbox, betting, casino, generic, minimal"
        )

    # Generate slug
    slug = generate_slug(request.name)

    # Generate redirect URL if not provided
    redirect_url = request.redirect_url
    if not redirect_url:
        bot_username = os.getenv("TELEGRAM_BOT_USERNAME", "your_bot")
        # {utm_id} will be replaced at render time
        redirect_url = f"https://t.me/{bot_username}?start={{utm_id}}"

    # Create landing page
    landing = LandingPage(
        user_id=user_id,
        name=request.name,
        template=request.template,
        slug=slug,
        config=request.config.dict(exclude_none=True),
        utm_campaign=request.utm_campaign,
        utm_source=request.utm_source,
        utm_medium=request.utm_medium,
        redirect_type=request.redirect_type,
        redirect_url=redirect_url,
        redirect_delay=request.redirect_delay,
        custom_domain=request.custom_domain,
        status="draft"
    )

    db.add(landing)
    db.commit()
    db.refresh(landing)

    # Generate URLs
    landing_base_url = os.getenv("LANDING_BASE_URL", "http://localhost:8000")
    preview_url = f"{landing_base_url}/landings/preview/{landing.id}"
    utm_link = f"{landing_base_url}/l/{landing.slug}"

    return LandingPageResponse(
        id=str(landing.id),
        name=landing.name,
        template=landing.template,
        slug=landing.slug,
        status=landing.status,
        is_published=landing.is_published,
        preview_url=preview_url,
        utm_link=utm_link,
        custom_domain=landing.custom_domain,
        views=landing.views,
        clicks=landing.clicks,
        conversions=landing.conversions,
        created_at=landing.created_at
    )


@router.get("/preview/{landing_id}", response_class=HTMLResponse)
def preview_landing_page(
    landing_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Preview landing page (without tracking).

    **Use this to see how landing page looks before publishing.**
    """

    landing = db.query(LandingPage).filter(LandingPage.id == landing_id).first()

    if not landing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Landing page not found"
        )

    # Prepare template context
    context = {
        "request": request,
        "config": landing.config,
        "utm_id": "preview",
        "redirect_url": landing.redirect_url.replace("{utm_id}", "preview"),
        "redirect_delay": landing.redirect_delay
    }

    # Render template
    template_name = f"landings/{landing.template}.html"
    return templates.TemplateResponse(template_name, context)


@router.get("/{slug_or_id}", response_class=HTMLResponse)
def render_landing_page(
    slug_or_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Render landing page (with tracking).

    This is the public-facing endpoint that users hit.
    Tracks the visit and redirects to Telegram.
    """

    # Try to find by slug first, then by ID
    landing = db.query(LandingPage).filter(
        (LandingPage.slug == slug_or_id) | (LandingPage.id == slug_or_id)
    ).first()

    if not landing or landing.status != "active":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Landing page not found or not active"
        )

    # Generate UTM ID for tracking
    utm_id = f"{landing.utm_source}_{str(uuid.uuid4())[:8]}"

    # Track traffic source
    from utils.geoip import get_geoip

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")

    geoip = get_geoip()
    country, city = geoip.lookup(client_ip) if client_ip else (None, None)

    # Create traffic source record
    traffic_source = TrafficSource(
        user_id=landing.user_id,
        utm_source=landing.utm_source,
        utm_medium=landing.utm_medium,
        utm_campaign=landing.utm_campaign,
        utm_id=utm_id,
        landing_page=request.url.path,
        referrer=request.headers.get("referer"),
        ip_address=client_ip,
        user_agent=user_agent,
        country=country,
        city=city
    )

    db.add(traffic_source)

    # Update landing page stats
    landing.views += 1
    landing.last_view_at = datetime.utcnow()

    db.commit()

    # Prepare redirect URL with utm_id
    redirect_url = landing.redirect_url.replace("{utm_id}", utm_id)

    # Prepare template context
    context = {
        "request": request,
        "config": landing.config,
        "utm_id": utm_id,
        "redirect_url": redirect_url,
        "redirect_delay": landing.redirect_delay
    }

    # Render template
    template_name = f"landings/{landing.template}.html"
    return templates.TemplateResponse(template_name, context)


@router.put("/{landing_id}")
def update_landing_page(
    landing_id: str,
    request: LandingUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update landing page configuration.

    **Example:**
    ```json
    {
      "config": {
        "headline": "NEW HEADLINE!",
        "bg_color": "#FF0000"
      },
      "status": "active"
    }
    ```
    """

    user_id = current_user["user_id"]

    landing = db.query(LandingPage).filter(
        LandingPage.id == landing_id,
        LandingPage.user_id == user_id
    ).first()

    if not landing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Landing page not found"
        )

    # Update fields
    if request.name:
        landing.name = request.name

    if request.config:
        # Merge with existing config
        current_config = landing.config or {}
        new_config = request.config.dict(exclude_none=True)
        current_config.update(new_config)
        landing.config = current_config

    if request.redirect_delay is not None:
        landing.redirect_delay = request.redirect_delay

    if request.redirect_url:
        landing.redirect_url = request.redirect_url

    if request.status:
        landing.status = request.status

        if request.status == "active" and not landing.is_published:
            landing.is_published = True
            landing.published_at = datetime.utcnow()

    landing.updated_at = datetime.utcnow()

    db.commit()

    return {"message": "Landing page updated successfully"}


@router.get("/")
def list_landing_pages(
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List all landing pages for current user.

    **Filters:**
    - status: draft, active, paused, archived
    """

    user_id = current_user["user_id"]

    query = db.query(LandingPage).filter(LandingPage.user_id == user_id)

    if status:
        query = query.filter(LandingPage.status == status)

    landings = query.order_by(LandingPage.created_at.desc()).limit(limit).all()

    landing_base_url = os.getenv("LANDING_BASE_URL", "http://localhost:8000")

    return {
        "landings": [
            {
                "id": str(l.id),
                "name": l.name,
                "template": l.template,
                "slug": l.slug,
                "status": l.status,
                "is_published": l.is_published,
                "preview_url": f"{landing_base_url}/landings/preview/{l.id}",
                "utm_link": f"{landing_base_url}/l/{l.slug}",
                "custom_domain": l.custom_domain,
                "views": l.views,
                "clicks": l.clicks,
                "conversions": l.conversions,
                "created_at": l.created_at.isoformat()
            }
            for l in landings
        ]
    }


@router.delete("/{landing_id}")
def delete_landing_page(
    landing_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete landing page."""

    user_id = current_user["user_id"]

    landing = db.query(LandingPage).filter(
        LandingPage.id == landing_id,
        LandingPage.user_id == user_id
    ).first()

    if not landing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Landing page not found"
        )

    db.delete(landing)
    db.commit()

    return {"message": "Landing page deleted successfully"}


@router.post("/deploy")
def deploy_landing_to_domain(
    request: LandingDeployRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Deploy landing page to custom domain.

    **Note:** This endpoint prepares the landing for deployment.
    You still need to:
    1. Point DNS to your server
    2. Run deploy script to configure Nginx
    3. Run certbot for SSL

    See docs/DEPLOYMENT.md for full guide.
    """

    user_id = current_user["user_id"]

    landing = db.query(LandingPage).filter(
        LandingPage.id == request.landing_id,
        LandingPage.user_id == user_id
    ).first()

    if not landing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Landing page not found"
        )

    # Update domain
    landing.custom_domain = request.custom_domain
    landing.is_domain_verified = False  # Will be verified after DNS setup

    db.commit()

    return {
        "message": "Landing page prepared for deployment",
        "next_steps": [
            f"1. Point DNS A record for {request.custom_domain} to your server IP",
            "2. Run: bash deploy/deploy-domain.sh to configure Nginx",
            "3. SSL will be configured automatically via certbot"
        ],
        "custom_domain": request.custom_domain
    }
