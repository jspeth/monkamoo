import cmd
import sys

from . import interpreter

from .core.player import Player

class Shell(cmd.Cmd):
    """ A command shell for processing user input and executing MOO commands. """

    intro = 'Welcome to MonkaMOO!'
    prompt = ''
    file = None
    use_rawinput = 0
    player = None

    def __init__(self, world, player=None, stdin=None, stdout=None):
        cmd.Cmd.__init__(self, stdin=stdin, stdout=stdout)
        self.world = world
        self.set_player(player)

    def set_player(self, player):
        if self.player:
            self.player.stdout = None
        self.player = player
        if self.player:
            self.player.stdout = self.stdout

    def precmd(self, line):
        if line == 'EOF':
            print
            sys.exit(0)
        return line

    def default(self, arg):
        if not self.player:
            self.stdout.write('Type "player [name]" to choose a player.\n')
            return
        if arg:
            self.world.parse_command(self.player, arg)

    def do_interact(self, arg):
        globals().update(((p.name.lower()), p) for p in self.world.players)
        interpreter.interact(local=globals(), stdin=self.stdin, stdout=self.stdout)

    def do_player(self, arg):
        player = self.world.find_player(arg)
        if not player:
            player = Player(name=arg)
            self.world.add_player(player)
        self.set_player(player)
        self.player.location.look(self.player)

    def do_quit(self, arg):
        sys.exit(0)
