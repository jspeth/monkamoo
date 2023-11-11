import asyncio
from typing import AsyncGenerator

class Broker:
    def __init__(self) -> None:
        self.channels = {}

    async def publish(self, channel: str, message: str) -> None:
        connections = self.channels.setdefault(channel, set())
        for connection in connections:
            await connection.put(message)

    async def subscribe(self, channel: str) -> AsyncGenerator[str, None]:
        connections = self.channels.setdefault(channel, set())
        connection = asyncio.Queue()
        connections.add(connection)
        try:
            while True:
                yield await connection.get()
        finally:
            connections.remove(connection)
