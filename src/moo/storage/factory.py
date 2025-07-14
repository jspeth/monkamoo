"""
Storage factory for MonkaMOO.

Determines which storage implementation to use based on environment configuration.
"""

import os

from ..logging_config import get_logger
from .cloud import CloudStorage
from .interface import StorageInterface
from .local import LocalFileStorage

# Get logger for this module
logger = get_logger("monkamoo.storage.factory")


def get_storage(world_path: str = "world.json", bots_dir: str = "bots") -> StorageInterface:
    """Get the appropriate storage implementation based on environment.

    Args:
        world_path: Path to world state file (for local storage)
        bots_dir: Directory containing AI player history files (for local storage)

    Returns:
        StorageInterface implementation

    Raises:
        ValueError: If cloud storage is requested but not properly configured
    """
    storage_type = os.getenv("STORAGE_TYPE", "local").lower()

    logger.info("Initializing storage with type: %s", storage_type)

    if storage_type == "local":
        logger.info("Using local file storage")
        return LocalFileStorage(world_path=world_path, bots_dir=bots_dir)
    if storage_type == "heroku":
        logger.info("Using cloud storage for Heroku")
        return CloudStorage()
    logger.warning("Unknown storage type '%s', falling back to local", storage_type)
    return LocalFileStorage(world_path=world_path, bots_dir=bots_dir)


def get_storage_with_fallback(world_path: str = "world.json", bots_dir: str = "bots") -> StorageInterface:
    """Get storage implementation with fallback to local if cloud fails.

    Args:
        world_path: Path to world state file (for local storage)
        bots_dir: Directory containing AI player history files (for local storage)

    Returns:
        StorageInterface implementation
    """
    storage_type = os.getenv("STORAGE_TYPE", "local").lower()

    if storage_type == "heroku":
        try:
            logger.info("Attempting to use cloud storage")
            cloud_storage = CloudStorage()
            # Test cloud storage health
            if cloud_storage.health_check():
                logger.info("Cloud storage is healthy, using it")
                return cloud_storage
            logger.warning("Cloud storage health check failed, falling back to local")
            return LocalFileStorage(world_path=world_path, bots_dir=bots_dir)
        except Exception:
            logger.exception("Failed to initialize cloud storage")
            logger.info("Falling back to local file storage")
            return LocalFileStorage(world_path=world_path, bots_dir=bots_dir)
    else:
        return get_storage(world_path, bots_dir)
