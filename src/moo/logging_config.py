import logging
import os
from typing import Optional

def setup_logging(mode: str = "console", log_level: Optional[str] = None) -> None:
    """
    Set up logging configuration for MonkaMOO.

    Args:
        mode: "console" for stdout logging, "file" for file logging
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                  If None, uses LOG_LEVEL env var or defaults to INFO
    """
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()

    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    log_datefmt = '%Y-%m-%d %H:%M:%S'

    if mode == "file":
        # File logging
        logging.basicConfig(
            level=getattr(logging, log_level),
            format=log_format,
            datefmt=log_datefmt,
            handlers=[logging.FileHandler('log.txt')]
        )
    else:
        # Console logging
        logging.basicConfig(
            level=getattr(logging, log_level),
            format=log_format,
            datefmt=log_datefmt,
            handlers=[logging.StreamHandler()]
        )

def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance for the given name.

    Args:
        name: Logger name. If None, uses 'monkamoo'

    Returns:
        Logger instance
    """
    if name is None:
        name = "monkamoo"
    return logging.getLogger(name)
