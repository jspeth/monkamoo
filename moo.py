#!/usr/bin/env python

import argparse
import cmd
import code
import json
import sys
import uuid

import server

## Helper for joining strings
def join_strings(items, word='and'):
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return items[0] + ' ' + word + ' ' + items[1]
    return ', '.join(items[:-1]) + ', ' + word + ' ' + items[-1]


## World
class World:
    path = 'world.json'

    def __init__(self):
        self.rooms = {'0': Room(id='0', description='This is the beginning of the world.')}
        self.players = {}

    def json_dictionary(self):
        return {'rooms': self.rooms, 'players': self.players}

    def load(self):
        data = open(self.path, 'r').read()
        world = json.loads(data)
        # rooms
        if 'rooms' in world:
            rooms = {}
            for room_id, room_dict in world['rooms'].iteritems():
                rooms[room_id] = Room(**room_dict)
            self.rooms = rooms
        # players
        if 'players' in world:
            for player_id, player_dict in world['players'].iteritems():
                self.add_player(Player(**player_dict))

    def save(self):
        data = json.dumps(self, default=lambda o: o.json_dictionary(), sort_keys=True, indent=2, separators=(',', ': '))
        with open(self.path, 'w') as f:
            f.write(data)

    def add_player(self, player):
        if player.id not in self.players:
            self.players[player.id] = player
        if not player.room:
            player.room = self.rooms['0']
        self.rooms[player.room.id].players[player.id] = player

    def move_player(self, player, new_room):
        del player.room.players[player.id]
        new_room.players[player.id] = player

    def find_player(self, name):
        for player in self.players.values():
            if player.name.lower() == name.lower():
                return player
        return None


## Room
class Room:
    def __init__(self, id=None, name=None, description=None, exits=None, players=None):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.exits = exits or {}
        self.players = players or {}

    def json_dictionary(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'exits': self.exits
        }

    def print_line(self, player, message, exclude_player=False):
        for other in self.players.values():
            if exclude_player and other is player:
                continue
            other.print_line(message)

    def look(self, player):
        if self.name:
            player.print_line('* ' + self.name + ' *')
        player.print_line(self.description or 'You see nothing here.')
        if self.exits:
            directions = self.exits.keys()
            player.print_line('You can go ' + join_strings(directions, 'or') + '.')
        players = [p for p in self.players.values() if p != player]
        if players:
            names = [p.name for p in players]
            isAre = len(players) > 1 and 'are' or 'is'
            player.print_line(join_strings(names, 'and') + ' ' + isAre + ' here.')

    def go(self, player, direction=None):
        if direction in self.exits:
            room = world.rooms[self.exits[direction]]
            self.print_line(player, player.name + ' exits to the ' + direction + '.', exclude_player=True)
            world.move_player(player, room)
            room.print_line(player, player.name + ' enters the room.', exclude_player=True)
            room.look(player)
            return room
        else:
            player.print_line('You can\'t go that way.')

    def dig(self, player, direction=None, back='back'):
        if direction is None:
            player.print_line('You must give a direction.')
        elif direction in self.exits:
            player.print_line('That direction already exists.')
        else:
            room = Room(exits={back: self.id})
            world.rooms[room.id] = room
            self.exits[direction] = room.id
            world.move_player(player, room)
            return room

    def do_name(self, player, name=None):
        if name:
            self.name = name
        elif self.name:
            player.print_line('* ' + self.name + ' *')
        else:
            player.print_line('This room has no name.')

    def do_describe(self, player, description=None):
        if description:
            self.description = description
        elif self.description:
            player.print_line(self.description)
        else:
            player.print_line('This room has no description.')


## Player
class Player:
    stdout = None

    def __init__(self, id=None, name=None, description=None, room_id=None):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.room = room_id and world.rooms[room_id] or None

    def json_dictionary(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'room_id': self.room.id
        }

    def print_line(self, message):
        if self.stdout:
            self.stdout.write(message + '\n')
            self.stdout.flush()

    def look(self, args=None):
        self.room.look(self)

    def say(self, message=None):
        if message:
            self.room.print_line(self, self.name + ' says, "' + message + '"')

    def emote(self, message=None):
        if message:
            self.room.print_line(self, self.name + ' ' + message)

    def do_name(self, name=None):
        self.room.do_name(self, name)

    def do_describe(self, description=None):
        self.room.do_describe(self, description)

    def go(self, direction=None):
        self.room = self.room.go(self, direction) or self.room

    def dig(self, direction=None, back='back'):
        self.room = self.room.dig(self, direction, back) or self.room

    def find_verb(self, verb):
        for verb in [verb, 'do_' + verb]:
            method = getattr(self, verb, None)
            if method and callable(method):
                return method
        return None

    def parse_command(self, line):
        args = line.split(' ', 1)
        verb = self.find_verb(args[0])
        if verb:
            arg = len(args) > 1 and args[1] or None
            verb(arg)
        else:
            self.print_line('I didn\'t understand that.')


## Shell

class Shell(cmd.Cmd):
    intro = 'Welcome to MonkaMOO!'
    prompt = ''
    file = None
    use_rawinput = 0
    player = None

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
        if line.startswith('"'):
            line = 'say ' + line.strip('" ')
        elif line.startswith(':'):
            line = 'emote ' + line.strip(': ')
        return line

    def default(self, arg):
        if not self.player:
            self.stdout.write('Type "player [name]" to choose a player.\n')
            return
        if arg:
            self.player.parse_command(arg)

    def do_load(self, arg):
        world.load()

    def do_save(self, arg):
        world.save()

    def do_interact(self, arg):
        # see https://docs.python.org/2/library/code.html?highlight=interpreter
        code.interact(local=globals())

    def do_player(self, arg):
        player = world.find_player(arg)
        if not player:
            player = Player(name=arg)
            world.add_player(player)
        self.set_player(player)

    def do_quit(self, arg):
        sys.exit(0)


## Launch

world = World()
world.load()

def main():
    parser = argparse.ArgumentParser(description='MonkaMOO')
    parser.add_argument('-i', '--interact', action='store_true', help='Run python shell')
    parser.add_argument('-s', '--server', action='store_true', help='Start moo server')
    args = parser.parse_args()
    if args.interact:
        code.interact(local=globals())
    elif args.server:
        print 'Starting server...'
        moo_server = server.MonkaMOOServer()
        moo_server.run()
    else:
        me = world.find_player('Jim')
        Shell(me).cmdloop()

if __name__ == '__main__':
    main()
