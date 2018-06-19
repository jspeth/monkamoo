#!/usr/bin/env python

import argparse
import cmd
import json
import sys
import uuid

import interpreter
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

    def find_room(self, name):
        for room in self.rooms.values():
            if room.name and room.name.lower() == name.lower():
                return room
        return None

    def find_player(self, name):
        for player in self.players.values():
            if player.name.lower() == name.lower():
                return player
        return None

    def add_player(self, player):
        if player.id not in self.players:
            self.players[player.id] = player
        if not player.room:
            player.room = self.rooms['0']
        self.rooms[player.room.id].players[player.id] = player


## Room
class Room:
    def __init__(self, id=None, name=None, description=None, exits=None, players=None, contents=None):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.exits = exits or {}
        self.players = players or {}
        self.contents = contents or {}

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

    def on_enter(self, player, direction=None):
        self.print_line(player, player.name + ' enters the room.', exclude_player=True)
        self.look(player)

    def on_exit(self, player, direction=None):
        if direction:
            message = player.name + ' exits ' + direction + '.'
        else:
            message = player.name + ' exits the room.'
        self.print_line(player, message, exclude_player=True)

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
        if self.contents:
            player.print_line('There is ' + join_strings(self.contents.keys(), 'and') + ' here.')

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

    def __init__(self, id=None, name=None, description=None, room_id=None, contents=None):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.room = room_id and world.rooms[room_id] or None
        self.contents = contents or {}

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

    def find_verb(self, verb):
        for key in [verb, 'do_' + verb]:
            method = getattr(self, key, None)
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

    def set_room(self, room, direction=None):
        self.room.on_exit(self, direction)
        del self.room.players[self.id]
        self.room = room
        room.players[self.id] = self
        room.on_enter(self)

    def go(self, direction=None):
        if direction not in self.room.exits:
            self.print_line('You can\'t go that way.')
            return
        room = world.rooms[self.room.exits[direction]]
        self.set_room(room, direction)

    def jump(self, room_name=None):
        room = world.find_room(room_name)
        if not room:
            self.print_line('I couldn\'t find ' + room_name + '.')
            return
        self.set_room(room)

    def dig(self, direction=None, back='back'):
        if direction is None:
            self.print_line('You must give a direction.')
            return
        if direction in self.room.exits:
            self.print_line('That direction already exists.')
            return
        room = Room(exits={back: self.room.id})
        world.rooms[room.id] = room
        self.room.exits[direction] = room.id
        self.set_room(room, direction)

    def look(self, name=None):
        if name is None or name == 'here':
            self.room.look(self)
        elif name == 'me' or name == self.name:
            self.print_line(self.description or 'You see nothing special.')
            if self.contents:
                self.print_line('You have ' + join_strings(self.contents.keys(), 'and') + '.')
        elif name in self.contents:
            obj = self.contents[name]
            self.print_line(obj.description or 'You see nothing special.')
        elif name in self.room.contents:
            obj = self.room.contents[name]
            self.print_line(obj.description or 'You see nothing special.')
        else:
            self.print_line('There is no ' + name + ' here.')

    def do_name(self, name=None):
        self.room.do_name(self, name)

    def do_describe(self, description=None):
        self.room.do_describe(self, description)

    def say(self, message=None):
        if message:
            self.room.print_line(self, self.name + ' says, "' + message + '"')

    def tell(self, message=None):
        parts = message.split(' ', 1)
        if len(parts) < 2:
            self.print_line('What do you want to tell them?')
            return
        name, message = parts
        player = world.find_player(name)
        if player and message:
            player.print_line(self.name + ' whispers, "' + message + '"')

    def emote(self, message=None):
        if message:
            self.room.print_line(self, self.name + ' ' + message)

    def find(self, name=None):
        player = world.find_player(name)
        if player and player.room:
            if player.room.name:
                self.print_line(player.name + ' is in ' + player.room.name + '.')
            else:
                self.print_line(player.name + ' is in a room with no name.')
                self.print_line('It looks like:\n' + player.room.description or '?')
        else:
            self.print_line('I couldn\'t find ' + name + '.')

    def take(self, name=None):
        if name not in self.room.contents:
            self.print_line('There is no ' + name + ' here.')
            return
        self.contents[name] = self.room.contents[name]
        del self.room.contents[name]
        self.print_line('You take ' + name + '.')
        self.room.print_line(self, self.name + ' takes ' + name + '.', exclude_player=True)

    def drop(self, name=None):
        if name not in self.contents:
            self.print_line('You are not carrying ' + name + '.')
            return
        self.room.contents[name] = self.contents[name]
        del self.contents[name]
        self.print_line('You drop ' + name + '.')
        self.room.print_line(self, self.name + ' drops ' + name + '.', exclude_player=True)


## Objects
class Object:
    name = None
    description = None

class Ball(Object):
    name = 'ball'
    description = 'A super bouncy red rubber ball.'

ball = Ball()

rainbox = Object()
rainbox.description = 'A small wooden box with a metal lock, with water seeping out of its edges.'

waterfall = Object()
waterfall.description = 'A beautiful waterfall with a glorious rainbow behind it.'

hotdog = Object()
hotdog.description = 'Hotdog, hotdog, hot-diggity-dog.'


## Shell

class Shell(cmd.Cmd):
    intro = 'Welcome to MonkaMOO!'
    prompt = ''
    file = None
    use_rawinput = 0
    player = None

    shortcuts = {
        '"': 'say',
        '@': 'tell',
        ':': 'emote',
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
            self.player.parse_command(arg)

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

world = World()
world.load()

world.rooms['0'].contents['ball'] = ball
world.rooms['0'].contents['waterfall'] = waterfall
world.rooms['0'].contents['hotdog'] = hotdog
world.find_room('attic').contents['rainbox'] = rainbox

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
