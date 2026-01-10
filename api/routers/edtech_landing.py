"""
EdTech Landing Page Router - для тестирования креативов через micro-influencers.

Флоу:
1. User кликает по ссылке инфлюенсера: /?utm_id=inf_creator_abc123
2. Landing page:
   - Извлекает UTM параметры
   - Инициализирует RudderStack (anonymousId persistence)
   - Отправляет Page Viewed event
3. User покупает курс:
   - Форма checkout
   - Отправляет Order Completed event
   - Redirect на success page

Attribution: RudderStack anonymousId связывает Page Viewed и Order Completed.
"""

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

from database.base import get_db
from database.models import TrafficSource, Conversion, UserSession
from utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter(prefix="/edtech", tags=["EdTech Landing"])


class CheckoutRequest(BaseModel):
    """Checkout form data"""
    email: str
    name: str
    utm_id: Optional[str] = None
    anonymous_id: str  # RudderStack anonymousId


def get_edtech_landing_html(
    course_name: str = "Master Python in 30 Days",
    price: float = 49.00,
    instructor: str = "Alex Rodriguez",
    students: int = 12453,
    rating: float = 4.8,
    pain_point: str = "no_time",  # EdTech pain point
    rudderstack_write_key: str = None,
    rudderstack_data_plane_url: str = None
) -> str:
    """
    Generate EdTech landing page HTML with RudderStack integration.

    Features:
    - RudderStack SDK (anonymousId persistence)
    - UTM parameter extraction
    - Page Viewed tracking
    - Checkout form with Order Completed event
    - Mobile-responsive design
    - Pain point-focused copy
    """

    # Pain point messaging
    pain_messages = {
        "no_time": {
            "headline": "Learn Python in Just 15 Minutes a Day",
            "subheadline": "Busy schedule? No problem. Master coding without sacrificing your free time.",
            "benefit": "⏰ Bite-sized lessons that fit your schedule"
        },
        "too_expensive": {
            "headline": "Professional Python Course for Just $49",
            "subheadline": "Why pay $500+ when you can get the same results for 10x less?",
            "benefit": "💰 Same quality, fraction of the price"
        },
        "fear_failure": {
            "headline": "95% of Our Students Get Their First Dev Job",
            "subheadline": "Stop worrying about failure. Our proven method works even for complete beginners.",
            "benefit": "✅ Step-by-step guidance from zero to hired"
        },
        "no_progress": {
            "headline": "See Real Results in Your First Week",
            "subheadline": "Tired of courses where you don't see progress? Build your first app in 7 days.",
            "benefit": "🚀 Ship real projects, not just watch videos"
        },
        "need_career_switch": {
            "headline": "From Teacher to Developer in 6 Months",
            "subheadline": "Switching careers? Join 1,200+ professionals who made the leap with us.",
            "benefit": "💼 Career-focused curriculum with job placement support"
        },
        "imposter_syndrome": {
            "headline": "No Coding Experience? Start Here.",
            "subheadline": "Everyone feels like an imposter at first. Our beginner-friendly approach makes it easy.",
            "benefit": "🎯 Built for absolute beginners"
        },
        "info_overload": {
            "headline": "Only What You Need to Get Hired",
            "subheadline": "Cut through the noise. Learn exactly what employers want, nothing more.",
            "benefit": "🎓 Curated curriculum, zero fluff"
        }
    }

    messaging = pain_messages.get(pain_point, pain_messages["no_time"])

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{course_name} - {messaging['headline']}</title>

    <!-- RudderStack SDK -->
    <script>
    rudderanalytics=window.rudderanalytics=[];for(var methods=["load","page","track","identify","alias","group","ready","reset","getAnonymousId","setAnonymousId"],i=0;i<methods.length;i++){{var method=methods[i];rudderanalytics[method]=function(a){{return function(){{rudderanalytics.push([a].concat(Array.prototype.slice.call(arguments)))}}}}(method)}}
    </script>
    <script src="https://cdn.rudderlabs.com/v1.1/rudder-analytics.min.js"></script>

    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            line-height: 1.6;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}

        /* Hero Section */
        .hero {{
            background: white;
            border-radius: 20px;
            padding: 60px 40px;
            margin: 40px 0;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            text-align: center;
        }}

        .hero h1 {{
            font-size: 3em;
            color: #667eea;
            margin-bottom: 20px;
            font-weight: 800;
        }}

        .hero .subheadline {{
            font-size: 1.5em;
            color: #666;
            margin-bottom: 30px;
        }}

        .trust-badge {{
            display: inline-flex;
            align-items: center;
            gap: 10px;
            background: #f0f4ff;
            padding: 15px 25px;
            border-radius: 10px;
            margin: 20px 10px;
            font-weight: 600;
        }}

        .rating {{
            color: #ffc107;
            font-size: 1.2em;
        }}

        /* Benefits Section */
        .benefits {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin: 40px 0;
        }}

        .benefit-card {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }}

        .benefit-card h3 {{
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.5em;
        }}

        /* Pricing Section */
        .pricing {{
            background: white;
            border-radius: 20px;
            padding: 50px;
            margin: 40px 0;
            text-align: center;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}

        .price {{
            font-size: 4em;
            color: #667eea;
            font-weight: 800;
            margin: 20px 0;
        }}

        .price-old {{
            text-decoration: line-through;
            color: #999;
            font-size: 0.4em;
            display: block;
        }}

        /* Checkout Form */
        .checkout-form {{
            max-width: 500px;
            margin: 30px auto;
        }}

        .form-group {{
            margin-bottom: 20px;
        }}

        .form-group label {{
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #333;
        }}

        .form-group input {{
            width: 100%;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 1em;
            transition: border-color 0.3s;
        }}

        .form-group input:focus {{
            outline: none;
            border-color: #667eea;
        }}

        .btn-primary {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 60px;
            border: none;
            border-radius: 50px;
            font-size: 1.3em;
            font-weight: 700;
            cursor: pointer;
            width: 100%;
            transition: all 0.3s;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        }}

        .btn-primary:hover {{
            transform: translateY(-3px);
            box-shadow: 0 15px 40px rgba(102, 126, 234, 0.6);
        }}

        .btn-primary:active {{
            transform: translateY(-1px);
        }}

        /* Urgency Timer */
        .urgency {{
            background: #ff6b6b;
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            text-align: center;
            font-weight: 600;
        }}

        /* Mobile Responsive */
        @media (max-width: 768px) {{
            .hero h1 {{ font-size: 2em; }}
            .hero .subheadline {{ font-size: 1.2em; }}
            .price {{ font-size: 3em; }}
            .pricing {{ padding: 30px 20px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Hero Section -->
        <div class="hero">
            <h1>{messaging['headline']}</h1>
            <p class="subheadline">{messaging['subheadline']}</p>

            <div class="trust-badges">
                <div class="trust-badge">
                    <span class="rating">⭐⭐⭐⭐⭐</span>
                    <span>{rating} ({students:,} students)</span>
                </div>
                <div class="trust-badge">
                    <span>👨‍🏫</span>
                    <span>Taught by {instructor}</span>
                </div>
            </div>
        </div>

        <!-- Benefits -->
        <div class="benefits">
            <div class="benefit-card">
                <h3>{messaging['benefit']}</h3>
                <p>Our proven methodology has helped thousands of students achieve their coding goals, even with busy schedules.</p>
            </div>

            <div class="benefit-card">
                <h3>🎯 Real Projects, Real Skills</h3>
                <p>Build 10+ portfolio projects you can show to employers. No more tutorial hell.</p>
            </div>

            <div class="benefit-card">
                <h3>💬 Lifetime Community Access</h3>
                <p>Join our private community of {students:,}+ students. Get help anytime, network, and find job opportunities.</p>
            </div>
        </div>

        <!-- Urgency -->
        <div class="urgency">
            🔥 Limited Time Offer: 50% OFF expires in 24 hours!
        </div>

        <!-- Pricing & Checkout -->
        <div class="pricing">
            <h2>Get Instant Access Today</h2>
            <div class="price">
                <span class="price-old">${{price * 2:.0f}}</span>
                ${price:.0f}
            </div>
            <p style="color: #666; margin-bottom: 30px;">One-time payment. Lifetime access. No subscriptions.</p>

            <!-- Checkout Form -->
            <form class="checkout-form" id="checkoutForm">
                <div class="form-group">
                    <label for="name">Full Name</label>
                    <input type="text" id="name" name="name" required placeholder="John Doe">
                </div>

                <div class="form-group">
                    <label for="email">Email Address</label>
                    <input type="email" id="email" name="email" required placeholder="john@example.com">
                </div>

                <button type="submit" class="btn-primary" id="checkoutBtn">
                    Enroll Now - ${price:.0f}
                </button>
            </form>

            <p style="margin-top: 20px; color: #999; font-size: 0.9em;">
                🔒 Secure checkout. 30-day money-back guarantee.
            </p>
        </div>
    </div>

    <script>
        // ========== RUDDERSTACK INITIALIZATION ==========

        const RUDDERSTACK_WRITE_KEY = '{rudderstack_write_key or "YOUR_WRITE_KEY"}';
        const RUDDERSTACK_DATA_PLANE_URL = '{rudderstack_data_plane_url or "https://your-instance.dataplane.rudderstack.com"}';

        // Initialize RudderStack
        rudderanalytics.load(RUDDERSTACK_WRITE_KEY, RUDDERSTACK_DATA_PLANE_URL, {{
            storage: {{
                type: 'localStorage',
            }},
            cookieDuration: 31536000000, // 1 year
        }});

        // ========== UTM EXTRACTION ==========

        function getUtmParams() {{
            const urlParams = new URLSearchParams(window.location.search);
            return {{
                utm_source: urlParams.get('utm_source'),
                utm_medium: urlParams.get('utm_medium'),
                utm_campaign: urlParams.get('utm_campaign'),
                utm_content: urlParams.get('utm_content'),
                utm_id: urlParams.get('utm_id'), // ⭐ KEY PARAMETER
            }};
        }}

        function saveUtmToStorage(utmParams) {{
            const expiry = Date.now() + (30 * 24 * 60 * 60 * 1000); // 30 days
            localStorage.setItem('utm_params', JSON.stringify({{
                ...utmParams,
                expiry
            }}));
        }}

        function getStoredUtm() {{
            const stored = localStorage.getItem('utm_params');
            if (!stored) return null;

            const data = JSON.parse(stored);
            if (Date.now() > data.expiry) {{
                localStorage.removeItem('utm_params');
                return null;
            }}

            return data;
        }}

        // ========== PAGE VIEWED EVENT ==========

        rudderanalytics.ready(() => {{
            // Extract UTM from URL
            const utmParams = getUtmParams();

            // Save UTM if present
            if (utmParams.utm_id) {{
                saveUtmToStorage(utmParams);
            }}

            // Get final UTM (from URL or storage)
            const finalUtm = utmParams.utm_id ? utmParams : getStoredUtm();

            // Get anonymousId
            const anonymousId = rudderanalytics.getAnonymousId();

            console.log('📊 RudderStack initialized');
            console.log('   AnonymousId:', anonymousId);
            console.log('   UTM:', finalUtm);

            // Send Page Viewed event
            rudderanalytics.page({{
                properties: {{
                    ...finalUtm,
                    page_url: window.location.href,
                    referrer: document.referrer,
                    course_name: '{course_name}',
                    pain_point: '{pain_point}',
                }}
            }});

            console.log('✅ Page Viewed event sent');
        }});

        // ========== CHECKOUT FORM SUBMISSION ==========

        document.getElementById('checkoutForm').addEventListener('submit', async (e) => {{
            e.preventDefault();

            const btn = document.getElementById('checkoutBtn');
            btn.disabled = true;
            btn.textContent = 'Processing...';

            const name = document.getElementById('name').value;
            const email = document.getElementById('email').value;
            const anonymousId = rudderanalytics.getAnonymousId();
            const utmParams = getStoredUtm();

            try {{
                // Send checkout request to backend
                const response = await fetch('/api/v1/edtech/checkout', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        name,
                        email,
                        utm_id: utmParams?.utm_id,
                        anonymous_id: anonymousId,
                    }})
                }});

                const data = await response.json();

                if (response.ok) {{
                    // Identify user
                    rudderanalytics.identify(data.user_id, {{
                        email: email,
                        name: name,
                    }});

                    // Send Order Completed event
                    rudderanalytics.track('Order Completed', {{
                        order_id: data.order_id,
                        total: {price},
                        currency: 'USD',
                        product_name: '{course_name}',
                        product_id: 'python_course_001',
                        utm_id: utmParams?.utm_id,
                    }});

                    console.log('✅ Order Completed event sent');

                    // Redirect to success page
                    window.location.href = '/api/v1/edtech/success?order_id=' + data.order_id;
                }} else {{
                    alert('Error: ' + (data.detail || 'Payment failed'));
                    btn.disabled = false;
                    btn.textContent = 'Enroll Now - ${price:.0f}';
                }}
            }} catch (error) {{
                console.error('Checkout error:', error);
                alert('Something went wrong. Please try again.');
                btn.disabled = false;
                btn.textContent = 'Enroll Now - ${price:.0f}';
            }}
        }});
    </script>
</body>
</html>
"""


@router.get("/landing", response_class=HTMLResponse)
async def edtech_landing_page(
    pain_point: str = "no_time",
    course: str = "python",
    request: Request = None,
):
    """
    Render EdTech landing page.

    Query params:
        - pain_point: EdTech pain point (no_time, too_expensive, etc.)
        - course: Course type (python, design, english)

    Example:
        GET /api/v1/edtech/landing?pain_point=no_time&course=python
    """

    import os

    courses = {
        "python": {
            "name": "Master Python in 30 Days",
            "price": 49.00,
            "instructor": "Alex Rodriguez",
            "students": 12453,
            "rating": 4.8,
        },
        "design": {
            "name": "UI/UX Design Bootcamp",
            "price": 59.00,
            "instructor": "Sarah Chen",
            "students": 8234,
            "rating": 4.9,
        },
        "english": {
            "name": "Business English Mastery",
            "price": 39.00,
            "instructor": "Michael Johnson",
            "students": 15678,
            "rating": 4.7,
        }
    }

    course_data = courses.get(course, courses["python"])

    html = get_edtech_landing_html(
        course_name=course_data["name"],
        price=course_data["price"],
        instructor=course_data["instructor"],
        students=course_data["students"],
        rating=course_data["rating"],
        pain_point=pain_point,
        rudderstack_write_key=os.getenv("RUDDERSTACK_WRITE_KEY"),
        rudderstack_data_plane_url=os.getenv("RUDDERSTACK_DATA_PLANE_URL"),
    )

    return HTMLResponse(content=html)


@router.post("/checkout")
async def checkout(
    checkout_data: CheckoutRequest,
    db: Session = Depends(get_db)
):
    """
    Process checkout and create conversion.

    This is a simplified MVP version. In production:
    - Integrate with payment gateway (Stripe, PayPal)
    - Verify payment before creating conversion
    - Send confirmation email
    - Grant course access
    """

    try:
        # Generate order ID
        order_id = f"ord_{uuid.uuid4().hex[:12]}"
        user_id = f"user_{uuid.uuid4().hex[:12]}"

        # In production: process payment here
        # stripe.Charge.create(...)

        logger.info(f"Checkout: {checkout_data.email} → Order {order_id}")

        # Note: Conversion will be created by RudderStack webhook
        # when Order Completed event arrives

        return {
            "success": True,
            "order_id": order_id,
            "user_id": user_id,
            "message": "Payment successful! Check your email for course access."
        }

    except Exception as e:
        logger.error(f"Checkout error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/success", response_class=HTMLResponse)
async def success_page(order_id: str):
    """Success page after purchase"""

    return HTMLResponse(content=f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Thank You!</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            background: white;
            padding: 60px 40px;
            border-radius: 20px;
            max-width: 600px;
            text-align: center;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        .success-icon {{
            font-size: 5em;
            margin-bottom: 20px;
        }}
        h1 {{
            color: #667eea;
            margin-bottom: 20px;
        }}
        p {{
            font-size: 1.2em;
            color: #666;
            line-height: 1.6;
        }}
        .order-id {{
            background: #f0f4ff;
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
            font-family: monospace;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="success-icon">🎉</div>
        <h1>Welcome Aboard!</h1>
        <p>Your purchase was successful. Check your email for course access instructions.</p>
        <div class="order-id">Order ID: {order_id}</div>
        <p>You should receive a confirmation email within 5 minutes.</p>
    </div>
</body>
</html>
    """)
