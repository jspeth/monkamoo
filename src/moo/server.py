import asyncio

from . import shell
from .logging_config import get_logger

# Get logger for this module
logger = get_logger("monkamoo.server")

class StreamReaderWrapper:
    def __init__(self, reader):
        self.reader = reader

    async def async_readline(self):
        data = await self.reader.readline()
        return data.decode()

class StreamWriterWrapper:
    def __init__(self, writer):
        self.writer = writer

    def write(self, data):
        if isinstance(data, str):
            data = data.encode()
        self.writer.write(data)

    def flush(self):
        pass

class MonkaMOOServer(object):
    clients = []

    def __init__(self, world):
        self.world = world
        self.server = None

    async def start_server(self):
        self.server = await asyncio.start_server(self.handle_client, '0.0.0.0', 8888)
        addr = self.server.sockets[0].getsockname()
        logger.info(f'Telnet server started on {addr}')

    async def handle_client(self, reader, writer):
        client_addr = writer.get_extra_info('peername')
        logger.info('Telnet client connected: %s', client_addr)
        self.clients.append(writer)

        try:
            # wrap the reader and writer
            wrapped_reader = StreamReaderWrapper(reader)
            wrapped_writer = StreamWriterWrapper(writer)

            # run shell command loop
            client_shell = shell.Shell(self.world, stdin=wrapped_reader, stdout=wrapped_writer)
            await client_shell.cmdloop()
        except Exception as e:
            logger.error('Telnet client error for %s: %s', client_addr, e)
        finally:
            # close connection
            self.clients.remove(writer)
            writer.close()
            logger.info('Telnet client disconnected: %s', client_addr)

    async def run(self):
        await self.start_server()
        logger.info('Telnet server running, waiting for connections...')
        async with self.server:
            await self.server.serve_forever()

    def stop(self):
        if self.server:
            logger.info('Stopping telnet server...')
            self.server.close()
