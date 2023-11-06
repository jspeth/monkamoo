import asyncio
import sys
from concurrent.futures import ThreadPoolExecutor

from . import interpreter
from .core.player import Player

class Shell(object):
    """ A command shell for processing user input and executing MOO commands. """

    intro = 'Welcome to MonkaMOO!'
    player = None

    def __init__(self, world, player=None, stdin=sys.stdin, stdout=sys.stdout, loop=None):
        self.world = world
        self.stdin = stdin
        self.stdout = stdout
        self.loop = loop or asyncio.get_event_loop()
        self.executor = ThreadPoolExecutor()
        self.set_player(player)
        self.stdout.write(self.intro + '\n')

    def set_player(self, player):
        if self.player:
            self.player.stdout = None
        self.player = player
        if self.player:
            self.player.stdout = self.stdout

    async def cmdloop(self):
        while True:
            try:
                line = await self.get_input()
            except EOFError:
                break
            if line == 'quit' or line == 'exit':
                break
            await self.exec_cmd(line)

    async def get_input(self):
        if hasattr(self.stdin, 'async_readline'):
            line = await self.stdin.async_readline()
        else:
            line = await self.loop.run_in_executor(self.executor, self.stdin.readline)
        if not line:
            raise EOFError
        return line.strip()

    async def exec_cmd(self, line):
        arg = ' '.join(line.split(' ')[1:])
        if line.startswith('interact'):
            return await self.do_interact(arg)
        if line.startswith('player'):
            return await self.do_player(arg)
        await self.default(line)

    async def default(self, line):
        if not self.player:
            return await self.do_player(None)
        if line:
            self.world.parse_command(self.player, line)

    async def do_interact(self, arg):
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
