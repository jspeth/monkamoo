"""
Local file storage implementation for MonkaMOO.

Provides file-based storage for local development and testing.
"""

import json
from pathlib import Path

from ..logging_config import get_logger
from .interface import StorageInterface

# Get logger for this module
logger = get_logger("monkamoo.storage.local")


class LocalFileStorage(StorageInterface):
    """Local file-based storage implementation."""

    def __init__(self, world_path: str = "world.json", bots_dir: str = "bots"):
        """Initialize local file storage.

        Args:
            world_path: Path to world state file
            bots_dir: Directory containing AI player history files
        """
        self.world_path = Path(world_path)
        self.bots_dir = Path(bots_dir)

        # Ensure bots directory exists
        self.bots_dir.mkdir(parents=True, exist_ok=True)

        logger.info("LocalFileStorage initialized: world=%s, bots=%s", self.world_path, self.bots_dir)

    def save_world(self, world) -> bool:
        try:
            logger.debug("Saving world to local file: %s", self.world_path)
            data = json.dumps(
                world,
                default=lambda o: o.json_dictionary(),
                sort_keys=True,
                indent=2,
                separators=(",", ": "),
            )
            with self.world_path.open("w") as f:
                f.write(data)
            logger.info("World saved successfully to local file")
        except Exception:
            logger.exception("Failed to save world to local file")
            return False
        else:
            return True

    def load_world(self) -> dict | None:
        try:
            logger.debug("Loading world from local file: %s", self.world_path)
            if not self.world_path.exists():
                logger.warning("World file does not exist: %s", self.world_path)
                return None
            with self.world_path.open() as f:
                data = f.read()
            if not data:
                logger.warning("World file is empty: %s", self.world_path)
                return None
            world_data = json.loads(data)
            logger.info("World loaded successfully from local file")
        except Exception:
            logger.exception("Failed to load world from local file")
            return None
        else:
            return world_data

    def save_ai_history(self, player_name: str, history: list[dict]) -> bool:
        try:
            history_path = self.bots_dir / f"{player_name}.json"
            logger.debug("Saving AI history for %s to: %s", player_name, history_path)
            history_path.parent.mkdir(parents=True, exist_ok=True)
            with history_path.open("w") as f:
                json.dump(history, f, indent=2, separators=(",", ": "))
            logger.debug("AI history saved successfully for %s", player_name)
        except Exception:
            logger.exception("Failed to save AI history for %s", player_name)
            return False
        else:
            return True

    def load_ai_history(self, player_name: str) -> list[dict] | None:
        try:
            history_path = self.bots_dir / f"{player_name}.json"
            logger.debug("Loading AI history for %s from: %s", player_name, history_path)
            if not history_path.exists():
                logger.debug("AI history file does not exist for %s", player_name)
                return None
            with history_path.open() as f:
                history = json.load(f)
            logger.debug("AI history loaded successfully for %s", player_name)
        except Exception:
            logger.exception("Failed to load AI history for %s", player_name)
            return None
        else:
            return history

    def list_ai_players(self) -> list[str]:
        try:
            if not self.bots_dir.exists():
                logger.debug("Bots directory does not exist: %s", self.bots_dir)
                return []
            players = []
            for file_path in self.bots_dir.glob("*.json"):
                player_name = file_path.stem
                players.append(player_name)
            logger.debug("Found %d AI players in local storage", len(players))
        except Exception:
            logger.exception("Failed to list AI players")
            return []
        else:
            return players

    def health_check(self) -> bool:
        try:
            world_dir = self.world_path.parent
            world_dir.mkdir(parents=True, exist_ok=True)
            self.bots_dir.mkdir(parents=True, exist_ok=True)
            logger.debug("Local file storage health check passed")
        except Exception:
            logger.exception("Local file storage health check failed")
            return False
        else:
            return True
