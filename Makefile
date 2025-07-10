.PHONY: help build up down logs restart clean deploy redeploy status check install

help:
	@echo "LinkedIn Auto Publisher - Docker Commands"
	@echo "======================================="
	@echo "make build      - Build Docker images"
	@echo "make up         - Start application"
	@echo "make down       - Stop application"
	@echo "make deploy     - Full deployment (build + up)"
	@echo "make redeploy   - Redeploy (down + build + up)"
	@echo "make logs       - View logs"
	@echo "make restart    - Restart application"
	@echo "make status     - Show container status"
	@echo "make check      - Check if services are running"
	@echo "make install    - Install dependencies and setup"
	@echo "make clean      - Clean up containers and volumes"

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

restart:
	docker-compose restart

# Deployment commands
deploy: build up
	@echo "✅ Application deployed successfully!"
	@echo "Frontend: http://localhost:3000"
	@echo "Backend API: http://localhost:5000"
	@echo "API Docs: http://localhost:5000/docs/"

redeploy: down build up
	@echo "✅ Application redeployed successfully!"


# Status and monitoring
status:
	docker-compose ps

check:
	@echo "Checking services..."
	@curl -s http://localhost:5000/health > /dev/null && echo "✅ Backend is running" || echo "❌ Backend is down"
	@curl -s http://localhost:3000 > /dev/null && echo "✅ Frontend is running" || echo "❌ Frontend is down"

# Installation and setup
install:
	@echo "Setting up LinkedIn Auto Publisher..."
	@if [ ! -f .env ]; then \
		echo "Creating .env file..."; \
		echo "GEMINI_API_KEY=your_gemini_api_key_here" > .env; \
		echo "⚠️  Please edit .env and add your GEMINI_API_KEY"; \
	fi
	@mkdir -p data logs
	@chmod +x scripts/init-db.sh
	@echo "✅ Setup complete! Run 'make deploy' to start the application"

# Cleanup
clean:
	docker-compose down -v
	docker system prune -f
	rm -rf data/*.db logs/*.log