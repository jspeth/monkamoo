"""
Migration script to upload local MonkaMOO data to cloud storage.

This script uploads the world.json file and bots/*.json files to S3.
"""

import json
import os
import sys
from pathlib import Path

import dotenv

# Load environment variables
dotenv.load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from moo.logging_config import get_logger, setup_logging  # noqa: E402
from moo.storage import get_storage_with_fallback  # noqa: E402


def migrate_to_cloud():
    """Migrate local data to cloud storage."""
    # Set up logging
    setup_logging(mode="console")
    logger = get_logger("monkamoo.migration")

    # Check if cloud storage is configured
    storage_type = os.getenv("STORAGE_TYPE", "local").lower()
    if storage_type != "heroku":
        return False

    bucket_name = os.getenv("CLOUD_STORAGE_BUCKET")
    if not bucket_name:
        return False

    try:
        # Get cloud storage
        storage = get_storage_with_fallback()

        # Test health check
        if not storage.health_check():
            return False

        # Migrate world data
        world_file = Path("world.json")
        if world_file.exists():
            with world_file.open() as f:
                world_data = json.load(f)
            success = storage.save_world(world_data)
            if not success:
                return False

        # Migrate AI player history
        bots_dir = Path("bots")
        if bots_dir.exists():
            for bot_file in bots_dir.glob("*.json"):
                player_name = bot_file.stem
                with bot_file.open() as f:
                    history = json.load(f)
                success = storage.save_ai_history(player_name, history)
                if not success:
                    pass

        # Verify migration
        loaded_world = storage.load_world()
        if not loaded_world:
            return False
        storage.list_ai_players()
    except Exception:
        logger.exception("Migration failed")
        return False
    return True


def main():
    """Main migration function."""
    success = migrate_to_cloud()
    if success:
        pass
    else:
        pass


if __name__ == "__main__":
    main()
