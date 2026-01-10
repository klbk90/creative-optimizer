#!/bin/bash

echo "🚀 Creative Optimizer - Full Setup & Start"
echo "=========================================="
echo ""

# 1. Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env from .env.local..."
    cp .env.local .env
fi

if [ ! -f frontend/.env ]; then
    echo "📝 Creating frontend/.env..."
    echo "VITE_API_URL=http://localhost:8000" > frontend/.env
fi

# 2. Start services
echo "🏗️  Starting Docker services..."
docker-compose down 2>/dev/null
docker-compose up -d postgres redis api frontend

# 3. Wait for services
echo "⏳ Waiting for services to start (15s)..."
sleep 15

# 4. Check health
echo "🏥 Checking API health..."
curl -s http://localhost:8000/health | python3 -m json.tool || echo "API starting..."
echo ""

# 5. Initialize DB and create test user
echo "👤 Creating test user..."
docker exec utm-api python3 -c "
from database.base import SessionLocal, init_db
from database.models import User, Base
import uuid

# Init DB tables
init_db()
print('✅ Database initialized')

# Create test user
db = SessionLocal()
test_user_id = uuid.UUID('00000000-0000-0000-0000-000000000001')
user = db.query(User).filter(User.id == test_user_id).first()

if not user:
    user = User(
        id=test_user_id,
        email='test@mvp.com',
        password_hash='dummy_hash_for_mvp',
        is_active=True
    )
    db.add(user)
    db.commit()
    print('✅ Test user created:', test_user_id)
else:
    print('✅ Test user already exists')

db.close()
" 2>&1

echo ""
echo "======================================"
echo "✅ Creative Optimizer MVP is READY!"
echo "======================================"
echo ""
echo "🌐 Access Points:"
echo "  • Frontend UI:      http://localhost:3001"
echo "  • API Docs:         http://localhost:8000/docs"
echo "  • Health Check:     http://localhost:8000/health"
echo ""
echo "🎯 ML Features:"
echo "  ✓ Markov Chain CVR prediction"
echo "  ✓ Thompson Sampling recommendations"
echo "  ✓ Pattern learning & auto-update"
echo ""
echo "📝 Quick Test:"
echo "  ./test-mvp.sh"
echo ""
echo "🛑 Stop:"
echo "  docker-compose down"
echo ""
echo "📊 View Logs:"
echo "  docker-compose logs -f api"
echo "  docker-compose logs -f frontend"
echo ""
