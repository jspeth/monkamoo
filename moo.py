#!/usr/bin/env python

import argparse
import cmd
import json
import sys

import interpreter
import parser
import server

from core import Object, Room, Player, Thing
from ball import Ball

class World(Object):
    """ The root container of all MOO objects. """

    def __init__(self, path=None, **kwargs):
        super(World, self).__init__(**kwargs)
        self.path = path
        if not self.contents:
            self.contents = {'0': Room(id='0', description='This is the beginning of the world.')}

    def json_dictionary(self):
        return {'contents': self.contents}

    def load(self, path=None):
        path = path or self.path
        data = open(path, 'r').read()
        if not data:
            return
        world = json.loads(data)
        all_contents = {}
        for object_dict in world.get('contents', {}).values():
            # get object class
            class_name = object_dict.get('type')
            cls = globals().get(class_name)
            if not cls:
                sys.stderr.write('Error: class not found: ' + class_name + '\n')
                continue
            del object_dict['type']
            # create object, building contents map
            obj = cls(**object_dict)
            obj.world = self
            if obj.location:
                contents = all_contents.setdefault(obj.location, {})
                contents[obj.id] = obj
            self.contents[obj.id] = obj
        # update objects with their contents
        for id, contents in all_contents.iteritems():
            if id in self.contents:
                self.contents[id].contents = contents
        # replace location id with object
        for obj in self.contents.values():
            if obj.location and obj.location in self.contents:
                obj.location = self.contents[obj.location]

    def save(self, path=None):
        path = path or self.path
        data = json.dumps(self, default=lambda o: o.json_dictionary(), sort_keys=True, indent=2, separators=(',', ': '))
        with open(path, 'w') as f:
            f.write(data)

    def add_player(self, player):
        self.contents[player.id] = player
        if not player.location:
            player.location = self.contents['0']
        player.location.contents[player.id] = player


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

    def __init__(self, player=None, stdin=None, stdout=None):
        cmd.Cmd.__init__(self, stdin=stdin, stdout=stdout)
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
        command = parser.Parser.parse(line)
        if not command:
            self.player.tell('I didn\'t understand that.')
            return
        command.resolve(world, self.player)
        verb = self.find_verb(command.verb)
        if not verb:
            self.player.tell('I didn\'t understand that.')
            return
        verb(command)

    def find_verb(self, verb):
        search_path = [self.player] + self.player.contents.values() + self.player.location.contents.values()
        for obj in search_path:
            method = obj.get_verb(verb)
            if method:
                return method
        return None

    def do_load(self, arg):
        world.load()

    def do_save(self, arg):
        world.save()

    def do_interact(self, arg):
        interpreter.interact(local=globals(), stdin=self.stdin, stdout=self.stdout)

    def do_player(self, arg):
        player = world.find_player(arg)
        if not player:
            player = Player(name=arg)
            world.add_player(player)
        self.set_player(player)

    def do_quit(self, arg):
        sys.exit(0)


## Launch

world = World(path='world.json')
world.load()

def main():
    parser = argparse.ArgumentParser(description='MonkaMOO')
    parser.add_argument('-i', '--interact', action='store_true', help='Run python shell')
    parser.add_argument('-s', '--server', action='store_true', help='Start moo server')
    args = parser.parse_args()
    if args.interact:
        interpreter.interact(local=globals())
    elif args.server:
        print 'Starting server...'
        moo_server = server.MonkaMOOServer()
        moo_server.run()
    else:
        me = world.find_player('Jim')
        Shell(me).cmdloop()

if __name__ == '__main__':
    main()
