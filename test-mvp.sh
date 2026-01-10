#!/bin/bash

echo "🧪 Testing Creative Optimizer MVP"
echo "=================================="
echo ""

API_URL="http://localhost:8000"

# 1. Health check
echo "1️⃣ Health Check..."
curl -s $API_URL/health | python3 -m json.tool
echo ""

# 2. Create test video (dummy 1MB file)
echo "2️⃣ Creating test video file..."
dd if=/dev/zero of=/tmp/test_creative.mp4 bs=1024 count=1024 2>/dev/null
echo "Created /tmp/test_creative.mp4 (1MB)"
echo ""

# 3. Upload creative
echo "3️⃣ Uploading creative..."
CREATIVE_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/creative/upload" \
  -F "video=@/tmp/test_creative.mp4" \
  -F "creative_name=Test Creative #1" \
  -F "product_category=language_learning" \
  -F "creative_type=ugc" \
  -F "campaign_tag=test_jan_2025")

echo "$CREATIVE_RESPONSE" | python3 -m json.tool
CREATIVE_ID=$(echo "$CREATIVE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null)
echo ""

if [ -z "$CREATIVE_ID" ]; then
    echo "❌ Failed to upload creative"
    exit 1
fi

echo "✅ Creative ID: $CREATIVE_ID"
echo ""

# 4. List creatives
echo "4️⃣ Listing creatives..."
curl -s "$API_URL/api/v1/creative/creatives?limit=5" | python3 -m json.tool
echo ""

# 5. Update metrics
echo "5️⃣ Updating creative metrics..."
curl -s -X PUT "$API_URL/api/v1/creative/creatives/$CREATIVE_ID/metrics" \
  -F "impressions=10000" \
  -F "clicks=500" \
  -F "conversions=50" | python3 -m json.tool
echo ""

# 6. List updated creatives
echo "6️⃣ Listing creatives with updated metrics..."
curl -s "$API_URL/api/v1/creative/creatives?campaign_tag=test_jan_2025" | python3 -m json.tool
echo ""

echo "✅ MVP Test Complete!"
echo ""
echo "Next steps:"
echo "  • Open UI: http://localhost:3001"
echo "  • View API docs: http://localhost:8000/docs"
echo "  • Check creatives in dashboard"
