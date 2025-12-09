#!/bin/bash
# Cleanup testnet deployment

set -e

FULL_CLEANUP=${1:-"--full"}

echo "DCMX Testnet Cleanup"
echo "===================="
echo ""

if [ "$FULL_CLEANUP" = "--full" ]; then
    echo "Performing FULL cleanup (includes volumes)..."
    docker-compose down -v
    echo "✓ All containers and volumes removed"
else
    echo "Performing standard cleanup (containers only)..."
    docker-compose down
    echo "✓ Containers stopped and removed"
    echo "Data volumes preserved"
fi

echo ""
echo "Cleanup complete"
