"""
DCMX Tracing Decorators

Provides easy-to-use decorators for instrumenting DCMX functions and methods
with OpenTelemetry tracing.
"""

import functools
import time
import logging
from typing import Any, Callable, Optional, Dict
from inspect import iscoroutinefunction

from dcmx.observability.tracing import get_tracer, start_span, record_histogram, set_attribute


logger = logging.getLogger(__name__)


def traced(
    operation_name: Optional[str] = None,
    include_args: bool = True,
    include_result: bool = True,
    include_duration: bool = True,
):
    """
    Decorator to automatically trace a function or method

    Args:
        operation_name: Name for the span (defaults to function name)
        include_args: Include function arguments in span attributes
        include_result: Include function result in span attributes
        include_duration: Record function duration as histogram metric

    Example:
        @traced()
        def my_function(x, y):
            return x + y

        @traced(operation_name="custom_operation")
        async def my_async_function():
            pass
    """

    def decorator(func: Callable) -> Callable:
        span_name = operation_name or f"{func.__module__}.{func.__name__}"

        if iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                with start_span(span_name) as span:
                    start_time = time.time()

                    if include_args:
                        span.set_attribute("function.args.count", len(args))
                        span.set_attribute("function.kwargs.count", len(kwargs))
                        for i, arg in enumerate(args[:5]):  # Limit to 5 args
                            try:
                                span.set_attribute(f"arg.{i}", str(arg)[:100])
                            except (TypeError, ValueError):
                                pass

                    try:
                        result = await func(*args, **kwargs)

                        if include_result:
                            try:
                                span.set_attribute("function.result", str(result)[:100])
                            except (TypeError, ValueError):
                                pass

                        if include_duration:
                            duration_ms = (time.time() - start_time) * 1000
                            record_histogram(
                                f"{span_name}.duration_ms",
                                duration_ms,
                                {"status": "success"}
                            )

                        return result

                    except Exception as e:
                        span.set_attribute("exception.type", type(e).__name__)
                        span.set_attribute("exception.message", str(e)[:100])
                        span.set_attribute("status", "error")

                        if include_duration:
                            duration_ms = (time.time() - start_time) * 1000
                            record_histogram(
                                f"{span_name}.duration_ms",
                                duration_ms,
                                {"status": "error"}
                            )

                        raise

            return async_wrapper

        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                with start_span(span_name) as span:
                    start_time = time.time()

                    if include_args:
                        span.set_attribute("function.args.count", len(args))
                        span.set_attribute("function.kwargs.count", len(kwargs))
                        for i, arg in enumerate(args[:5]):
                            try:
                                span.set_attribute(f"arg.{i}", str(arg)[:100])
                            except (TypeError, ValueError):
                                pass

                    try:
                        result = func(*args, **kwargs)

                        if include_result:
                            try:
                                span.set_attribute("function.result", str(result)[:100])
                            except (TypeError, ValueError):
                                pass

                        if include_duration:
                            duration_ms = (time.time() - start_time) * 1000
                            record_histogram(
                                f"{span_name}.duration_ms",
                                duration_ms,
                                {"status": "success"}
                            )

                        return result

                    except Exception as e:
                        span.set_attribute("exception.type", type(e).__name__)
                        span.set_attribute("exception.message", str(e)[:100])
                        span.set_attribute("status", "error")

                        if include_duration:
                            duration_ms = (time.time() - start_time) * 1000
                            record_histogram(
                                f"{span_name}.duration_ms",
                                duration_ms,
                                {"status": "error"}
                            )

                        raise

            return sync_wrapper

    return decorator


def traced_method(
    operation_name: Optional[str] = None,
    include_args: bool = False,
    include_result: bool = False,
):
    """
    Decorator for class methods (doesn't include self in attributes)

    Args:
        operation_name: Name for the span
        include_args: Include method arguments (excluding self)
        include_result: Include method result in span attributes

    Example:
        class MyClass:
            @traced_method()
            def my_method(self, x):
                return x * 2
    """

    def decorator(func: Callable) -> Callable:
        span_name = operation_name or f"{func.__qualname__}"

        if iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(self, *args, **kwargs) -> Any:
                with start_span(span_name) as span:
                    span.set_attribute("class", self.__class__.__name__)

                    if include_args:
                        span.set_attribute("method.args.count", len(args))
                        span.set_attribute("method.kwargs.count", len(kwargs))

                    try:
                        result = await func(self, *args, **kwargs)

                        if include_result:
                            try:
                                span.set_attribute("method.result", str(result)[:100])
                            except (TypeError, ValueError):
                                pass

                        return result

                    except Exception as e:
                        span.set_attribute("exception.type", type(e).__name__)
                        span.record_exception(e)
                        raise

            return async_wrapper

        else:
            @functools.wraps(func)
            def sync_wrapper(self, *args, **kwargs) -> Any:
                with start_span(span_name) as span:
                    span.set_attribute("class", self.__class__.__name__)

                    if include_args:
                        span.set_attribute("method.args.count", len(args))
                        span.set_attribute("method.kwargs.count", len(kwargs))

                    try:
                        result = func(self, *args, **kwargs)

                        if include_result:
                            try:
                                span.set_attribute("method.result", str(result)[:100])
                            except (TypeError, ValueError):
                                pass

                        return result

                    except Exception as e:
                        span.set_attribute("exception.type", type(e).__name__)
                        span.record_exception(e)
                        raise

            return sync_wrapper

    return decorator
