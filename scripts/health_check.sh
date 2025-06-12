#!/bin/bash
# GreenLightPA Development Environment Health Check Script
# This script verifies that all services are running correctly

set -e

echo "🏥 GreenLightPA Development Environment Health Check"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Health check functions
check_service() {
    local service_name=$1
    local check_command=$2
    local expected_output=$3
    
    echo -n "🔍 Checking $service_name... "
    
    if eval "$check_command" &>/dev/null; then
        echo -e "${GREEN}✅ OK${NC}"
        return 0
    else
        echo -e "${RED}❌ FAILED${NC}"
        return 1
    fi
}

# Start health checks
echo "📦 Checking Docker services status..."
docker-compose ps

echo ""
echo "🌐 Testing service endpoints..."

# Check FastAPI
check_service "FastAPI Health" \
    "curl -f http://localhost:8000/health" \
    "healthy"

# Check N8n
check_service "N8n Web Interface" \
    "curl -f http://localhost:5678" \
    ""

# Check PostgreSQL
check_service "PostgreSQL Database" \
    "docker-compose exec -T postgres pg_isready -U greenlight_user" \
    "accepting connections"

# Check Redis
check_service "Redis Cache" \
    "docker-compose exec -T redis redis-cli ping" \
    "PONG"

# Check ChromaDB
check_service "ChromaDB Vector Database" \
    "curl -f http://localhost:8001/api/v2/heartbeat" \
    ""

echo ""
echo "🔐 Testing database connections..."

# Test main database connection
echo -n "🐘 Testing main database connection... "
if docker-compose exec -T postgres psql -U greenlight_user -d greenlightpa_dev -c "SELECT 1;" &>/dev/null; then
    echo -e "${GREEN}✅ Connected${NC}"
else
    echo -e "${RED}❌ Connection failed${NC}"
fi

# Test N8n database connection
echo -n "⚙️ Testing N8n database connection... "
if docker-compose exec -T postgres psql -U greenlight_user -d n8n -c "SELECT 1;" &>/dev/null; then
    echo -e "${GREEN}✅ Connected${NC}"
else
    echo -e "${RED}❌ Connection failed${NC}"
fi

# Test vector extension
echo -n "🧠 Testing pgvector extension... "
if docker-compose exec -T postgres psql -U greenlight_user -d greenlightpa_dev -c "SELECT 1 FROM pg_extension WHERE extname = 'vector';" | grep -q "1"; then
    echo -e "${GREEN}✅ Installed${NC}"
else
    echo -e "${RED}❌ Not installed${NC}"
fi

echo ""
echo "📊 Resource usage check..."

# Check Docker resource usage
echo "🐳 Docker resource usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

echo ""
echo "💾 Volume status:"
docker volume ls | grep greenlightpa

echo ""
echo "🔧 Testing API endpoints..."

# Test FastAPI endpoints if available
echo -n "📋 Testing API documentation... "
if curl -f http://localhost:8000/docs &>/dev/null; then
    echo -e "${GREEN}✅ Available${NC}"
else
    echo -e "${YELLOW}⚠️ Not available${NC}"
fi

echo -n "🔍 Testing health endpoint details... "
health_response=$(curl -s http://localhost:8000/health 2>/dev/null || echo "failed")
if [[ "$health_response" == *"healthy"* ]]; then
    echo -e "${GREEN}✅ Healthy${NC}"
    echo "   Response: $health_response"
else
    echo -e "${RED}❌ Unhealthy${NC}"
    echo "   Response: $health_response"
fi

echo ""
echo "📁 Checking file permissions..."

# Check important directories
directories=("./data" "./logs" "./config")
for dir in "${directories[@]}"; do
    if [ -d "$dir" ]; then
        echo -n "📂 Checking $dir permissions... "
        if [ -r "$dir" ] && [ -w "$dir" ]; then
            echo -e "${GREEN}✅ OK${NC}"
        else
            echo -e "${YELLOW}⚠️ Check permissions${NC}"
        fi
    fi
done

echo ""
echo "🧪 Running basic integration tests..."

# Test if we can run pytest
echo -n "🔬 Testing pytest availability... "
if docker-compose exec -T app python -c "import pytest; print('pytest available')" &>/dev/null; then
    echo -e "${GREEN}✅ Available${NC}"
    
    # Run a quick test if tests directory exists
    if docker-compose exec -T app test -d tests; then
        echo "🧪 Running basic tests..."
        docker-compose exec -T app pytest tests/test_health.py -v --tb=short 2>/dev/null || echo -e "${YELLOW}⚠️ No health tests found${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ Not available${NC}"
fi

echo ""
echo "🌍 Network connectivity test..."

# Test external connectivity
echo -n "🌐 Testing external connectivity... "
if docker-compose exec -T app python -c "import requests; requests.get('https://httpbin.org/get', timeout=5)" &>/dev/null; then
    echo -e "${GREEN}✅ Connected${NC}"
else
    echo -e "${YELLOW}⚠️ Limited connectivity${NC}"
fi

echo ""
echo "📋 Environment variables check..."

# Check critical environment variables
critical_vars=("DATABASE_URL" "REDIS_URL" "SECRET_KEY")
for var in "${critical_vars[@]}"; do
    echo -n "🔑 Checking $var... "
    if docker-compose exec -T app printenv "$var" &>/dev/null; then
        echo -e "${GREEN}✅ Set${NC}"
    else
        echo -e "${RED}❌ Missing${NC}"
    fi
done

echo ""
echo "📝 Generating health report summary..."

# Count successful checks
total_services=5
successful_services=0

services=("FastAPI:8000" "N8n:5678" "PostgreSQL:5432" "Redis:6379" "ChromaDB:8001")
for service in "${services[@]}"; do
    name=$(echo "$service" | cut -d':' -f1)
    port=$(echo "$service" | cut -d':' -f2)
    
    if curl -f "http://localhost:$port" &>/dev/null || \
       ([ "$name" = "PostgreSQL" ] && docker-compose exec -T postgres pg_isready -U greenlight_user &>/dev/null) || \
       ([ "$name" = "Redis" ] && docker-compose exec -T redis redis-cli ping &>/dev/null); then
        ((successful_services++))
    fi
done

echo ""
echo "📊 Health Check Summary:"
echo "======================="
echo "Services healthy: $successful_services/$total_services"

if [ $successful_services -eq $total_services ]; then
    echo -e "${GREEN}🎉 All services are healthy and ready for development!${NC}"
    echo ""
    echo "🚀 Quick access links:"
    echo "   • FastAPI Docs: http://localhost:8000/docs"
    echo "   • N8n Workflows: http://localhost:5678"
    echo "   • pgAdmin: http://localhost:5050"
    echo ""
    echo "📚 Next steps:"
    echo "   1. Start developing: Open your IDE and begin coding"
    echo "   2. Run tests: docker-compose exec app pytest tests/"
    echo "   3. View logs: docker-compose logs -f"
    exit 0
else
    echo -e "${YELLOW}⚠️ Some services may need attention. Check the output above.${NC}"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "   1. Try restarting: docker-compose restart"
    echo "   2. Check logs: docker-compose logs [service_name]"
    echo "   3. Rebuild: docker-compose down && docker-compose up --build"
    exit 1
fi 