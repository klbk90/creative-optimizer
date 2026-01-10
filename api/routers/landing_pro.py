"""
Premium EdTech Landing - стильный современный лендинг без npm.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
import os

router = APIRouter(prefix="/landing", tags=["Premium Landing"])


@router.get("", response_class=HTMLResponse)
async def premium_landing(
    request: Request,
    pain_point: str = "no_time",
    course: str = "python",
    utm_id: str = None
):
    """Супер стильный EdTech лендинг"""

    pain_messages = {
        "no_time": {
            "headline": "Learn Python in Just 15 Minutes a Day",
            "emoji": "⏰",
            "subtext": "Busy schedule? No problem."
        },
        "fear_failure": {
            "headline": "95% of Students Get Their First Dev Job",
            "emoji": "✅",
            "subtext": "Stop worrying. Start winning."
        },
        "too_expensive": {
            "headline": "Professional Course for Just $49",
            "emoji": "💰",
            "subtext": "Same quality, 10x cheaper."
        }
    }

    msg = pain_messages.get(pain_point, pain_messages["no_time"])

    return HTMLResponse(content=f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{msg['headline']}</title>

    <!-- RudderStack SDK -->
    <script>
    rudderanalytics=window.rudderanalytics=[];for(var methods=["load","page","track","identify","alias","group","ready","reset","getAnonymousId","setAnonymousId"],i=0;i<methods.length;i++){{var method=methods[i];rudderanalytics[method]=function(a){{return function(){{rudderanalytics.push([a].concat(Array.prototype.slice.call(arguments)))}}}}(method)}}
    </script>
    <script src="https://cdn.rudderlabs.com/v1.1/rudder-analytics.min.js"></script>

    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #0a0a0a;
            color: #fff;
            overflow-x: hidden;
        }}

        /* Animated gradient background */
        .bg-wrapper {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            background-size: 300% 300%;
            animation: gradientShift 15s ease infinite;
            z-index: -1;
        }}

        @keyframes gradientShift {{
            0% {{ background-position: 0% 50%; }}
            50% {{ background-position: 100% 50%; }}
            100% {{ background-position: 0% 50%; }}
        }}

        .container {{
            max-width: 1100px;
            margin: 0 auto;
            padding: 40px 20px;
            position: relative;
            z-index: 1;
        }}

        /* Hero Section */
        .hero {{
            text-align: center;
            padding: 80px 20px;
            animation: fadeInUp 0.8s ease;
        }}

        @keyframes fadeInUp {{
            from {{ opacity: 0; transform: translateY(40px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .emoji-big {{
            font-size: 120px;
            animation: float 3s ease-in-out infinite;
            display: inline-block;
            margin-bottom: 30px;
        }}

        @keyframes float {{
            0%, 100% {{ transform: translateY(0px); }}
            50% {{ transform: translateY(-20px); }}
        }}

        h1 {{
            font-size: clamp(2.5rem, 6vw, 5rem);
            font-weight: 900;
            line-height: 1.1;
            margin-bottom: 20px;
            background: linear-gradient(to right, #fff, #e0e0e0);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .subtext {{
            font-size: 1.5rem;
            opacity: 0.95;
            margin-bottom: 40px;
        }}

        /* Stats badges */
        .stats {{
            display: flex;
            justify-content: center;
            gap: 20px;
            flex-wrap: wrap;
            margin: 40px 0;
        }}

        .stat-badge {{
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(10px);
            padding: 15px 30px;
            border-radius: 50px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            font-weight: 600;
            transition: transform 0.3s ease;
        }}

        .stat-badge:hover {{
            transform: translateY(-5px);
        }}

        /* Benefits Grid */
        .benefits {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin: 60px 0;
        }}

        .benefit-card {{
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            padding: 40px;
            border-radius: 24px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
            animation: slideUp 0.6s ease;
        }}

        .benefit-card:hover {{
            transform: translateY(-10px);
            background: rgba(255, 255, 255, 0.15);
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        }}

        @keyframes slideUp {{
            from {{ opacity: 0; transform: translateY(30px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .benefit-card h3 {{
            font-size: 1.8rem;
            margin-bottom: 15px;
        }}

        /* Urgency Banner */
        .urgency {{
            background: linear-gradient(135deg, #ff6b6b, #ff5252);
            padding: 20px;
            border-radius: 16px;
            text-align: center;
            font-weight: 700;
            font-size: 1.2rem;
            margin: 40px 0;
            box-shadow: 0 10px 40px rgba(255, 107, 107, 0.4);
            animation: pulse 2s ease infinite;
        }}

        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.02); }}
        }}

        /* Pricing Card */
        .pricing-card {{
            background: rgba(255, 255, 255, 0.95);
            color: #333;
            padding: 60px 40px;
            border-radius: 32px;
            max-width: 600px;
            margin: 0 auto;
            box-shadow: 0 30px 80px rgba(0, 0, 0, 0.4);
            animation: scaleIn 0.5s ease;
        }}

        @keyframes scaleIn {{
            from {{ opacity: 0; transform: scale(0.9); }}
            to {{ opacity: 1; transform: scale(1); }}
        }}

        .price-old {{
            text-decoration: line-through;
            color: #999;
            font-size: 2rem;
        }}

        .price-new {{
            font-size: 5rem;
            font-weight: 900;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 20px 0;
        }}

        /* Form */
        input {{
            width: 100%;
            padding: 18px 24px;
            border: 2px solid #e0e0e0;
            border-radius: 12px;
            font-size: 1.1rem;
            margin-bottom: 20px;
            transition: all 0.3s ease;
        }}

        input:focus {{
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
        }}

        /* CTA Button */
        .btn-cta {{
            width: 100%;
            padding: 24px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 16px;
            font-size: 1.5rem;
            font-weight: 800;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 10px 40px rgba(102, 126, 234, 0.4);
            position: relative;
            overflow: hidden;
        }}

        .btn-cta:hover {{
            transform: translateY(-3px);
            box-shadow: 0 15px 50px rgba(102, 126, 234, 0.6);
        }}

        .btn-cta:active {{
            transform: translateY(0);
        }}

        .btn-cta::before {{
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            transition: left 0.5s;
        }}

        .btn-cta:hover::before {{
            left: 100%;
        }}

        /* Mobile */
        @media (max-width: 768px) {{
            h1 {{ font-size: 2.5rem; }}
            .emoji-big {{ font-size: 80px; }}
            .price-new {{ font-size: 3.5rem; }}
            .benefit-card {{ padding: 30px; }}
        }}
    </style>
</head>
<body>
    <div class="bg-wrapper"></div>

    <div class="container">
        <!-- Hero -->
        <div class="hero">
            <div class="emoji-big">{msg['emoji']}</div>
            <h1>{msg['headline']}</h1>
            <p class="subtext">{msg['subtext']}</p>

            <div class="stats">
                <div class="stat-badge">⭐⭐⭐⭐⭐ 4.8 (12,453 students)</div>
                <div class="stat-badge">👨‍🏫 Taught by Alex Rodriguez</div>
                <div class="stat-badge">🎯 95% Job Success Rate</div>
            </div>
        </div>

        <!-- Benefits -->
        <div class="benefits">
            <div class="benefit-card">
                <h3>⏰ Fits Your Schedule</h3>
                <p>Learn at your own pace with bite-sized lessons. Perfect for busy professionals.</p>
            </div>

            <div class="benefit-card">
                <h3>🚀 Real Projects</h3>
                <p>Build 10+ portfolio projects. No more tutorial hell. Real skills, real results.</p>
            </div>

            <div class="benefit-card">
                <h3>💬 Lifetime Access</h3>
                <p>Join 12,000+ students in our private community. Get help anytime, anywhere.</p>
            </div>
        </div>

        <!-- Urgency -->
        <div class="urgency">
            🔥 Limited Time: 50% OFF expires in 24 hours!
        </div>

        <!-- Pricing -->
        <div class="pricing-card">
            <h2 style="text-align: center; margin-bottom: 30px; font-size: 2rem;">Get Instant Access</h2>

            <div style="text-align: center;">
                <div class="price-old">$98</div>
                <div class="price-new">$49</div>
                <p style="color: #666; margin-bottom: 40px;">One-time payment. Lifetime access.</p>
            </div>

            <form id="checkoutForm">
                <input type="text" id="name" placeholder="Your Name" required>
                <input type="email" id="email" placeholder="your@email.com" required>

                <button type="submit" class="btn-cta">
                    Enroll Now - $49
                </button>
            </form>

            <p style="text-align: center; color: #999; margin-top: 20px; font-size: 0.9rem;">
                🔒 Secure checkout • 30-day money-back guarantee
            </p>
        </div>
    </div>

    <script>
        // RudderStack initialization
        const RUDDERSTACK_WRITE_KEY = '{os.getenv("RUDDERSTACK_WRITE_KEY", "YOUR_KEY")}';
        const RUDDERSTACK_DATA_PLANE_URL = '{os.getenv("RUDDERSTACK_DATA_PLANE_URL", "https://your-instance.dataplane.rudderstack.com")}';

        // Load RudderStack
        if (RUDDERSTACK_WRITE_KEY !== 'YOUR_KEY') {{
            rudderanalytics.load(RUDDERSTACK_WRITE_KEY, RUDDERSTACK_DATA_PLANE_URL);
        }}

        // UTM handling
        const urlParams = new URLSearchParams(window.location.search);
        const utmId = urlParams.get('utm_id') || '{utm_id or ""}';

        if (utmId) {{
            localStorage.setItem('utm_id', utmId);
            localStorage.setItem('utm_expiry', Date.now() + (30 * 24 * 60 * 60 * 1000));
        }}

        // Page View tracking
        if (typeof rudderanalytics !== 'undefined' && RUDDERSTACK_WRITE_KEY !== 'YOUR_KEY') {{
            rudderanalytics.page({{
                properties: {{
                    utm_id: utmId || localStorage.getItem('utm_id'),
                    pain_point: '{pain_point}',
                    course: '{course}',
                }}
            }});
            console.log('✅ Page Viewed tracked');
        }}

        // Form submission
        document.getElementById('checkoutForm').addEventListener('submit', async (e) => {{
            e.preventDefault();

            const btn = e.target.querySelector('button');
            btn.textContent = 'Processing...';
            btn.disabled = true;

            const name = document.getElementById('name').value;
            const email = document.getElementById('email').value;
            const anonId = typeof rudderanalytics !== 'undefined' ? rudderanalytics.getAnonymousId() : 'anon_fallback';

            try {{
                const response = await fetch('/api/v1/edtech/checkout', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        name,
                        email,
                        utm_id: localStorage.getItem('utm_id'),
                        anonymous_id: anonId,
                    }})
                }});

                const data = await response.json();

                if (response.ok) {{
                    // Track conversion
                    if (typeof rudderanalytics !== 'undefined') {{
                        rudderanalytics.identify(data.user_id, {{ email, name }});
                        rudderanalytics.track('Order Completed', {{
                            order_id: data.order_id,
                            total: 49.00,
                            currency: 'USD',
                            product_name: 'Python Course',
                            utm_id: localStorage.getItem('utm_id'),
                        }});
                        console.log('✅ Order Completed tracked');
                    }}

                    window.location.href = '/api/v1/edtech/success?order_id=' + data.order_id;
                }} else {{
                    alert('Error: ' + (data.detail || 'Payment failed'));
                    btn.textContent = 'Enroll Now - $49';
                    btn.disabled = false;
                }}
            }} catch (error) {{
                console.error('Checkout error:', error);
                alert('Something went wrong. Please try again.');
                btn.textContent = 'Enroll Now - $49';
                btn.disabled = false;
            }}
        }});
    </script>
</body>
</html>
""")
