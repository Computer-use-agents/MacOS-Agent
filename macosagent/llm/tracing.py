import functools
import logging
import os
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

ENABLE_TRACING = os.getenv("ENABLE_TRACING", "false").lower() == "true"
logger.warning(f"ENABLE_TRACING: {ENABLE_TRACING}")
if ENABLE_TRACING:
    from langfuse.callback import CallbackHandler

    langfuse_handler = CallbackHandler(
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        host=os.getenv("LANGFUSE_HOST"),
    )
    from langfuse.openai import openai

else:
    langfuse_handler = None
    import openai  # noqa: F401

def trace_with_metadata(
        name: str | None = None,
        custom_id: str | None = None,
        tags: list[str] | None = None,
        observation_name: str | None = None):
    """
    A decorator that adds tracing with metadata to a function.
    If tracing is disabled, the function will execute normally without tracing.
    
    Args:
        name (Optional[str]): The name of the trace
        custom_id (Optional[str]): A custom identifier to be added to the trace metadata
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not ENABLE_TRACING:
                return func(*args, **kwargs)

            # Create metadata with custom_id if provided
            metadata = {"custom_id": custom_id} if custom_id else {}

            # Use the observe decorator from langfuse with metadata
            from langfuse.decorators import langfuse_context, observe
            @observe
            def traced_func(*args: Any, **kwargs: Any) -> Any:
                if len(metadata) > 0:
                    langfuse_context.update_current_trace(metadata=metadata)
                if name:
                    langfuse_context.update_current_trace(name=name)
                if tags is not None and len(tags) > 0:
                    langfuse_context.update_current_trace(tags=tags)
                if observation_name:
                    langfuse_context.update_current_observation(name=observation_name)
                return func(*args, **kwargs)

            return traced_func(*args, **kwargs)

        return wrapper
    return decorator


def span_with_metadata(custom_id: str | None = None):
    """
    A decorator that adds span with metadata to a function.
    If tracing is disabled, the function will execute normally without tracing.
    
    Args:
        custom_id (Optional[str]): A custom identifier to be added to the trace metadata
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not ENABLE_TRACING:
                return func(*args, **kwargs)

            # Create metadata with custom_id if provided
            metadata = {"custom_id": custom_id} if custom_id else {}

            # Use the observe decorator from langfuse with metadata
            from langfuse.decorators import langfuse_context, observe
            @observe
            def traced_func(*args: Any, **kwargs: Any) -> Any:
                langfuse_context.update_current_trace(metadata=metadata)
                return func(*args, **kwargs)

            return traced_func(*args, **kwargs)

        return wrapper
    return decorator

