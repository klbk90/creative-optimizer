# Client Integration Guide

## 5-Minute Setup for Conversion Tracking

This guide shows you how to track conversions from UGC influencer campaigns.

---

## Step 1: Add Tracking Script (1 min)

Add this script to your website's `<head>` tag:

```html
<script src="https://creative-optimizer.vercel.app/api/v1/tracking/script"></script>
```

That's it! The script will automatically:
- Capture UTM parameters from influencer links
- Store them for later conversion tracking
- Expose tracking functions

---

## Step 2: Track Conversions (2 min)

### Option A: Simple Purchase Tracking

Add this code after a successful purchase:

```html
<script>
  // After payment confirmation
  creativeOptimizer.trackPurchase(49.99, 'order_12345');
</script>
```

### Option B: Track Signup/Trial

```html
<script>
  // After user registration
  creativeOptimizer.trackSignup('user@email.com');

  // Or after trial start
  creativeOptimizer.trackTrial('user@email.com');
</script>
```

### Option C: Custom Events

```html
<script>
  creativeOptimizer.track('custom_event', {
    revenue: 99.99,
    customer_id: 'user_123',
    plan: 'premium'
  });
</script>
```

---

## Step 3: Verify Integration (2 min)

1. **Add UTM parameter to your URL:**
   ```
   https://yoursite.com?utm_id=test_creative_123
   ```

2. **Open browser console** and check for:
   ```
   [Creative Optimizer] Tracking initialized
   ```

3. **Complete a test purchase**

4. **Check your Creative Optimizer dashboard** - you should see the conversion!

---

## How It Works

### Influencer Campaign Flow:

```
1. Influencer posts video with link:
   https://yoursite.com?utm_id=influencer_tiktok_abc123

2. User clicks → lands on your site
   → Tracking script captures utm_id

3. User signs up / makes purchase
   → creativeOptimizer.trackPurchase() called

4. Conversion sent to Creative Optimizer API
   → Attribution: This sale came from creative abc123!

5. Dashboard shows:
   - Which influencer drove the sale
   - Which creative performed best
   - ROI per influencer
```

---

## Advanced: Server-Side Tracking

If you prefer server-side tracking (no JavaScript):

```python
# Python example
import requests

def track_conversion(creative_id, revenue, customer_id):
    response = requests.post(
        'https://creative-optimizer.vercel.app/api/v1/conversion',
        json={
            'creative_id': creative_id,
            'event': 'purchase',
            'revenue': revenue,
            'customer_id': customer_id
        }
    )
    return response.json()

# After payment
track_conversion('creative_abc123', 49.99, 'user@email.com')
```

```javascript
// Node.js example
const axios = require('axios');

async function trackConversion(creativeId, revenue) {
  await axios.post(
    'https://creative-optimizer.vercel.app/api/v1/conversion',
    {
      creative_id: creativeId,
      event: 'purchase',
      revenue: revenue
    }
  );
}
```

---

## Troubleshooting

### "No conversions showing up"

1. Check browser console for errors
2. Verify utm_id is in URL: `?utm_id=xxx`
3. Make sure script loaded: Check Network tab for `tracking/script`

### "Conversions attributed to wrong creative"

1. Ensure unique utm_id per influencer/creative
2. Format: `utm_id=influencer_platform_uniqueid`
   - Example: `utm_id=johndoe_tiktok_001`

### "Need help?"

Email: support@creative-optimizer.com
Or check dashboard for integration status

---

## What You Get

After integration, your Creative Optimizer dashboard shows:

- **Conversion Rate** per influencer
- **Revenue** generated per creative
- **Best performing hooks** and creative styles
- **ROI** per campaign
- **Recommendations** on which creatives to scale

---

## Privacy & GDPR

- We only track UTM parameters (no PII)
- Customer IDs are hashed
- GDPR compliant
- No cookies used

---

**That's it! Integration complete in 5 minutes.**

Questions? Reach out to your account manager or email support@creative-optimizer.com
