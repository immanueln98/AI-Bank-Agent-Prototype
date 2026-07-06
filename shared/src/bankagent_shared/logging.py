"""Structured logging (structlog) with PII redaction built into the pipeline.

Every log line passes through :func:`pii_redaction_processor` before rendering,
so account/ID numbers never reach the console or log files even if a call site
forgets to mask. Known-value masking (session-specific) still happens at call
sites; this processor is the regex safety net.
"""

from __future__ import annotations

import logging
from collections.abc import MutableMapping
from typing import Any, Literal

import structlog

from .redaction import mask_mapping

LogFormat = Literal["console", "json"]


def pii_redaction_processor(
    _logger: Any, _method_name: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    return {k: mask_mapping(v) for k, v in event_dict.items()}


def configure_logging(service: str, fmt: LogFormat = "console") -> None:
    renderer: Any = (
        structlog.processors.JSONRenderer() if fmt == "json" else structlog.dev.ConsoleRenderer()
    )
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            pii_redaction_processor,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )
    structlog.contextvars.bind_contextvars(service=service)


def get_logger(name: str | None = None) -> Any:
    return structlog.get_logger(name)
