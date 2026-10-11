import logging
import structlog
import sys

ALLOWED_KEYS=["event", "level", "timestamp", "request_id", "user_id", "method", "route", "status", "duration_ms", "exc_type"]

def redact_sensitive(logger, method_name, event_dict):
    for k in list(event_dict):
        if k.lower() not in ALLOWED_KEYS : event_dict[k] = "[REDACTED]"
    return event_dict 

def _exception_type_name(exc_info) -> str | None:
    if exc_info is True:
        exc_info = sys.exc_info()
    if isinstance(exc_info, BaseException):
        return type(exc_info).__name__
    if isinstance(exc_info, tuple) and exc_info and exc_info[0] is not None:
        return exc_info[0].__name__
    return None

def sanitize_exceptions(logger, method_name, event_dict):
    exc_info = event_dict.pop("exc_info", None)
    if exc_info:
        name = _exception_type_name(exc_info)
        if name:
            event_dict["exc_type"] = name
    return event_dict


def configure_logging(env: str, level: str = "INFO"):
    log_level=logging.getLevelNamesMapping().get(str(level).upper(), logging.INFO)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            sanitize_exceptions,
            redact_sensitive,
            structlog.dev.ConsoleRenderer() if env == "development" else structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False
    )

def get_log(name: str):
    return structlog.get_logger(name)

