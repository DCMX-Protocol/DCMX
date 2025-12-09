# DCMX Distributed Tracing Guide

**Status**: ✅ Production Ready  
**Framework**: OpenTelemetry + Jaeger  
**Endpoint**: `http://localhost:4318` (HTTP) / `http://localhost:4317` (gRPC)

---

## Overview

DCMX now includes comprehensive distributed tracing using OpenTelemetry, enabling visualization of:
- **Agent Operations**: Track artist onboarding, NFT minting, royalty distribution
- **Performance Metrics**: Duration, latency, throughput of operations
- **Error Tracking**: Exceptions, failures, and error propagation
- **Dependency Tracing**: HTTP calls, blockchain operations, database queries
- **Multi-step Workflows**: Trace complex operations across multiple services

---

## Quick Start (5 Minutes)

### 1. Start Tracing Infrastructure

```bash
# Make script executable
chmod +x scripts/start-tracing.sh

# Start Jaeger, Prometheus, and Grafana
./scripts/start-tracing.sh
```

Or manually:
```bash
docker-compose -f docker-compose.tracing.yml up -d
```

### 2. Install Dependencies

```bash
pip install -r requirements-tracing.txt
```

### 3. Initialize Tracing in Your Code

```python
from dcmx.observability import DCMXTracer, DCMXTracingConfig

# Initialize at application startup
config = DCMXTracingConfig(
    service_name="dcmx",
    otlp_endpoint="http://localhost:4318"
)
tracer = DCMXTracer.init(config)
```

### 4. View Traces

Open Jaeger UI: **http://localhost:16686**

---

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    DCMX Application                         │
│                                                             │
│  @traced()          @traced_method()      Manual spans      │
│  Decorators         Decorators            start_span()      │
│         └───────────┬───────────────┬────────┘               │
│                     │               │                       │
│         ┌───────────▼───────────────▼────────┐              │
│         │   OpenTelemetry SDK                │              │
│         │ (dcmx.observability.tracing)       │              │
│         └────────────┬──────────────────────┘               │
│                      │                                      │
│         ┌────────────▼──────────────┐                       │
│         │  OTLP Exporter            │                       │
│         │  (gRPC or HTTP)           │                       │
│         └────────────┬──────────────┘                       │
└─────────────────────┼──────────────────────────────────────┘
                      │ Traces & Metrics
                      │ (gRPC on :4317, HTTP on :4318)
                      │
          ┌───────────▼──────────────┐
          │      Jaeger Collector    │
          │  (localhost:4317/4318)   │
          └───────┬──────────┬───────┘
                  │          │
         ┌────────▼─┐    ┌──▼───────┐
         │ Jaeger   │    │ Prometheus│
         │ Backend  │    │ Exporter  │
         │ (Storage)│    │           │
         └────┬─────┘    └──┬────────┘
              │             │
         ┌────▼─────┐   ┌───▼────────┐
         │  Jaeger  │   │ Prometheus │
         │   UI     │   │   Server   │
         │ :16686   │   │   :9090    │
         └──────────┘   └────┬───────┘
                              │
                         ┌────▼───────┐
                         │  Grafana   │
                         │ Dashboards │
                         │   :3000    │
                         └────────────┘
```

---

## Using Tracing

### 1. Automatic Instrumentation (Decorators)

#### For Functions

```python
from dcmx.observability import traced

@traced(
    operation_name="custom_operation",
    include_args=True,           # Include function arguments
    include_result=True,         # Include return value
    include_duration=True,       # Record duration metric
)
async def my_operation(x, y):
    return x + y
```

#### For Class Methods

```python
from dcmx.observability import traced_method

class MyClass:
    @traced_method(
        operation_name="custom_method",
        include_args=False,  # Don't include args for security
        include_result=True,
    )
    async def my_method(self):
        return "result"
```

### 2. Manual Span Creation

```python
from dcmx.observability import start_span, set_attribute, add_event, record_counter

# Create a named span
with start_span("operation_name") as span:
    # Set attributes
    set_attribute("user.id", "user_123")
    set_attribute("operation.status", "in_progress")
    
    # Add events
    add_event("step_1_complete", {"step": 1})
    
    # Record metrics
    record_counter("operations.total", 1)
    
    # Your code here
    result = perform_operation()
    
    # Update status
    set_attribute("operation.status", "completed")
```

### 3. Nested Spans

```python
from dcmx.observability import start_span

with start_span("parent_operation") as parent_span:
    parent_span.set_attribute("parent.id", "p_123")
    
    # Child spans are automatically linked
    with start_span("child_operation_1") as child1:
        child1.set_attribute("child.order", 1)
        # Work here
    
    with start_span("child_operation_2") as child2:
        child2.set_attribute("child.order", 2)
        # Work here
```

---

## Real-World Examples

### Example 1: Artist Onboarding

```python
from dcmx.observability import traced, start_span, record_counter, set_attribute

@traced(operation_name="artist_onboarding")
async def onboard_artist(artist_data):
    """Complete artist onboarding with tracing"""
    
    # Step 1: Verify identity
    with start_span("verify_identity") as span:
        span.set_attribute("artist.id", artist_data['id'])
        is_verified = await verify_identity(artist_data)
        span.set_attribute("verification.status", "verified" if is_verified else "failed")
        record_counter("artist.verifications", 1)
    
    # Step 2: Connect wallet
    with start_span("connect_wallet") as span:
        wallet = await connect_wallet(artist_data['wallet_address'])
        span.set_attribute("wallet.address", wallet.address)
        record_counter("wallet.connections", 1)
    
    # Step 3: Award badge
    with start_span("award_badge") as span:
        badge = await award_dcmx_badge(artist_data['id'])
        span.set_attribute("badge.id", badge.id)
        record_counter("badges.awarded", 1)
    
    return {"artist_id": artist_data['id'], "verified": True}
```

### Example 2: NFT Minting with Watermark Verification

```python
from dcmx.observability import traced, start_span, record_histogram

@traced(operation_name="nft_minting_workflow")
async def mint_nft(artist_id: str, track_data: dict):
    """Mint NFT with watermark verification"""
    
    # Verify watermark
    with start_span("verify_watermark") as span:
        watermark_valid, confidence = await verify_watermark(track_data)
        span.set_attribute("watermark.valid", watermark_valid)
        span.set_attribute("watermark.confidence", confidence)
        record_histogram("watermark.confidence_score", confidence)
    
    # Verify ZK proof
    with start_span("verify_zk_proof") as span:
        proof_valid = await verify_zk_proof(track_data['proof_chain_id'])
        span.set_attribute("proof.valid", proof_valid)
    
    # Mint on blockchain
    with start_span("blockchain_mint") as span:
        tx_hash, token_id = await mint_on_chain(artist_id, track_data)
        span.set_attribute("tx.hash", tx_hash)
        span.set_attribute("nft.token_id", token_id)
        span.set_attribute("nft.status", "minted")
    
    return {"token_id": token_id, "tx_hash": tx_hash}
```

### Example 3: Secondary Market Royalty Distribution

```python
from dcmx.observability import traced, start_span, record_counter, record_histogram

@traced(operation_name="secondary_market_royalty")
async def handle_secondary_sale(token_id: str, sale_data: dict):
    """Detect and process secondary market sale"""
    
    # Detect marketplace
    with start_span("detect_marketplace") as span:
        marketplace = await detect_marketplace(sale_data)
        span.set_attribute("marketplace.name", marketplace)
    
    # Calculate royalty
    with start_span("calculate_royalty") as span:
        royalty_amount = sale_data['price'] * 0.05  # 5% royalty
        span.set_attribute("royalty.amount", royalty_amount)
        span.set_attribute("royalty.percentage", 5.0)
        record_histogram("royalty.amounts", royalty_amount)
    
    # Distribute
    with start_span("distribute_royalty") as span:
        tx_hash = await distribute_to_artist(token_id, royalty_amount)
        span.set_attribute("tx.hash", tx_hash)
        span.set_attribute("distribution.status", "completed")
        record_counter("royalties.distributed", 1)
    
    return {"royalty": royalty_amount, "tx_hash": tx_hash}
```

---

## Metrics

### Available Metrics

```python
from dcmx.observability import record_counter, record_histogram

# Counters (increment by 1 or more)
record_counter("artist.verifications", 1)
record_counter("wallet.connections.total", 1)
record_counter("nft.mints.total", 1)

# Histograms (record values for distribution analysis)
record_histogram("watermark.confidence_score", 0.98)
record_histogram("nft.mint.duration_ms", 1500)
record_histogram("royalty.amounts", 2.5)
```

### Common Metric Names

```
artist.verifications              # KYC verification count
wallet.connections                # Wallet connection count
nft.mints.total                   # Total NFTs minted
nft.mint.gas_used                 # Gas used per mint
nft.mint.duration_ms              # Mint operation duration
watermark.confidence_score        # Watermark verification confidence
zk_proofs.verified.total          # ZK proof verifications
royalties.distributed.total       # Royalty payments
royalty.amounts                   # Individual royalty amounts
marketplace.sales.detected        # Secondary market sales detected
```

---

## Attributes

### Standard Attributes for Spans

```python
# Artist-related
span.set_attribute("artist.id", "artist_123")
span.set_attribute("artist.verified", True)
span.set_attribute("artist.kyc_level", 2)

# NFT/Token-related
span.set_attribute("nft.token_id", "0x123abc")
span.set_attribute("nft.edition", 1)
span.set_attribute("nft.status", "minted")

# Wallet-related
span.set_attribute("wallet.address", "0x123...")
span.set_attribute("wallet.type", "metamask")
span.set_attribute("wallet.verified", True)

# Transaction-related
span.set_attribute("tx.hash", "0x456def")
span.set_attribute("tx.status", "confirmed")
span.set_attribute("tx.gas_used", 180000)

# Watermark-related
span.set_attribute("watermark.status", "valid")
span.set_attribute("watermark.confidence", 0.98)
span.set_attribute("watermark.tampered", False)

# Blockchain-related
span.set_attribute("blockchain.network", "polygon")
span.set_attribute("blockchain.chain_id", 137)
span.set_attribute("blockchain.rpc_url", "...")

# Error-related (automatic)
span.set_attribute("exception.type", "ValueError")
span.set_attribute("exception.message", "Invalid input")
```

---

## Viewing Traces

### Jaeger UI

Open http://localhost:16686

**Features:**
- Search traces by service, operation, tags
- View trace timeline and latency
- See span relationships and dependencies
- Identify bottlenecks and failures

**Example Queries:**
- Service: `dcmx`
- Operation: `artist_onboarding`
- Tags: `artist.id=artist_123`

### Prometheus

Open http://localhost:9090

**Available Metrics:**
- Request latency histograms
- Operation counters
- Error rates
- Custom business metrics

### Grafana

Open http://localhost:3000 (admin/admin)

**Dashboards to Create:**
- DCMX Artist Operations
- NFT Minting Performance
- Royalty Distribution Metrics
- Error and Exception Tracking

---

## Production Configuration

### Environment Variables

```bash
# OTLP Endpoint
OTLP_ENDPOINT="http://jaeger-collector:4318"

# Service Name
OTEL_SERVICE_NAME="dcmx"

# Sample Rate (0.0 - 1.0)
OTEL_TRACES_SAMPLER_ARG="0.1"  # 10% sampling

# Resource Attributes
OTEL_RESOURCE_ATTRIBUTES="environment=production,region=us-east-1"
```

### Docker Compose Override

```yaml
# docker-compose.tracing.prod.yml
version: '3.8'

services:
  jaeger:
    environment:
      COLLECTOR_OTLP_ENABLED: "true"
      SPAN_STORAGE_TYPE: "badger"
      BADGER_EPHEMERAL: "false"
    volumes:
      - jaeger-data:/badger
```

### Kubernetes Deployment

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: dcmx-tracing-config
data:
  otlp-endpoint: "jaeger-collector.observability:4317"
  sample-rate: "0.1"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dcmx
spec:
  template:
    spec:
      containers:
      - name: dcmx
        env:
        - name: OTLP_ENDPOINT
          valueFrom:
            configMapKeyRef:
              name: dcmx-tracing-config
              key: otlp-endpoint
```

---

## Performance Impact

### Overhead

- **Memory**: ~50-100 MB for tracer and exporter
- **CPU**: <1% for normal operations
- **Network**: ~1-10 KB per span (depends on attributes)
- **Latency**: <10ms per span creation

### Optimization Tips

1. **Sampling**: Use sampling for high-volume operations
   ```python
   config = DCMXTracingConfig(sample_rate=0.1)  # 10% sampling
   ```

2. **Batch Export**: Already enabled by default
   - Batches spans before sending
   - Reduces network overhead

3. **Selective Instrumentation**: Don't trace everything
   ```python
   @traced(include_args=False, include_result=False)  # Minimal overhead
   ```

---

## Troubleshooting

### No Traces in Jaeger

1. **Check Jaeger is running**:
   ```bash
   docker ps | grep jaeger
   ```

2. **Check OTLP endpoint is correct**:
   ```python
   config = DCMXTracingConfig(otlp_endpoint="http://localhost:4318")
   ```

3. **Check logs**:
   ```bash
   docker-compose -f docker-compose.tracing.yml logs jaeger
   ```

### High Memory Usage

- Reduce sample rate
- Decrease batch size
- Check for memory leaks in span attributes

### Missing Metrics

- Enable Prometheus in compose file
- Check `prometheus.yml` scrape configs
- Verify metrics are being recorded

---

## Best Practices

### 1. Name Spans Clearly

```python
# Good
@traced(operation_name="artist_kyc_verification")

# Bad
@traced(operation_name="verify")
```

### 2. Use Attributes Consistently

```python
# Good - consistent naming
span.set_attribute("artist.id", artist_id)
span.set_attribute("artist.verified", True)

# Bad - inconsistent
span.set_attribute("artistId", artist_id)
span.set_attribute("is_verified", True)
```

### 3. Include Meaningful Context

```python
# Good
with start_span("blockchain_mint") as span:
    span.set_attribute("nft.token_id", token_id)
    span.set_attribute("blockchain.network", "polygon")
    span.set_attribute("tx.gas_price", gas_price)

# Bad
with start_span("mint") as span:
    pass  # No context
```

### 4. Don't Trace Sensitive Data

```python
# Bad - exposes private key
span.set_attribute("wallet.private_key", private_key)

# Good - only trace public data
span.set_attribute("wallet.address", wallet_address)
span.set_attribute("wallet.verified", True)
```

### 5. Use Hierarchical Span Names

```python
# Good - shows hierarchy
"artist_onboarding.verify_identity"
"artist_onboarding.connect_wallet"
"artist_onboarding.award_badge"

# Bad - no hierarchy
"verify"
"connect"
"award"
```

---

## Examples

### Run Tracing Examples

```bash
# Start tracing infrastructure
./scripts/start-tracing.sh

# Run example workflows
python examples/tracing_example.py

# View in Jaeger
# Open http://localhost:16686
# Filter by service: dcmx
# Filter by operation: artist_onboarding_workflow
```

### Integration with Phase 4

The `ArtistNFTMinter` in Phase 4 now includes tracing:

```python
from dcmx.blockchain.artist_nft_minter import ArtistNFTMinter

minter = ArtistNFTMinter(...)

# These methods automatically trace:
success, msg, minted = await minter.mint_artist_nft(request, metadata_uri)
success, msg, dist = await minter.distribute_primary_sale_royalty(mint_id, price)
success, msg, dist = await minter.handle_secondary_market_sale(...)
```

---

## Files

### Core Tracing
- `dcmx/observability/tracing.py` - Main tracer and configuration
- `dcmx/observability/decorators.py` - Tracing decorators
- `dcmx/observability/__init__.py` - Module exports

### Infrastructure
- `docker-compose.tracing.yml` - Jaeger, Prometheus, Grafana
- `prometheus.yml` - Prometheus configuration
- `scripts/start-tracing.sh` - Startup script

### Examples
- `examples/tracing_example.py` - Complete workflow examples

### Documentation
- `TRACING.md` - This file

---

## Resources

- **OpenTelemetry**: https://opentelemetry.io/
- **Jaeger**: https://www.jaegertracing.io/
- **Prometheus**: https://prometheus.io/
- **Grafana**: https://grafana.com/

---

## Support

For issues or questions about tracing:

1. Check Jaeger logs: `docker-compose -f docker-compose.tracing.yml logs jaeger`
2. Verify OTLP endpoint is accessible: `curl http://localhost:4318/status`
3. Check example output: `python examples/tracing_example.py`

---

**Status**: ✅ Production Ready - DCMX Distributed Tracing is fully implemented and ready to use!
