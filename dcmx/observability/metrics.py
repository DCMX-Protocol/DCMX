"""
DCMX Application Metrics

Prometheus metrics for monitoring DCMX performance and health.
"""

import time
import logging
from functools import wraps
from typing import Callable
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, REGISTRY
from prometheus_client.core import CollectorRegistry

logger = logging.getLogger(__name__)

# Create custom registry
registry = CollectorRegistry()

# ============================================================================
# HTTP Metrics
# ============================================================================

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
    registry=registry
)

# ============================================================================
# Database Metrics
# ============================================================================

db_connections_active = Gauge(
    'db_connections_active',
    'Active database connections',
    registry=registry
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['query_type'],
    buckets=[0.001, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
    registry=registry
)

db_queries_total = Counter(
    'db_queries_total',
    'Total database queries',
    ['query_type', 'status'],
    registry=registry
)

# ============================================================================
# Blockchain Metrics
# ============================================================================

blockchain_blocks_indexed = Counter(
    'blockchain_blocks_indexed_total',
    'Total blockchain blocks indexed',
    ['network'],
    registry=registry
)

blockchain_last_indexed_block = Gauge(
    'blockchain_last_indexed_block_number',
    'Last indexed block number',
    ['network'],
    registry=registry
)

blockchain_last_indexed_block_timestamp = Gauge(
    'blockchain_last_indexed_block_timestamp',
    'Timestamp of last indexed block',
    ['network'],
    registry=registry
)

blockchain_transactions_processed = Counter(
    'blockchain_transactions_processed_total',
    'Total blockchain transactions processed',
    ['network', 'type'],
    registry=registry
)

# ============================================================================
# NFT Metrics
# ============================================================================

nft_mints_total = Counter(
    'nft_mints_total',
    'Total NFTs minted',
    ['artist'],
    registry=registry
)

nft_sales_total = Counter(
    'nft_sales_total',
    'Total NFT sales',
    registry=registry
)

nft_sales_volume = Counter(
    'nft_sales_volume_trx',
    'Total NFT sales volume in TRX',
    registry=registry
)

# ============================================================================
# Reward Metrics
# ============================================================================

rewards_distributed_total = Counter(
    'rewards_distributed_total',
    'Total rewards distributed',
    ['reward_type'],
    registry=registry
)

rewards_distributed_tokens = Counter(
    'rewards_distributed_tokens_total',
    'Total tokens distributed as rewards',
    ['reward_type'],
    registry=registry
)

# ============================================================================
# Auth Metrics
# ============================================================================

auth_attempts_total = Counter(
    'auth_attempts_total',
    'Total authentication attempts',
    ['result'],
    registry=registry
)

auth_failed_total = Counter(
    'auth_failed_total',
    'Total failed authentication attempts',
    registry=registry
)

active_sessions = Gauge(
    'active_sessions',
    'Number of active user sessions',
    registry=registry
)

# ============================================================================
# Business Metrics
# ============================================================================

active_users = Gauge(
    'active_users_total',
    'Total active users',
    registry=registry
)

active_artists = Gauge(
    'active_artists_total',
    'Total active artists',
    registry=registry
)

platform_revenue_trx = Counter(
    'platform_revenue_trx_total',
    'Total platform revenue in TRX',
    registry=registry
)

# ============================================================================
# Application Info
# ============================================================================

app_info = Info(
    'dcmx_app',
    'DCMX application information',
    registry=registry
)

app_info.info({
    'version': '1.0.0',
    'environment': 'production',
})

# ============================================================================
# Metric Decorators
# ============================================================================

def track_request_metrics(endpoint: str):
    """Decorator to track HTTP request metrics."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "500"
            
            try:
                result = await func(*args, **kwargs)
                status = "200"
                return result
            except Exception as e:
                status = "500"
                raise
            finally:
                duration = time.time() - start_time
                http_request_duration_seconds.labels(
                    method="POST",
                    endpoint=endpoint
                ).observe(duration)
                http_requests_total.labels(
                    method="POST",
                    endpoint=endpoint,
                    status=status
                ).inc()
        
        return wrapper
    return decorator


def track_db_query(query_type: str):
    """Decorator to track database query metrics."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "error"
            
            try:
                result = await func(*args, **kwargs)
                status = "success"
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                db_query_duration_seconds.labels(
                    query_type=query_type
                ).observe(duration)
                db_queries_total.labels(
                    query_type=query_type,
                    status=status
                ).inc()
        
        return wrapper
    return decorator


# ============================================================================
# Metrics Endpoint
# ============================================================================

def get_metrics() -> bytes:
    """Get Prometheus metrics in text format."""
    return generate_latest(registry)
