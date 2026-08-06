"""Logging configuration.

A single stdout stream handler with a consistent, greppable format. No
external logging service integration — for a project this size, that's
infrastructure to configure and maintain without a corresponding benefit.
"""

import logging
import sys

_LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s %(message)s"
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def configure_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt=_LOG_FORMAT, datefmt=_DATE_FORMAT))

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)

    # Quiet down noisy third-party loggers at INFO; keep our own app logs.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
