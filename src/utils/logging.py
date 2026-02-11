"""
Structured Logging Module for Smart Microgrid Manager Pro.

This module provides a centralized logging configuration.
"""

import logging
import sys
from typing import Optional


class ColorizingFormatter(logging.Formatter):
    """Formatter with color support for terminal output."""
    
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",   # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",   # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        """Add color to the formatted message."""
        if not sys.stdout.isatty():
            return super().format(record)
        
        message = super().format(record)
        color = self.COLORS.get(record.levelname, self.RESET)
        return f"{color}{message}{self.RESET}"


def setup_logger(
    name: str,
    level: int = logging.INFO,
    use_json: bool = False,
) -> logging.Logger:
    """
    Configure and return a logger instance.
    
    Args:
        name: Logger name
        level: Minimum log level
        use_json: Whether to output JSON format
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    console_handler = logging.StreamHandler(sys.stdout)
    
    if use_json:
        formatter = logging.Formatter('{"time": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s"}')
        formatter.datefmt = "%Y-%m-%dT%H:%M:%S"
        console_handler.setFormatter(formatter)
    else:
        fmt = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
        datefmt = "%Y-%m-%d %H:%M:%S"
        formatter = ColorizingFormatter(fmt=fmt, datefmt=datefmt)
        console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    return logger


def configure_app_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    use_json: bool = False,
) -> None:
    """Configure root logger for the application."""
    # Suppress noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    
    console_handler = logging.StreamHandler(sys.stdout)
    
    if use_json:
        formatter = logging.Formatter('{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}')
        formatter.datefmt = "%Y-%m-%dT%H:%M:%S"
        console_handler.setFormatter(formatter)
    else:
        fmt = "%(asctime)s | %(levelname)-8s | %(message)s"
        datefmt = "%Y-%m-%d %H:%M:%S"
        formatter = ColorizingFormatter(fmt=fmt, datefmt=datefmt)
        console_handler.setFormatter(formatter)
    
    root_logger.addHandler(console_handler)
    
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_formatter = logging.Formatter('{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}')
        file_formatter.datefmt = "%Y-%m-%dT%H:%M:%S"
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)


# Convenience loggers
_optimization_logger = None
_weather_logger = None
_database_logger = None
_auth_logger = None


def get_optimization_logger() -> logging.Logger:
    """Get logger for optimization module."""
    global _optimization_logger
    if _optimization_logger is None:
        _optimization_logger = setup_logger("optimization", level=logging.INFO)
    return _optimization_logger


def get_weather_logger() -> logging.Logger:
    """Get logger for weather module."""
    global _weather_logger
    if _weather_logger is None:
        _weather_logger = setup_logger("weather", level=logging.INFO)
    return _weather_logger


def get_database_logger() -> logging.Logger:
    """Get logger for database module."""
    global _database_logger
    if _database_logger is None:
        _database_logger = setup_logger("database", level=logging.INFO)
    return _database_logger


def get_auth_logger() -> logging.Logger:
    """Get logger for authentication module."""
    global _auth_logger
    if _auth_logger is None:
        _auth_logger = setup_logger("auth", level=logging.INFO)
    return _auth_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the given name.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Configured logger instance
    """
    return setup_logger(name, level=logging.INFO)


if __name__ == "__main__":
    # Demonstration
    configure_app_logging(level=logging.DEBUG)
    
    logger = setup_logger(__name__)
    
    logger.debug("Debug message")
    logger.info("Information message")
    logger.warning("Warning message")
    logger.error("Error message")

