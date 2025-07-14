import asyncio
from collections.abc import AsyncGenerator

from .logging_config import get_logger

# Get logger for this module
logger = get_logger("monkamoo.broker")


class Broker:
    def __init__(self) -> None:
        self.channels = {}

    async def publish(self, channel: str, message: str) -> None:
        connections = self.channels.setdefault(channel, set())
        logger.debug(
            "Publishing message to channel %s: %s", channel, message[:100] + "..." if len(message) > 100 else message,
        )
        for connection in connections:
            await connection.put(message)

    async def subscribe(self, channel: str) -> AsyncGenerator[str, None]:
        connections = self.channels.setdefault(channel, set())
        connection = asyncio.Queue()
        connections.add(connection)
        logger.info("New subscription to channel: %s (total connections: %d)", channel, len(connections))
        try:
            while True:
                yield await connection.get()
        finally:
            connections.remove(connection)
            logger.info("Subscription ended for channel: %s (remaining connections: %d)", channel, len(connections))
