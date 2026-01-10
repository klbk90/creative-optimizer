#!/bin/bash

echo "📊 Loading demo data with different patterns..."

API="http://localhost:8000"

# Create dummy video
dd if=/dev/zero of=/tmp/demo.mp4 bs=1024 count=512 2>/dev/null

echo "1️⃣ Uploading 5 creatives with different patterns..."

# Pattern 1: before_after + achievement
ID1=$(curl -s -X POST "$API/api/v1/creative/upload" \
  -F "video=@/tmp/demo.mp4" \
  -F "creative_name=Before/After Transformation" \
  -F "product_category=language_learning" \
  -F "campaign_tag=demo_batch" \
  -F "hook_type=before_after" \
  -F "emotion=achievement" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

# Pattern 2: question + curiosity  
ID2=$(curl -s -X POST "$API/api/v1/creative/upload" \
  -F "video=@/tmp/demo.mp4" \
  -F "creative_name=Question Hook" \
  -F "product_category=language_learning" \
  -F "campaign_tag=demo_batch" \
  -F "hook_type=question" \
  -F "emotion=curiosity" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

# Pattern 3: social_proof + fomo
ID3=$(curl -s -X POST "$API/api/v1/creative/upload" \
  -F "video=@/tmp/demo.mp4" \
  -F "creative_name=Social Proof" \
  -F "product_category=language_learning" \
  -F "campaign_tag=demo_batch" \
  -F "hook_type=social_proof" \
  -F "emotion=fomo" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

# Pattern 4: urgency + scarcity
ID4=$(curl -s -X POST "$API/api/v1/creative/upload" \
  -F "video=@/tmp/demo.mp4" \
  -F "creative_name=Urgency Hook" \
  -F "product_category=language_learning" \
  -F "campaign_tag=demo_batch" \
  -F "hook_type=urgency" \
  -F "emotion=scarcity" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

# Pattern 5: transformation + motivation
ID5=$(curl -s -X POST "$API/api/v1/creative/upload" \
  -F "video=@/tmp/demo.mp4" \
  -F "creative_name=Transformation Story" \
  -F "product_category=language_learning" \
  -F "campaign_tag=demo_batch" \
  -F "hook_type=transformation" \
  -F "emotion=motivation" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

echo "✅ 5 creatives uploaded"
echo ""

sleep 2

echo "2️⃣ Simulating ad results (updating metrics)..."

# WINNER: 0.8% CVR
curl -s -X PUT "$API/api/v1/creative/creatives/$ID1/metrics" \
  -F "impressions=50000" -F "clicks=2500" -F "conversions=400" > /dev/null
echo "  ✅ before_after + achievement: 400/50000 = 0.8% CVR"

# OK: 0.5% CVR  
curl -s -X PUT "$API/api/v1/creative/creatives/$ID2/metrics" \
  -F "impressions=48000" -F "clicks=1920" -F "conversions=240" > /dev/null
echo "  ✅ question + curiosity: 240/48000 = 0.5% CVR"

# LOSER: 0.2% CVR
curl -s -X PUT "$API/api/v1/creative/creatives/$ID3/metrics" \
  -F "impressions=52000" -F "clicks=1040" -F "conversions=104" > /dev/null
echo "  ✅ social_proof + fomo: 104/52000 = 0.2% CVR"

# OK: 0.6% CVR
curl -s -X PUT "$API/api/v1/creative/creatives/$ID4/metrics" \
  -F "impressions=47000" -F "clicks=1880" -F "conversions=282" > /dev/null
echo "  ✅ urgency + scarcity: 282/47000 = 0.6% CVR"

# WINNER: 0.9% CVR
curl -s -X PUT "$API/api/v1/creative/creatives/$ID5/metrics" \
  -F "impressions=51000" -F "clicks=2550" -F "conversions=459" > /dev/null
echo "  ✅ transformation + motivation: 459/51000 = 0.9% CVR"

echo ""
echo "3️⃣ Markov Chain learned! Top patterns:"
curl -s "$API/api/v1/creative/patterns/top?product_category=language_learning" | python3 -m json.tool

echo ""
echo "4️⃣ Thompson Sampling recommendations:"
curl -s "$API/api/v1/creative/patterns/recommend?product_category=language_learning&n_patterns=3" | python3 -m json.tool

echo ""
echo "✅ Demo data loaded!"
echo ""
echo "📊 View in UI: http://localhost:3001/creatives?campaign_tag=demo_batch"
echo "📈 Analytics: http://localhost:3001/analytics"
echo "🎯 Patterns: http://localhost:3001/patterns"
