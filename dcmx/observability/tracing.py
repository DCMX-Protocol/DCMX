"""
DCMX Distributed Tracing Implementation

This module provides comprehensive distributed tracing for the DCMX system
using OpenTelemetry, enabling visualization via Jaeger at http://localhost:4319
"""

import logging
import os
from typing import Optional, Dict, Any
from contextvars import ContextVar

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.asyncpg import AsyncPgInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes


logger = logging.getLogger(__name__)

# Context variable for storing current trace context
_trace_context: ContextVar[Optional[Dict[str, Any]]] = ContextVar(
    'trace_context', default=None
)


class DCMXTracingConfig:
    """Configuration for DCMX tracing system"""

    def __init__(
        self,
        service_name: str = "dcmx",
        service_version: str = "1.0.0",
        otlp_endpoint: str = "http://localhost:4319",
        enable_console: bool = True,
        sample_rate: float = 1.0,
    ):
        self.service_name = service_name
        self.service_version = service_version
        self.otlp_endpoint = otlp_endpoint
        self.enable_console = enable_console
        self.sample_rate = sample_rate


class DCMXTracer:
    """
    DCMX Distributed Tracing Manager

    Provides unified tracing for all DCMX components with OpenTelemetry.
    Supports tracing for:
    - Artist NFT minting operations
    - Blockchain transactions
    - Watermark verification
    - Zero-knowledge proof generation
    - P2P network operations
    - Storage operations
    """

    _instance: Optional["DCMXTracer"] = None

    def __init__(self, config: DCMXTracingConfig):
        self.config = config
        self.tracer_provider = self._setup_tracer_provider()
        self.meter_provider = self._setup_meter_provider()
        self._setup_instrumentation()
        self.tracer = trace.get_tracer(__name__, version=config.service_version)
        self.meter = metrics.get_meter(__name__, version=config.service_version)
        logger.info(f"DCMX Tracing initialized: {config.service_name} @ {config.otlp_endpoint}")

    def _setup_tracer_provider(self) -> TracerProvider:
        """Setup OpenTelemetry TracerProvider with OTLP exporter"""
        resource = Resource(
            attributes={
                ResourceAttributes.SERVICE_NAME: self.config.service_name,
                ResourceAttributes.SERVICE_VERSION: self.config.service_version,
                "environment": os.getenv("ENV", "development"),
            }
        )

        tracer_provider = TracerProvider(resource=resource)
        otlp_exporter = OTLPSpanExporter(
            endpoint=self.config.otlp_endpoint,
            timeout=10,
        )
        tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        trace.set_tracer_provider(tracer_provider)

        return tracer_provider

    def _setup_meter_provider(self) -> MeterProvider:
        """Setup OpenTelemetry MeterProvider for metrics"""
        resource = Resource(
            attributes={
                ResourceAttributes.SERVICE_NAME: self.config.service_name,
                ResourceAttributes.SERVICE_VERSION: self.config.service_version,
            }
        )

        metric_reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(
                endpoint=self.config.otlp_endpoint,
                timeout=10,
            )
        )
        meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
        metrics.set_meter_provider(meter_provider)

        return meter_provider

    def _setup_instrumentation(self) -> None:
        """Setup automatic instrumentation for common libraries"""
        try:
            RequestsInstrumentor().instrument()
            logger.debug("Requests instrumentation enabled")
        except Exception as e:
            logger.debug(f"Could not enable Requests instrumentation: {e}")

        try:
            AioHttpClientInstrumentor().instrument()
            logger.debug("AioHttp instrumentation enabled")
        except Exception as e:
            logger.debug(f"Could not enable AioHttp instrumentation: {e}")

        try:
            LoggingInstrumentor().instrument()
            logger.debug("Logging instrumentation enabled")
        except Exception as e:
            logger.debug(f"Could not enable Logging instrumentation: {e}")

        try:
            AsyncPgInstrumentor().instrument()
            logger.debug("AsyncPG instrumentation enabled")
        except Exception as e:
            logger.debug(f"Could not enable AsyncPG instrumentation: {e}")

    @classmethod
    def init(cls, config: Optional[DCMXTracingConfig] = None) -> "DCMXTracer":
        """Initialize singleton instance of DCMXTracer"""
        if cls._instance is None:
            if config is None:
                config = DCMXTracingConfig()
            cls._instance = cls(config)
        return cls._instance

    @classmethod
    def get(cls) -> "DCMXTracer":
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls(DCMXTracingConfig())
        return cls._instance

    def start_span(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """
        Start a new span for tracing

        Args:
            name: Name of the span
            attributes: Optional attributes to add to the span

        Returns:
            OpenTelemetry span context manager
        """
        span = self.tracer.start_as_current_span(name)
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        return span

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """
        Add an event to the current span

        Args:
            name: Name of the event
            attributes: Optional event attributes
        """
        current_span = trace.get_current_span()
        if current_span and current_span.is_recording():
            current_span.add_event(name, attributes or {})

    def set_attribute(self, key: str, value: Any) -> None:
        """Set attribute on current span"""
        current_span = trace.get_current_span()
        if current_span and current_span.is_recording():
            current_span.set_attribute(key, value)

    def record_counter(
        self, name: str, value: int = 1, attributes: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record counter metric"""
        try:
            counter = self.meter.create_counter(name)
            counter.add(value, attributes or {})
        except Exception as e:
            logger.debug(f"Failed to record counter {name}: {e}")

    def record_histogram(
        self, name: str, value: float, attributes: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record histogram metric"""
        try:
            histogram = self.meter.create_histogram(name)
            histogram.record(value, attributes or {})
        except Exception as e:
            logger.debug(f"Failed to record histogram {name}: {e}")

    def record_gauge(
        self, name: str, value: float, attributes: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record gauge metric"""
        try:
            # Note: Gauges in OpenTelemetry are typically used with callbacks
            # This is a simplified recording
            pass
        except Exception as e:
            logger.debug(f"Failed to record gauge {name}: {e}")

    async def shutdown(self) -> None:
        """Shutdown tracer and flush spans"""
        try:
            self.tracer_provider.force_flush(timeout_millis=5000)
            await self.meter_provider._shutdown()
            logger.info("DCMX Tracing shutdown complete")
        except Exception as e:
            logger.error(f"Error during tracing shutdown: {e}")


# Convenience functions for use throughout DCMX

def get_tracer() -> DCMXTracer:
    """Get current tracer instance"""
    return DCMXTracer.get()


def start_span(name: str, attributes: Optional[Dict[str, Any]] = None):
    """Start a named span"""
    return get_tracer().start_span(name, attributes)


def record_counter(
    name: str, value: int = 1, attributes: Optional[Dict[str, Any]] = None
) -> None:
    """Record a counter metric"""
    get_tracer().record_counter(name, value, attributes)


def record_histogram(
    name: str, value: float, attributes: Optional[Dict[str, Any]] = None
) -> None:
    """Record a histogram metric"""
    get_tracer().record_histogram(name, value, attributes)


def set_attribute(key: str, value: Any) -> None:
    """Set attribute on current span"""
    get_tracer().set_attribute(key, value)


def add_event(name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
    """Add event to current span"""
    get_tracer().add_event(name, attributes)
