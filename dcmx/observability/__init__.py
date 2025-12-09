"""
DCMX Observability Module

Provides distributed tracing, metrics, and logging for all DCMX components.
"""

from dcmx.observability.tracing import (
    DCMXTracer,
    DCMXTracingConfig,
    get_tracer,
    start_span,
    record_counter,
    record_histogram,
    set_attribute,
    add_event,
)

from dcmx.observability.decorators import (
    traced,
    traced_method,
)

__all__ = [
    "DCMXTracer",
    "DCMXTracingConfig",
    "get_tracer",
    "start_span",
    "record_counter",
    "record_histogram",
    "set_attribute",
    "add_event",
    "traced",
    "traced_method",
]
