#!/bin/bash

echo "🚀 Starting Creative Optimizer MVP..."

# Check if .env exists, if not copy from .env.local
if [ ! -f .env ]; then
    echo "📝 Creating .env from .env.local..."
    cp .env.local .env
fi

# Check if frontend/.env exists
if [ ! -f frontend/.env ]; then
    echo "📝 Creating frontend/.env..."
    echo "VITE_API_URL=http://localhost:8000" > frontend/.env
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Build and start services
echo "🏗️  Building and starting services..."
docker-compose up -d postgres redis api frontend

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 15

# Check health
echo "🏥 Checking service health..."
curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || echo "API starting..."

echo ""
echo "✅ Creative Optimizer MVP is running!"
echo ""
echo "📊 Frontend UI:    http://localhost:3001"
echo "🔧 API Docs:       http://localhost:8000/docs"
echo "💚 Health Check:   http://localhost:8000/health"
echo ""
echo "MVP Features:"
echo "  • Upload creatives with campaign tags"
echo "  • Manual metrics tracking"
echo "  • Simple analytics"
echo ""
echo "Commands:"
echo "  Stop:       docker-compose down"
echo "  Logs API:   docker-compose logs -f api"
echo "  Logs UI:    docker-compose logs -f frontend"
echo "  Restart:    docker-compose restart api frontend"
