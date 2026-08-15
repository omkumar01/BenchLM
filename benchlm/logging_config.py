"""Logging configuration for BenchLM using loguru."""

import sys
from pathlib import Path

from loguru import logger

from benchlm.config import get_config, LoggingConfig


def setup_logging(config: LoggingConfig | None = None) -> None:
    """Configure loguru logging based on config."""
    if config is None:
        config = get_config().logging

    # Remove default handler
    logger.remove()

    # Ensure log directory exists
    log_path = Path(config.file_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Console handler (stdout)
    logger.add(
        sys.stdout,
        level=config.level,
        format=config.format,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # File handler with rotation
    logger.add(
        config.file_path,
        level=config.level,
        format=config.format,
        rotation=config.rotation,
        retention=config.retention,
        compression=config.compression,
        backtrace=True,
        diagnose=True,
        enqueue=True,  # Thread-safe
    )

    # Set log level for specific modules
    try:
        logger.level("TRACE", color="<dim>")
    except ValueError:
        pass

    logger.info(f"Logging initialized - level: {config.level}, file: {config.file_path}")


def get_logger(name: str):
    """Get a logger instance for a module."""
    return logger.bind(module=name)


# Context manager for temporary log level changes
class LogLevel:
    """Context manager to temporarily change log level."""

    def __init__(self, level: str):
        self.level = level
        self.previous_level = None

    def __enter__(self):
        self.previous_level = logger._core.min_level
        logger.remove()
        logger.add(sys.stdout, level=self.level, format=logger._core.handlers[0]._format)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.remove()
        logger.add(sys.stdout, level=self.previous_level, format=logger._core.handlers[0]._format)