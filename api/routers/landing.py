"""
Landing page router for TikTok → Telegram funnel.
Displays intermediate page with auto-redirect and click tracking.
"""

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import os

from database.base import get_db
from database.models import TrafficSource
from utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()


def get_landing_page_html(
    telegram_link: str,
    utm_id: str,
    channel_name: str = "Sports Hub",
    channel_description: str = "Your daily dose of sports highlights & discussions",
) -> str:
    """
    Generate landing page HTML with branding and auto-redirect.

    Features:
    - Beautiful gradient background
    - Feature highlights
    - Stats (members, daily posts, etc.)
    - Auto-redirect after 3 seconds
    - JavaScript time tracking
    """
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{channel_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            padding: 20px;
            overflow-x: hidden;
        }}

        .container {{
            max-width: 550px;
            width: 100%;
            text-align: center;
            animation: fadeIn 0.6s ease;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(30px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .logo {{
            font-size: 4em;
            margin-bottom: 10px;
            animation: bounce 2s infinite;
        }}

        @keyframes bounce {{
            0%, 100% {{ transform: translateY(0); }}
            50% {{ transform: translateY(-10px); }}
        }}

        h1 {{
            font-size: 2.5em;
            margin-bottom: 15px;
            text-shadow: 2px 2px 8px rgba(0,0,0,0.3);
            font-weight: 700;
        }}

        .subtitle {{
            font-size: 1.2em;
            margin-bottom: 30px;
            opacity: 0.95;
            line-height: 1.5;
        }}

        .features {{
            background: rgba(255,255,255,0.15);
            border-radius: 25px;
            padding: 30px;
            margin: 30px 0;
            backdrop-filter: blur(15px);
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
        }}

        .features h3 {{
            margin-bottom: 25px;
            font-size: 1.4em;
            font-weight: 600;
        }}

        .feature-item {{
            display: flex;
            align-items: center;
            margin: 20px 0;
            font-size: 1.05em;
            text-align: left;
        }}

        .feature-icon {{
            font-size: 2em;
            margin-right: 20px;
            min-width: 50px;
            text-align: center;
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin: 40px 0;
        }}

        .stat {{
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }}

        .stat-number {{
            font-size: 2.2em;
            font-weight: 700;
            margin-bottom: 5px;
        }}

        .stat-label {{
            opacity: 0.9;
            font-size: 0.9em;
        }}

        .btn {{
            display: inline-block;
            background: white;
            color: #764ba2;
            padding: 20px 60px;
            border-radius: 50px;
            text-decoration: none;
            font-size: 1.4em;
            font-weight: 700;
            margin-top: 20px;
            transition: all 0.3s ease;
            box-shadow: 0 10px 35px rgba(0,0,0,0.3);
            border: none;
            cursor: pointer;
        }}

        .btn:hover {{
            transform: translateY(-5px) scale(1.02);
            box-shadow: 0 15px 45px rgba(0,0,0,0.4);
        }}

        .btn:active {{
            transform: translateY(-2px) scale(0.98);
        }}

        .redirect-notice {{
            margin-top: 35px;
            font-size: 0.95em;
            opacity: 0.8;
        }}

        .loading {{
            display: inline-block;
            width: 22px;
            height: 22px;
            border: 3px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s linear infinite;
            margin-right: 10px;
            vertical-align: middle;
        }}

        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}

        .trust-badges {{
            margin-top: 30px;
            display: flex;
            justify-content: center;
            gap: 25px;
            opacity: 0.8;
            font-size: 0.9em;
        }}

        .badge {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        @media (max-width: 600px) {{
            h1 {{ font-size: 2em; }}
            .logo {{ font-size: 3em; }}
            .stats {{ grid-template-columns: 1fr; gap: 15px; }}
            .btn {{ padding: 18px 45px; font-size: 1.2em; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">⚽</div>
        <h1>{channel_name}</h1>
        <p class="subtitle">{channel_description}</p>

        <div class="features">
            <h3>What you'll get:</h3>
            <div class="feature-item">
                <span class="feature-icon">🎥</span>
                <span>Daily match highlights & best moments</span>
            </div>
            <div class="feature-item">
                <span class="feature-icon">💬</span>
                <span>Active community of sports fans</span>
            </div>
            <div class="feature-item">
                <span class="feature-icon">📊</span>
                <span>Match analysis & expert predictions</span>
            </div>
            <div class="feature-item">
                <span class="feature-icon">🏆</span>
                <span>Exclusive content & insider news</span>
            </div>
        </div>

        <div class="stats">
            <div class="stat">
                <div class="stat-number">50K+</div>
                <div class="stat-label">Members</div>
            </div>
            <div class="stat">
                <div class="stat-number">100+</div>
                <div class="stat-label">Daily Posts</div>
            </div>
            <div class="stat">
                <div class="stat-number">24/7</div>
                <div class="stat-label">Active Chat</div>
            </div>
        </div>

        <a href="{telegram_link}" class="btn" id="joinBtn">
            Join Telegram Channel
        </a>

        <div class="trust-badges">
            <div class="badge">
                <span>✓</span>
                <span>100% Free</span>
            </div>
            <div class="badge">
                <span>✓</span>
                <span>Instant Access</span>
            </div>
            <div class="badge">
                <span>✓</span>
                <span>No Spam</span>
            </div>
        </div>

        <div class="redirect-notice">
            <div class="loading"></div>
            <span>Redirecting to Telegram...</span>
        </div>
    </div>

    <script>
        // Track time on page
        const startTime = Date.now();
        const utmId = '{utm_id}';

        // Auto redirect after 3 seconds
        setTimeout(() => {{
            window.location.href = "{telegram_link}";
        }}, 3000);

        // Track when user leaves
        window.addEventListener('beforeunload', () => {{
            const timeSpent = Math.floor((Date.now() - startTime) / 1000);

            // Send time spent to analytics
            const data = {{
                utm_id: utmId,
                time_spent: timeSpent
            }};

            // Use sendBeacon for reliability (works even when page is closing)
            if (navigator.sendBeacon) {{
                const blob = new Blob([JSON.stringify(data)], {{ type: 'application/json' }});
                navigator.sendBeacon('/api/v1/landing/track-time', blob);
            }}
        }});

        // Track button click
        document.getElementById('joinBtn').addEventListener('click', (e) => {{
            // Let default action proceed (opens Telegram)
            // Just track that user clicked manually (vs auto-redirect)
            fetch('/api/v1/landing/track-click', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ utm_id: utmId, manual_click: true }})
            }}).catch(() => {{}});
        }});
    </script>
</body>
</html>
"""


@router.get("/l/{utm_id}", response_class=HTMLResponse)
async def landing_page(
    utm_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Landing page with auto-redirect to Telegram.

    URL format: /api/v1/landing/l/{utm_id}

    This page:
    1. Shows beautiful landing with channel info
    2. Auto-redirects to Telegram after 3 seconds
    3. Tracks the visit via JavaScript
    4. Collects time spent on page
    """
    # Find traffic source
    traffic_source = db.query(TrafficSource).filter(
        TrafficSource.utm_id == utm_id
    ).first()

    if not traffic_source:
        # If UTM ID not found, redirect directly to a default channel
        logger.warning(f"Landing page accessed with invalid UTM ID: {utm_id}")
        return RedirectResponse("https://t.me/sportschannel")

    # Build Telegram link with utm_id preserved
    # Option 1: Direct to bot (recommended - preserves utm_id)
    # Option 2: To channel (loses utm_id unless you add inline button)

    redirect_type = os.getenv("LANDING_REDIRECT_TYPE", "bot")  # "bot" or "channel"

    if redirect_type == "bot":
        # Direct to bot with utm_id in /start parameter
        bot_username = os.getenv("TELEGRAM_BOT_USERNAME", "your_bot")
        telegram_link = f"https://t.me/{bot_username}?start={utm_id}"
    else:
        # To channel (utm_id will be lost unless channel has button to bot)
        telegram_link = os.getenv("DEFAULT_TELEGRAM_CHANNEL", "https://t.me/sportschannel")

    # Get channel/bot info from config or database
    channel_name = os.getenv("CHANNEL_NAME", "Sports Hub")
    channel_description = os.getenv("CHANNEL_DESCRIPTION", "Daily sports highlights & discussions")

    # Generate HTML
    html = get_landing_page_html(
        telegram_link=telegram_link,
        utm_id=utm_id,
        channel_name=channel_name,
        channel_description=channel_description,
    )

    # Track the landing page view (initial visit)
    # This happens server-side before page loads
    try:
        # Parse user agent
        user_agent = request.headers.get("User-Agent", "")
        ip_address = (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or request.headers.get("X-Real-IP", "")
            or request.client.host
        )

        # Update traffic source
        traffic_source.clicks += 1
        traffic_source.last_click = datetime.utcnow()
        traffic_source.landing_page = str(request.url)
        traffic_source.referrer = request.headers.get("Referer", "")

        if traffic_source.clicks == 1:
            # First click - save metadata
            traffic_source.ip_address = ip_address
            traffic_source.user_agent = user_agent

        db.commit()

        logger.info(f"Landing page view: {utm_id} (click #{traffic_source.clicks})")

    except Exception as e:
        logger.error(f"Error tracking landing page view: {e}")
        # Don't fail the request if tracking fails

    return HTMLResponse(content=html)


@router.post("/track-time")
async def track_time_spent(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Track time spent on landing page.
    Called via JavaScript beacon when user leaves page.
    """
    try:
        data = await request.json()
        utm_id = data.get("utm_id")
        time_spent = data.get("time_spent", 0)

        if utm_id:
            traffic_source = db.query(TrafficSource).filter(
                TrafficSource.utm_id == utm_id
            ).first()

            if traffic_source:
                # Update time spent (average if multiple visits)
                if traffic_source.time_spent > 0:
                    traffic_source.time_spent = (traffic_source.time_spent + time_spent) // 2
                else:
                    traffic_source.time_spent = time_spent

                db.commit()

                logger.info(f"Time tracked: {utm_id} spent {time_spent}s on landing page")

        return {"success": True}

    except Exception as e:
        logger.error(f"Error tracking time: {e}")
        return {"success": False}


@router.post("/track-click")
async def track_manual_click(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Track manual button click (vs auto-redirect).
    Useful for A/B testing CTA effectiveness.
    """
    try:
        data = await request.json()
        utm_id = data.get("utm_id")
        manual_click = data.get("manual_click", False)

        if utm_id and manual_click:
            # Could store this in a separate field or metadata
            # For now, just log it
            logger.info(f"Manual click: {utm_id}")

        return {"success": True}

    except Exception as e:
        logger.error(f"Error tracking manual click: {e}")
        return {"success": False}


@router.get("/preview")
async def preview_landing_page():
    """
    Preview landing page without UTM tracking.
    Useful for testing design.
    """
    html = get_landing_page_html(
        telegram_link="https://t.me/sportschannel",
        utm_id="preview",
        channel_name="Sports Hub Preview",
        channel_description="This is a preview of your landing page",
    )

    return HTMLResponse(content=html)
