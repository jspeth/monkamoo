"""
Storage abstraction layer for MonkaMOO.

This module provides a unified interface for storing world state and AI player history
across different environments (local files, cloud storage, etc.).
"""

from .cloud import CloudStorage
from .factory import get_storage, get_storage_with_fallback
from .interface import StorageInterface
from .local import LocalFileStorage

__all__ = ["StorageInterface", "LocalFileStorage", "CloudStorage", "get_storage", "get_storage_with_fallback"]
