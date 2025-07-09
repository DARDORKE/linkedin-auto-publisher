#!/bin/bash

echo "🚀 Starting LinkedIn Auto Publisher..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please create it with your API keys."
    exit 1
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Build and start services
echo "🏗️ Building and starting services..."
docker-compose up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 15

# Check if services are running
echo "🔍 Checking services status..."
docker-compose ps

# Get container logs
echo "📝 Recent logs:"
docker-compose logs --tail=10

echo ""
echo "✅ Application started!"
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:5000"
echo ""
echo "📊 Useful commands:"
echo "  docker-compose logs -f           # View logs"
echo "  docker-compose down             # Stop services"
echo "  docker-compose restart          # Restart services"