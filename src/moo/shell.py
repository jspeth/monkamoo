import asyncio
import sys
from concurrent.futures import ThreadPoolExecutor

from . import interpreter
from .core.player import Player
from .logging_config import get_logger

# Get logger for this module
logger = get_logger("monkamoo.shell")


class Shell:
    """A command shell for processing user input and executing MOO commands."""

    intro = "Welcome to MonkaMOO!"
    player = None

    def __init__(self, world, player=None, stdin=sys.stdin, stdout=sys.stdout, loop=None):
        self.world = world
        self.stdin = stdin
        self.stdout = stdout
        self.loop = loop or asyncio.get_event_loop()
        self.executor = ThreadPoolExecutor()
        self.set_player(player)
        self.stdout.write(self.intro + "\n")
        logger.info("Shell initialized for world: %s", world.path)

    def set_player(self, player):
        if self.player:
            self.player.stdout = None
        self.player = player
        if self.player:
            self.player.stdout = self.stdout
            logger.info("Shell player set to: %s", player.name)

    async def cmdloop(self):
        logger.info("Shell command loop started")
        while True:
            try:
                line = await self.get_input()
            except EOFError:
                logger.info("Shell received EOF, exiting")
                break
            if line in {"quit", "exit"}:
                logger.info("Shell received quit command")
                break
            await self.exec_cmd(line)
        logger.info("Shell command loop ended")

    async def get_input(self):
        if hasattr(self.stdin, "async_readline"):
            line = await self.stdin.async_readline()
        else:
            line = await self.loop.run_in_executor(self.executor, self.stdin.readline)
        if not line:
            raise EOFError
        return line.strip()

    async def exec_cmd(self, line):
        arg = " ".join(line.split(" ")[1:])
        if line.startswith("interact"):
            logger.debug("Shell executing interact command: %s", arg)
            return await self.do_interact(arg)
        if line.startswith("player"):
            logger.debug("Shell executing player command: %s", arg)
            return await self.do_player(arg)
        logger.debug("Shell executing default command: %s", line)
        await self.default(line)
        return None

    async def default(self, line):
        if not self.player:
            return await self.do_player(None)
        if line:
            logger.debug("Shell parsing command for player %s: %s", self.player.name if self.player else "None", line)
            self.world.parse_command(self.player, line)
        return None

    async def do_interact(self, _arg):
        globals().update(((p.name.lower()), p) for p in self.world.players)
        interpreter.interact(local=globals(), stdin=self.stdin, stdout=self.stdout)

    async def do_player(self, arg):
        if not arg:
            self.stdout.write('Type "player [name]" to choose a player.\n')
            return
        player = self.world.find_player(arg)
        if not player:
            player = Player(name=arg)
            self.world.add_player(player)
        self.set_player(player)
        self.player.location.look(self.player)
