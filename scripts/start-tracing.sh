#!/bin/bash
# Start DCMX Distributed Tracing Infrastructure
# 
# This script sets up Jaeger, Prometheus, and Grafana for visualization
# of DCMX agent operations and performance metrics.

set -e

echo "═══════════════════════════════════════════════════════════════════════════════"
echo "  DCMX Distributed Tracing Setup"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "📦 Starting tracing infrastructure..."
echo ""

# Start services
docker-compose -f docker-compose.tracing.yml up -d

echo "✅ Tracing infrastructure started!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Service Endpoints:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  🔍 Jaeger UI (Trace Visualization):"
echo "     http://localhost:16686"
echo ""
echo "  📊 Prometheus (Metrics):"
echo "     http://localhost:9090"
echo ""
echo "  📈 Grafana (Dashboards):"
echo "     http://localhost:3000 (admin/admin)"
echo ""
echo "  📡 OTLP Endpoint (gRPC):"
echo "     http://localhost:4317"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 To use tracing in your DCMX code:"
echo ""
echo "  from dcmx.observability import DCMXTracer, DCMXTracingConfig"
echo ""
echo "  # Initialize tracer"
echo "  config = DCMXTracingConfig(otlp_endpoint='http://localhost:4318')"
echo "  tracer = DCMXTracer.init(config)"
echo ""
echo "  # Use decorator for automatic tracing"
echo "  from dcmx.observability import traced"
echo ""
echo "  @traced()"
echo "  async def your_function():"
echo "      pass"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🛑 To stop services:"
echo "   docker-compose -f docker-compose.tracing.yml down"
echo ""
echo "📝 To view logs:"
echo "   docker-compose -f docker-compose.tracing.yml logs -f"
echo ""
