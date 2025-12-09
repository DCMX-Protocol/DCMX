#!/bin/bash
# Verify DCMX testnet deployment

set -e

DOCKER_COMPOSE_FILE=${1:-docker-compose.yml}

echo "================================"
echo "DCMX Testnet Verification"
echo "================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check service
check_service() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo -n "Checking $name... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo "000")
    
    if [ "$response" = "$expected_status" ]; then
        echo -e "${GREEN}✓${NC} (HTTP $response)"
        return 0
    else
        echo -e "${RED}✗${NC} (HTTP $response, expected $expected_status)"
        return 1
    fi
}

# Check Docker containers
echo "Container Status:"
docker-compose -f "$DOCKER_COMPOSE_FILE" ps

echo ""
echo "Service Health Checks:"
echo ""

# Node endpoints
check_service "DCMX Node 1" "http://localhost:8001/ping"
check_service "DCMX Node 2" "http://localhost:8002/ping"
check_service "DCMX Node 3" "http://localhost:8003/ping"

# Compliance
check_service "Compliance Monitor" "http://localhost:9001/health"

# Monitoring
check_service "Prometheus" "http://localhost:9090/-/healthy"
check_service "Grafana" "http://localhost:3000/api/health"

echo ""
echo "Peer Discovery:"
echo ""

# Check peer connectivity
echo -n "Node 1 Peers: "
peers=$(curl -s http://localhost:8001/peers | grep -o '"peer_id"' | wc -l || echo "0")
echo "$peers"

echo -n "Node 2 Peers: "
peers=$(curl -s http://localhost:8002/peers | grep -o '"peer_id"' | wc -l || echo "0")
echo "$peers"

echo -n "Node 3 Peers: "
peers=$(curl -s http://localhost:8003/peers | grep -o '"peer_id"' | wc -l || echo "0")
echo "$peers"

echo ""
echo "Storage Status:"
echo ""

# Check storage
for node in node-1 node-2 node-3; do
    container="dcmx-$node"
    size=$(docker exec "$container" du -sh /var/lib/dcmx 2>/dev/null | cut -f1 || echo "N/A")
    echo "Node $node storage: $size"
done

echo ""
echo "Database Status:"
echo ""

# Check database
echo -n "PostgreSQL: "
pg_status=$(docker exec dcmx-compliance-db pg_isready -U compliance 2>/dev/null && echo "Ready" || echo "Not Ready")
echo "$pg_status"

echo -n "Redis: "
redis_status=$(docker exec dcmx-compliance-cache redis-cli ping 2>/dev/null || echo "Not Ready")
echo "$redis_status"

echo ""
echo "Network Statistics:"
echo ""

# Network stats
docker stats --no-stream

echo ""
echo "================================"
echo "Verification Complete"
echo "================================"
