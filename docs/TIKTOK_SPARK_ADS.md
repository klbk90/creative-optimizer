

# 🚀 TikTok Spark Ads - Complete Setup Guide

**The secret weapon for testing UGC creatives at scale.**

Spark Ads let you promote organic-looking videos WITHOUT the "Sponsored" label looking intrusive. Perfect for testing creatives before committing to big budgets.

---

## 📚 Table of Contents

1. [What are Spark Ads?](#what-are-spark-ads)
2. [Why Spark Ads for UGC Testing?](#why-spark-ads-for-ugc-testing)
3. [Setup Guide](#setup-guide)
4. [Integration with UTM Tracking](#integration-with-utm-tracking)
5. [Campaign Structure](#campaign-structure)
6. [Optimization Tips](#optimization-tips)
7. [Scaling Strategy](#scaling-strategy)

---

## 🎯 What are Spark Ads?

**Spark Ads = Boosted TikTok Posts**

Unlike traditional TikTok ads (created in Ads Manager), Spark Ads promote EXISTING TikTok posts:
- From your own account
- From creator accounts (with permission)
- Looks native (small "Sponsored" tag, but blends in)
- Users can like, comment, follow (engagement stays on original post)

### Spark Ads vs Traditional Ads

| Feature | Spark Ads | Traditional Ads |
|---------|-----------|-----------------|
| **Look** | Native TikTok post | Obviously an ad |
| **Engagement** | Stays on original post | Isolated to ad |
| **"Sponsored" Label** | Small tag | Big banner |
| **Testing Speed** | Fast (use existing post) | Slow (upload to Ads Manager) |
| **Authenticity** | High (looks organic) | Low (screams "ad") |
| **Best For** | UGC testing, organic-looking | Big budgets, branded |

**Verdict for testing:** Spark Ads win. Higher CTR, lower CPC, faster iteration.

---

## 💡 Why Spark Ads for UGC Testing?

### The Problem with Regular Ads

You order UGC from Fiverr → Upload to TikTok Ads Manager → Everyone knows it's an ad → Performance tanks.

### The Spark Ads Solution

You order UGC from Fiverr → Post organically on TikTok → Promote with Spark Ads → Looks native → 2-3x better performance.

### Real Numbers

| Metric | Traditional Ads | Spark Ads |
|--------|----------------|-----------|
| **CTR** | 0.8-1.2% | 2-3% |
| **CPC** | $0.80-1.20 | $0.40-0.70 |
| **CVR** | 3-5% | 6-10% |
| **CPA** | $25-40 | $15-25 |

**Why?** Spark Ads don't trigger "ad blindness" - users think it's organic content.

---

## 🛠️ Setup Guide

### Prerequisites

- ✅ TikTok Business Account
- ✅ TikTok Ads Manager account
- ✅ Payment method added
- ✅ At least 1 TikTok account to post videos

### Step 1: Create TikTok Business Account

1. Go to [TikTok Ads Manager](https://ads.tiktok.com/)
2. Click "Create an Ad Account"
3. Fill in:
   - Business name
   - Country (where you're advertising)
   - Time zone
   - Currency
4. Verify email
5. Add payment method (credit card or PayPal)

**Note:** You can have multiple ad accounts under one business account (useful for multi-product testing).

---

### Step 2: Create TikTok Profile(s) for Posting

You need at least ONE TikTok account to post videos that you'll promote with Spark Ads.

**Option A: Use Your Brand Account**
- Pro: Engagement stays on your profile
- Con: If ad performs badly, might hurt organic reach

**Option B: Create Separate Testing Accounts**
- Pro: Isolate ad performance from organic
- Pro: Test multiple niches/angles
- Con: Need to manage multiple accounts

**Recommendation:** Create 2-3 testing accounts (different niches/angles).

**Setup:**
1. Download TikTok app
2. Create new account with email (not phone - easier to manage)
3. Complete profile:
   - Profile pic (logo or generic)
   - Bio (optional - can be empty)
   - Username (e.g., @lootbox_daily)
4. Make profile **PUBLIC** (required for Spark Ads)

---

### Step 3: Enable Spark Ads on Your TikTok Account

This allows Ads Manager to promote posts from your account.

**On TikTok App:**
1. Go to Profile → Settings → Privacy
2. Scroll to "Ad Authorization"
3. Toggle ON "Ad Authorization"
4. Note down your TikTok Account ID (you'll need it)

**Or on Desktop:**
1. Go to [TikTok Creator Marketplace](https://creatormarketplace.tiktok.com/)
2. Settings → Ad Settings
3. Enable "Allow others to use your videos as ads"

---

### Step 4: Post Your UGC Video

1. Upload video from Fiverr creator
2. Add caption (use your tested hooks!)
3. Add hashtags (optional, won't affect ad performance)
4. **Important:** Don't add clickable links in caption (TikTok doesn't allow)
5. Post!

**Wait 1-2 hours** before promoting (TikTok needs to process the post).

---

### Step 5: Create Spark Ads Campaign

#### 5.1 Create Campaign

1. Go to TikTok Ads Manager
2. Click "Create" → "Custom Mode" (not Simplified)
3. **Campaign Settings:**
   - Objective: **Conversions** (if you have pixel) OR **Traffic** (if testing)
   - Campaign name: `[Product] - Spark Ads - [Date]`
   - Budget: Campaign budget (optional) or leave unlimited
   - Budget optimization: ON (let TikTok optimize across ad groups)

#### 5.2 Create Ad Group

1. **Ad Group Name:** `UGC - [Hook Type] - [Emotion] - [Date]`
   - Example: `UGC - Wait - Excitement - Jan06`
2. **Placement:** TikTok only (uncheck everything else for testing)
3. **Targeting:**
   - **Location:** Your target country (e.g., United States)
   - **Gender:** All (or specific if relevant)
   - **Age:** 18-55+ (adjust for your product)
   - **Languages:** English (if targeting US)
   - **Interests:** Start broad, narrow later
     - For lootbox: Gaming, Mobile Games, Entertainment
     - For sports betting: Sports, Football, NBA
4. **Budget & Schedule:**
   - Daily budget: $20-50 (for testing)
   - Schedule: Run continuously
   - Optimization goal: **Conversion** (if pixel setup) OR **Click** (if no pixel)
   - Bid: Automatic (for testing)

#### 5.3 Create Ad (Spark Ad)

1. **Ad Format:** Spark Ad
2. **TikTok Post:** Click "Use TikTok Post"
3. **Select Post:**
   - Option 1: Choose from "Your TikTok Account" (if you posted it)
   - Option 2: Enter post code (if creator posted it - see below)
4. **Display Name:** Your brand name (will show in ad)
5. **Call-to-Action (CTA):**
   - If objective = Traffic: "Learn More" or "Visit Website"
   - If objective = Conversions: "Download" or "Shop Now"
6. **Landing Page:**
   - **THIS IS WHERE UTM TRACKING COMES IN!**
   - URL: `https://yourdomain.com/l/{utm_id}` (landing page)
   - OR: `https://t.me/your_bot?start={utm_id}` (direct to Telegram)

#### 5.4 UTM Parameters (CRITICAL!)

TikTok auto-adds some UTM parameters, but you should add custom ones:

**URL Structure:**
```
https://yourdomain.com/l/tiktok_sparkads_jan06?
  utm_source=tiktok
  &utm_medium=spark_ads
  &utm_campaign=lootbox_jan_2025
  &utm_content=ugc_wait_excitement
  &ttclid={{CLICK_ID}}
```

**Explanation:**
- `utm_source=tiktok` - Traffic source
- `utm_medium=spark_ads` - Distinguishes from organic TikTok
- `utm_campaign=lootbox_jan_2025` - Your campaign name
- `utm_content=ugc_wait_excitement` - Creative variant (use hook + emotion)
- `{{CLICK_ID}}` - TikTok's click ID (auto-populated)

**In our system:**
```
https://yourdomain.com/l/tiktok_sparkads_jan06
```

The utm_id (`tiktok_sparkads_jan06`) links to our database with all UTM params.

---

### Step 6: Launch & Monitor

1. Click "Submit" → TikTok reviews ad (1-24 hours)
2. Once approved, ad starts running
3. Monitor in Ads Manager:
   - Impressions
   - Clicks
   - CTR
   - CPC
   - Conversions (if pixel setup)

---

## 🔗 Integration with UTM Tracking

### Workflow

```
1. Fiverr creator sends video
   ↓
2. Analyze with Creative API → Get predicted CVR
   ↓
3. Post on TikTok account
   ↓
4. Create Spark Ad with UTM link
   ↓
5. User clicks ad → Landing page (utm_id tracked)
   ↓
6. User redirects to Telegram bot (utm_id preserved)
   ↓
7. User buys lootbox → Conversion webhook (utm_id attributed)
   ↓
8. Update creative performance in database
```

### API Integration Example

#### 1. Analyze Creative (Before Posting)

```bash
curl -X POST http://localhost:8000/api/v1/creative/analyze \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{
    "caption": "Wait for it... this lootbox opening is INSANE! 😱",
    "hashtags": ["fyp", "gaming", "lootbox"],
    "product_category": "lootbox"
  }'
```

**Response:**
```json
{
  "hook_type": "wait",
  "emotion": "excitement",
  "pacing": "fast",
  "predicted_cvr": 0.12,
  "predicted_cvr_percent": 12.0,
  "confidence_score": 0.75,
  "sample_size": 15
}
```

**Decision:** CVR 12% with confidence 75% → Worth testing!

---

#### 2. Create Creative Record

```bash
curl -X POST http://localhost:8000/api/v1/creative/creatives \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{
    "name": "UGC Lootbox - Wait Hook - Jan 6",
    "creative_type": "ugc",
    "product_category": "lootbox",
    "source_platform": "tiktok",
    "video_url": "https://tiktok.com/@lootbox_daily/video/123456789",
    "production_cost": 15000,
    "hook_type": "wait",
    "emotion": "excitement",
    "pacing": "fast",
    "predicted_cvr": 1200,
    "test_phase": "ugc_test"
  }'
```

**Response:**
```json
{
  "creative_id": "abc-123-def-456",
  "message": "Creative saved successfully"
}
```

---

#### 3. Generate UTM Link

```bash
curl -X POST http://localhost:8000/api/v1/utm/generate \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{
    "utm_source": "tiktok",
    "utm_medium": "spark_ads",
    "utm_campaign": "lootbox_jan_2025",
    "utm_content": "ugc_wait_excitement",
    "link_type": "landing"
  }'
```

**Response:**
```json
{
  "utm_id": "tiktok_abc123",
  "utm_link": "https://yourdomain.com/l/tiktok_abc123",
  "telegram_link": "https://t.me/your_bot?start=tiktok_abc123"
}
```

**Use this link** in your Spark Ad!

---

#### 4. Track Performance

After running ads for 3-7 days, update creative performance:

```bash
curl -X PUT http://localhost:8000/api/v1/creative/creatives/abc-123-def-456 \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{
    "impressions": 50000,
    "clicks": 1500,
    "conversions": 180,
    "revenue": 900000,
    "status": "active"
  }'
```

**System calculates:**
- CTR: 1500/50000 = 3%
- CVR: 180/1500 = 12%
- ROAS: $9000 / ($150 production + spend) = ...

---

#### 5. Update Markov Chain

After testing 10+ creatives:

```bash
curl -X POST http://localhost:8000/api/v1/creative/patterns/update \
  -H "Authorization: Bearer $JWT_TOKEN"
```

**System recalculates:**
- Which hooks perform best
- Which emotions drive conversions
- Confidence intervals for predictions

---

## 📊 Campaign Structure

### Strategy: Test Fast, Scale Winners

#### Phase 1: Initial Test (Week 1)

**5 UGC Videos** → **5 Spark Ads** → **$50/day each** = **$1,750/week**

| Creative | Hook | Emotion | Budget | Goal |
|----------|------|---------|--------|------|
| UGC-1 | Wait | Excitement | $50/day | Test hook |
| UGC-2 | Question | Curiosity | $50/day | Test hook |
| UGC-3 | Bold Claim | Greed | $50/day | Test emotion |
| UGC-4 | Wait | FOMO | $50/day | Test emotion |
| UGC-5 | Urgency | Excitement | $50/day | Test CTA |

**After 7 days:**
- Analyze which creative has highest CVR
- Pause losers
- Scale winner

---

#### Phase 2: Scale Winner (Week 2)

**1 Winning Creative** → **3 Ad Groups** → **$200/day total**

| Ad Group | Targeting | Budget | Goal |
|----------|-----------|--------|------|
| Broad | Gaming interests | $100/day | Find new audiences |
| Lookalike | Converters | $50/day | Scale existing |
| Retargeting | Website visitors | $50/day | Convert warm traffic |

**After 7 days:**
- If ROAS > 3x → Scale to $500/day
- If ROAS < 2x → Back to testing

---

#### Phase 3: Creative Refresh (Week 3-4)

**Problem:** Creative fatigue (people see same ad too many times)

**Solution:** Refresh creative every 2 weeks

**Strategy:**
- Order 3 more UGC variations (same hook, different visuals)
- Test new hooks based on Markov Chain insights
- Cycle creatives (pause old, launch new)

---

## 🎯 Optimization Tips

### 1. Creative Optimization

**If CTR is low (<1.5%):**
- ❌ Hook is weak
- ✅ Test different hook ("Wait" vs "Question")
- ✅ Change thumbnail (first frame)
- ✅ Add text overlay in first 2 seconds

**If CTR is high but CVR is low:**
- ❌ Landing page or bot experience is bad
- ✅ Simplify landing page
- ✅ Speed up redirect (2s instead of 5s)
- ✅ Improve bot onboarding

---

### 2. Targeting Optimization

**Start broad, narrow down:**

**Week 1: Broad**
```
Interests: Gaming, Entertainment, Mobile Games
Age: 18-55
Gender: All
```

**Week 2: Narrow (based on data)**
```
Interests: Loot box, Gacha games
Age: 18-34 (if they convert better)
Gender: Male (if they convert better)
```

**Week 3: Lookalike**
```
Create lookalike audience from converters
Size: 1% (most similar)
```

---

### 3. Budget Optimization

**Bidding Strategy:**

**Testing Phase:** Automatic bidding
- Let TikTok find optimal bid
- Gather data

**Scaling Phase:** Lowest cost with bid cap
- Set max CPC: $1.00 (adjust based on your CPA target)
- Prevents overspending

**Formula:**
```
Max CPC = Target CPA × CVR

Example:
Target CPA = $25
CVR = 10%
Max CPC = $25 × 0.10 = $2.50
```

---

### 4. Time-of-Day Optimization

**Check performance by hour:**

1. Ads Manager → Reports
2. Breakdown → Time
3. Find peak hours (highest CVR)
4. Schedule ads for peak hours only

**Example:**
```
Peak hours: 6pm-11pm (after work/school)
Pause ads: 2am-8am (low conversion hours)
```

**Benefit:** Save 30-40% budget by avoiding low-converting hours.

---

## 📈 Scaling Strategy

### When to Scale?

**Only scale if:**
- ✅ ROAS > 3x (for 7+ days)
- ✅ CVR > 8% (for your product)
- ✅ At least 50 conversions (statistical significance)
- ✅ No creative fatigue (frequency < 3)

### How to Scale?

**Option 1: Increase Budget (Slow)**
```
Day 1: $50/day
Day 3: $75/day (+50%)
Day 5: $112/day (+50%)
Day 7: $170/day (+50%)
```

**Why slow?** TikTok algorithm needs time to adjust. Doubling budget overnight tanks performance.

**Option 2: Duplicate Ad Groups (Fast)**
```
Original: $50/day (keep running)
Clone 1: $50/day (same targeting)
Clone 2: $50/day (lookalike)
Clone 3: $50/day (interest expansion)
= $200/day total
```

**Why better?** Doesn't disrupt original ad group's learning.

---

### Scaling Limits

**Daily spend limits by experience:**

| Your Experience | Max Daily Budget |
|-----------------|------------------|
| First campaign | $100-200/day |
| 1 month experience | $500-1000/day |
| 3+ months | $2000-5000/day |
| Agency/Expert | $10,000+/day |

**Why?** TikTok throttles new advertisers to prevent fraud. Build trust over time.

---

## 🚨 Common Mistakes

### 1. Testing Too Many Variables

❌ **Wrong:**
```
5 different hooks
+ 3 different emotions
+ 2 different CTAs
+ 3 different audiences
= 90 combinations!
```

✅ **Right:**
```
Test 1 variable at a time:
Week 1: Test hooks (keep emotion/CTA same)
Week 2: Test emotions (use winning hook)
Week 3: Test audiences (use winning creative)
```

---

### 2. Giving Up Too Early

❌ **Wrong:**
```
Day 1: Launched ad
Day 2: Only 5 conversions, paused
```

✅ **Right:**
```
Day 1-3: Learning phase (algorithm is learning)
Day 4-7: Evaluation phase (now judge performance)
Decision: Need 7+ days AND 50+ conversions before judging
```

---

### 3. Scaling Winners Too Fast

❌ **Wrong:**
```
Day 7: $50/day, ROAS 5x → "Let's do $1000/day!"
Day 8: ROAS drops to 1.5x → Panic
```

✅ **Right:**
```
Day 7: $50/day, ROAS 5x
Day 10: $75/day (+50%)
Day 13: $112/day (+50%)
Day 16: $170/day (+50%)
Gradually scale, monitor ROAS
```

---

### 4. Ignoring Creative Fatigue

**Signs of creative fatigue:**
- Frequency > 3 (users see ad 3+ times)
- CTR decreasing daily
- CPC increasing
- Comments like "I keep seeing this ad"

**Solution:**
- Pause fatigued ad
- Launch creative refresh
- Rotate creatives weekly

---

## 💰 Budget Guide

### Testing Budget

**Minimum to get statistical significance:**

```
Formula:
Testing budget = (Target CPA × 50 conversions) × 3 creatives

Example (Lootbox):
Target CPA = $25
Testing budget = ($25 × 50) × 3 = $3,750

Timeline: 2-3 weeks
```

**Breakdown:**
- Week 1: $1,750 (5 creatives × $50/day × 7 days)
- Week 2: $1,000 (2 winners × $75/day × 7 days)
- Week 3: $1,000 (1 winner × $150/day × 7 days)

**Outcome:** 1 proven winner, ready to scale.

---

### Scaling Budget

**Once you have a winner:**

| Month | Daily Budget | Monthly Spend | Expected ROAS | Revenue |
|-------|--------------|---------------|---------------|---------|
| Month 1 | $200/day | $6,000 | 3x | $18,000 |
| Month 2 | $500/day | $15,000 | 3x | $45,000 |
| Month 3 | $1,000/day | $30,000 | 2.5x | $75,000 |
| Month 4 | $2,000/day | $60,000 | 2x | $120,000 |

**Note:** ROAS decreases as you scale (law of diminishing returns).

---

## 🎓 Advanced: A/B Testing Framework

### Scientific Testing Approach

**Hypothesis:**
> "Wait" hook performs better than "Question" hook for lootbox UGC.

**Test Setup:**
```
Control: UGC with "Wait for it..." hook
Variant: UGC with "Did you know...?" hook
Budget: $50/day each
Duration: 7 days
Sample size: 50 conversions minimum
```

**Analysis:**
```bash
curl http://localhost:8000/api/v1/creative/creatives?product_category=lootbox
```

**Decision criteria:**
- If Control CVR > Variant CVR + 2% → Control wins
- If Variant CVR > Control CVR + 2% → Variant wins
- If difference < 2% → Inconclusive, test longer

**Iterate:**
```
Winner: "Wait" hook (12% CVR vs 9% CVR)
Next test: "Wait" hook with Excitement vs FOMO emotion
```

---

## 📚 Resources

### Official TikTok Resources
- [TikTok Ads Manager](https://ads.tiktok.com/)
- [Spark Ads Guide](https://ads.tiktok.com/help/article?aid=10008)
- [TikTok Pixel Setup](https://ads.tiktok.com/help/article?aid=10000357)

### Tools
- **Creative Analysis:** [Foreplay.co](https://foreplay.co) (spy on competitors' ads)
- **Ad Library:** [TikTok Creative Center](https://ads.tiktok.com/business/creativecenter)
- **Analytics:** Our UTM Tracking API (localhost:8000/docs)

---

## ✅ Checklist: Your First Spark Ad Campaign

- [ ] Created TikTok Ads Manager account
- [ ] Created TikTok profile(s) for posting
- [ ] Enabled Ad Authorization on TikTok profile
- [ ] Ordered 3-5 UGC videos from Fiverr
- [ ] Analyzed creatives with Creative API
- [ ] Posted videos on TikTok (wait 1-2 hours)
- [ ] Generated UTM links for tracking
- [ ] Created Spark Ads campaign
- [ ] Set daily budget: $50/day per creative
- [ ] Launched campaign
- [ ] Monitored performance for 7 days
- [ ] Updated creative performance in database
- [ ] Scaled winner or iterated on losers

---

**Ready to launch? Start with ONE creative, $50/day, 7 days. Learn the system. Then scale.** 🚀
