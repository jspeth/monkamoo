"""
Storage interface for MonkaMOO.

Defines the contract that all storage implementations must follow.
"""

from abc import ABC, abstractmethod


class StorageInterface(ABC):
    """Abstract base class for storage implementations."""

    @abstractmethod
    def save_world(self, world) -> bool:
        """Save world state data.

        Args:
            world: World object to save

        Returns:
            True if save was successful, False otherwise
        """

    @abstractmethod
    def load_world(self) -> dict | None:
        """Load world state data.

        Returns:
            World data dictionary if successful, None otherwise
        """

    @abstractmethod
    def save_ai_history(self, player_name: str, history: list[dict]) -> bool:
        """Save AI player conversation history.

        Args:
            player_name: Name of the AI player
            history: List of conversation messages

        Returns:
            True if save was successful, False otherwise
        """

    @abstractmethod
    def load_ai_history(self, player_name: str) -> list[dict] | None:
        """Load AI player conversation history.

        Args:
            player_name: Name of the AI player

        Returns:
            List of conversation messages if successful, None otherwise
        """

    @abstractmethod
    def list_ai_players(self) -> list[str]:
        """List all available AI players.

        Returns:
            List of AI player names
        """

    @abstractmethod
    def health_check(self) -> bool:
        """Check if storage is healthy and accessible.

        Returns:
            True if storage is healthy, False otherwise
        """
