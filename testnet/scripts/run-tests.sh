#!/bin/bash
# Run integration tests on testnet

set -e

NODES=${NODES:-3}
DURATION=${DURATION:-"5m"}
RPS=${RPS:-10}
TEST_OUTPUT="test-results-$(date +%Y%m%d-%H%M%S).json"

echo "Starting DCMX Testnet Integration Tests"
echo "========================================"
echo "Nodes: $NODES"
echo "Duration: $DURATION"
echo "Requests/sec: $RPS"
echo ""

# Wait for services to be ready
echo "Waiting for services to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8001/ping > /dev/null 2>&1; then
        echo "✓ Services ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "✗ Services did not start in time"
        exit 1
    fi
    sleep 1
done

echo ""
echo "Running test suite..."
python -m pytest tests/ -v --tb=short \
    --json-report \
    --json-report-file="$TEST_OUTPUT" \
    || true

echo ""
echo "Test Results Summary:"
echo "===================="

# Parse and display results
if [ -f "$TEST_OUTPUT" ]; then
    python3 << EOF
import json
with open("$TEST_OUTPUT") as f:
    data = json.load(f)
    summary = data.get("summary", {})
    print(f"Total: {summary.get('total', 0)}")
    print(f"Passed: {summary.get('passed', 0)}")
    print(f"Failed: {summary.get('failed', 0)}")
    print(f"Skipped: {summary.get('skipped', 0)}")
    print(f"Duration: {summary.get('duration', 0):.2f}s")
EOF
fi

echo ""
echo "Load Testing..."
echo "==============="

# Simple load test using Apache Bench if available
if command -v ab &> /dev/null; then
    echo "Running load test on /tracks endpoint..."
    ab -n 1000 -c 10 -q http://localhost:8001/tracks || true
else
    echo "Apache Bench not found, skipping load test"
fi

echo ""
echo "Network Topology Test..."
echo "========================"

# Verify all nodes see each other
for i in {1..3}; do
    port=$((8000 + i))
    echo -n "Node $i peers: "
    curl -s "http://localhost:$port/peers" | grep -o '"peer_id"' | wc -l || echo "0"
done

echo ""
echo "Compliance Tests..."
echo "==================="

# Test KYC endpoint
echo -n "KYC verification: "
curl -s -X POST http://localhost:9001/kyc/verify \
    -H "Content-Type: application/json" \
    -d '{"user_id":"test-user","wallet":"0x1234567890abcdef"}' \
    | grep -o '"verified"' && echo "✓" || echo "✗"

# Test OFAC check
echo -n "OFAC check: "
curl -s http://localhost:9001/ofac/check?address=0x1234567890abcdef \
    | grep -o '"is_blocked"' && echo "✓" || echo "✗"

echo ""
echo "Storage Distribution Test..."
echo "============================="

# Check content distribution across nodes
for i in {1..3}; do
    port=$((8000 + i))
    echo -n "Node $i tracks: "
    curl -s "http://localhost:$port/tracks" | grep -o '"content_hash"' | wc -l || echo "0"
done

echo ""
echo "Test Summary saved to: $TEST_OUTPUT"
echo ""
echo "✓ Integration tests completed"
