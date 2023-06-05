import cmd
import sys

import interpreter
import line_parser

from core.player import Player

class Shell(cmd.Cmd):
    """ A command shell for processing user input and executing MOO commands. """

    intro = 'Welcome to MonkaMOO!'
    prompt = ''
    file = None
    use_rawinput = 0
    player = None

    shortcuts = {
        '"': 'say',
        ':': 'emote',
        '@': 'whisper',
        '#': 'jump'
    }

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
        for key in self.shortcuts:
            if line.startswith(key):
                line = self.shortcuts[key] + ' ' + line.strip(key + ' ')
                break
        return line

    def default(self, arg):
        if not self.player:
            self.stdout.write('Type "player [name]" to choose a player.\n')
            return
        if arg:
            self.parse_command(arg)

    def parse_command(self, line):
        command = line_parser.Parser.parse(line)
        if not command:
            self.player.tell('I didn\'t understand that.')
            return
        command.resolve(self.world, self.player)
        func = self.find_function(command)
        if not func:
            self.player.tell('I didn\'t understand that.')
            return
        func(command)

    def find_function(self, command):
        search_path = [command.player, command.player.room]
        if command.direct_object:
            search_path.append(command.direct_object)
        if command.indirect_object:
            search_path.append(command.indirect_object)
        for obj in search_path:
            method = obj.get_function(command.verb)
            if method:
                return method
        return None

    def do_load(self, arg):
        self.world.load()

    def do_save(self, arg):
        self.world.save()

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
