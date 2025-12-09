#!/usr/bin/env python
"""
DCMX Tracing Quick Start

This script demonstrates the quickest way to get started with distributed tracing
for DCMX operations.
"""

import asyncio
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def main():
    """Quick start guide for DCMX tracing"""

    print("\n" + "=" * 80)
    print("  DCMX Distributed Tracing - Quick Start Guide")
    print("=" * 80)
    print()

    # Step 1: Check prerequisites
    print("📋 Step 1: Checking prerequisites...")
    print()

    try:
        import opentelemetry
        print("  ✅ OpenTelemetry installed")
    except ImportError:
        print("  ❌ OpenTelemetry not installed")
        print("     Run: pip install -r requirements-tracing.txt")
        return

    try:
        import docker
        client = docker.from_env()
        print("  ✅ Docker available")
    except Exception:
        print("  ⚠️  Docker not available (optional)")

    print()

    # Step 2: Start infrastructure
    print("📋 Step 2: Starting tracing infrastructure...")
    print()
    print("  Run these commands in a terminal:")
    print("  $ chmod +x scripts/start-tracing.sh")
    print("  $ ./scripts/start-tracing.sh")
    print()
    print("  Or:")
    print("  $ docker-compose -f docker-compose.tracing.yml up -d")
    print()

    # Step 3: Initialize tracer
    print("📋 Step 3: Initializing tracer...")
    print()

    try:
        from dcmx.observability import DCMXTracer, DCMXTracingConfig

        config = DCMXTracingConfig(
            service_name="dcmx-quickstart",
            otlp_endpoint="http://localhost:4318",
        )
        tracer = DCMXTracer.init(config)
        print("  ✅ Tracer initialized successfully")
        print()
    except Exception as e:
        print(f"  ❌ Error initializing tracer: {e}")
        print()
        return

    # Step 4: Trace a simple operation
    print("📋 Step 4: Tracing a simple operation...")
    print()

    try:
        from dcmx.observability import start_span, record_counter, set_attribute

        with start_span("quick_start_operation") as span:
            span.set_attribute("operation.type", "quickstart")
            span.set_attribute("step", 1)
            record_counter("operations.started", 1)

            # Simulate work
            await asyncio.sleep(0.1)

            span.set_attribute("step", 2)
            record_counter("operations.completed", 1)

        print("  ✅ Operation traced successfully")
        print()
    except Exception as e:
        print(f"  ❌ Error tracing operation: {e}")
        print()
        return

    # Step 5: Use decorator
    print("📋 Step 5: Using @traced decorator...")
    print()

    try:
        from dcmx.observability import traced

        @traced(operation_name="quickstart_function")
        async def my_function(x: int, y: int) -> int:
            await asyncio.sleep(0.05)
            return x + y

        result = await my_function(5, 3)
        print(f"  ✅ Function traced: {5} + {3} = {result}")
        print()
    except Exception as e:
        print(f"  ❌ Error using decorator: {e}")
        print()
        return

    # Step 6: View results
    print("📋 Step 6: Viewing traces...")
    print()
    print("  Open these URLs in your browser:")
    print()
    print("  🔍 Jaeger UI (traces):")
    print("     http://localhost:16686")
    print()
    print("  📊 Prometheus (metrics):")
    print("     http://localhost:9090")
    print()
    print("  📈 Grafana (dashboards):")
    print("     http://localhost:3000")
    print()

    # Step 7: Next steps
    print("📋 Step 7: Next steps...")
    print()
    print("  1. Read TRACING.md for complete documentation")
    print("  2. Run examples/tracing_example.py for more examples")
    print("  3. Integrate tracing into your code:")
    print()
    print("     from dcmx.observability import traced")
    print()
    print("     @traced()")
    print("     async def your_function():")
    print("         pass")
    print()

    # Shutdown
    print("=" * 80)
    print("✅ Quick start complete!")
    print("=" * 80)
    print()

    await tracer.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
