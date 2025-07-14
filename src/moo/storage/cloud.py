"""
Cloud storage implementation for MonkaMOO using AWS S3.

Provides S3-based storage for Heroku deployment.
"""

import json
import os

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from ..logging_config import get_logger
from .interface import StorageInterface

# Get logger for this module
logger = get_logger("monkamoo.storage.cloud")


class CloudStorage(StorageInterface):
    """AWS S3-based cloud storage implementation."""

    def __init__(self, bucket_name: str = None, region: str = None):
        """Initialize cloud storage with S3.

        Args:
            bucket_name: S3 bucket name (defaults to environment variable)
            region: AWS region (defaults to environment variable)
        """
        self.bucket_name = bucket_name or os.getenv("CLOUD_STORAGE_BUCKET")
        self.region = region or os.getenv("AWS_REGION", "us-east-1")

        if not self.bucket_name:
            msg = "CLOUD_STORAGE_BUCKET environment variable is required"
            raise ValueError(msg)

        # Initialize S3 client
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=self.region,
        )

        logger.info("CloudStorage initialized: bucket=%s, region=%s", self.bucket_name, self.region)

    def _get_world_key(self) -> str:
        """Get S3 key for world state."""
        return "world.json"

    def _get_ai_history_key(self, player_name: str) -> str:
        """Get S3 key for AI player history."""
        return f"bots/{player_name}.json"

    def save_world(self, world_data: dict) -> bool:
        try:
            key = self._get_world_key()
            data = json.dumps(world_data, sort_keys=True, indent=2, separators=(",", ": "))
            logger.debug("Saving world to S3: bucket=%s, key=%s", self.bucket_name, key)
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=data.encode("utf-8"),
                ContentType="application/json",
            )
            logger.info("World saved successfully to S3")
        except (ClientError, NoCredentialsError):
            logger.exception("Failed to save world to S3")
            return False
        except Exception:
            logger.exception("Unexpected error saving world to S3")
            return False
        else:
            return True

    def load_world(self) -> dict | None:
        try:
            key = self._get_world_key()
            logger.debug("Loading world from S3: bucket=%s, key=%s", self.bucket_name, key)
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            data = response["Body"].read().decode("utf-8")
            if not data:
                logger.warning("World data is empty in S3")
                return None
            world_data = json.loads(data)
            logger.info("World loaded successfully from S3")
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                logger.warning("World file does not exist in S3: %s", key)
                return None
            logger.exception("Failed to load world from S3")
            return None
        except Exception:
            logger.exception("Unexpected error loading world from S3")
            return None
        else:
            return world_data

    def save_ai_history(self, player_name: str, history: list[dict]) -> bool:
        try:
            key = self._get_ai_history_key(player_name)
            data = json.dumps(history, indent=2, separators=(",", ": "))
            logger.debug("Saving AI history for %s to S3: bucket=%s, key=%s", player_name, self.bucket_name, key)
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=data.encode("utf-8"),
                ContentType="application/json",
            )
            logger.debug("AI history saved successfully for %s to S3", player_name)
        except (ClientError, NoCredentialsError):
            logger.exception("Failed to save AI history for %s to S3", player_name)
            return False
        except Exception:
            logger.exception("Unexpected error saving AI history for %s to S3", player_name)
            return False
        else:
            return True

    def load_ai_history(self, player_name: str) -> list[dict] | None:
        try:
            key = self._get_ai_history_key(player_name)
            logger.debug("Loading AI history for %s from S3: bucket=%s, key=%s", player_name, self.bucket_name, key)
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            data = response["Body"].read().decode("utf-8")
            history = json.loads(data)
            logger.debug("AI history loaded successfully for %s from S3", player_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                logger.debug("AI history file does not exist for %s in S3", player_name)
                return None
            logger.exception("Failed to load AI history for %s from S3", player_name)
            return None
        except Exception:
            logger.exception("Unexpected error loading AI history for %s from S3", player_name)
            return None
        else:
            return history

    def list_ai_players(self) -> list[str]:
        try:
            logger.debug("Listing AI players from S3: bucket=%s, prefix=bots/", self.bucket_name)
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix="bots/",
            )
            players = []
            if "Contents" in response:
                for obj in response["Contents"]:
                    key = obj["Key"]
                    if key.endswith(".json") and key != "bots/":
                        player_name = key.replace("bots/", "").replace(".json", "")
                        players.append(player_name)
            logger.debug("Found %d AI players in S3", len(players))
        except (ClientError, NoCredentialsError):
            logger.exception("Failed to list AI players from S3")
            return []
        except Exception:
            logger.exception("Unexpected error listing AI players from S3")
            return []
        else:
            return players

    def health_check(self) -> bool:
        try:
            self.s3_client.list_objects_v2(Bucket=self.bucket_name, MaxKeys=1)
            logger.debug("S3 storage health check passed")
        except (ClientError, NoCredentialsError):
            logger.exception("S3 storage health check failed")
            return False
        except Exception:
            logger.exception("Unexpected error in S3 health check")
            return False
        else:
            return True
