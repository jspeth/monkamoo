#!/usr/bin/env python

import argparse
import cmd
import json
import sys
import uuid

import interpreter
import server

def join_strings(items, conj='and'):
    """ Return a string by joining the items with the conjunction. """
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return '{first} {conj} {last}'.format(first=items[0], last=items[1], conj=conj)
    return '{list}, {conj} {last}'.format(list=', '.join(items[:-1]), last=items[-1], conj=conj)


class World:
    """ The root container of all MOO objects. """

    path = 'world.json'

    def __init__(self):
        self.rooms = {'0': Room(id='0', description='This is the beginning of the world.')}
        self.players = {}
        self.objects = {}

    def json_dictionary(self):
        return {'rooms': self.rooms, 'players': self.players, 'objects': self.objects}

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
        # objects
        if 'objects' in world:
            for object_id, object_dict in world['objects'].iteritems():
                cls = Object
                if 'type' in object_dict:
                    cls = globals().get(object_dict['type'])
                    del object_dict['type']
                self.add_object(cls(**object_dict))

    def save(self):
        data = json.dumps(self, default=lambda o: o.json_dictionary(), sort_keys=True, indent=2, separators=(',', ': '))
        with open(self.path, 'w') as f:
            f.write(data)

    def get_location(self, location_id):
        if location_id in self.rooms:
            return self.rooms[location_id]
        if location_id in self.players:
            return self.players[location_id]
        return None

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

    def add_object(self, obj):
        if obj.id not in self.objects:
            self.objects[obj.id] = obj
        if not obj.location:
            obj.location = self.rooms['0']
        obj.location.contents[obj.name] = obj


class Room:
    """ Represents a room containing players and objects, with exits to other rooms. """

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

    def announce(self, player, message, exclude_player=False):
        for other in self.players.values():
            if exclude_player and other is player:
                continue
            other.tell(message)

    def on_enter(self, player, direction=None):
        self.announce(player, '{name} enters the room.'.format(name=player.name), exclude_player=True)
        self.look(player)

    def on_exit(self, player, direction=None):
        if direction:
            message = '{name} exits {direction}.'.format(name=player.name, direction=direction)
        else:
            message = '{name} exits the room.'.format(name=player.name)
        self.announce(player, message, exclude_player=True)

    def look(self, player):
        if self.name:
            player.tell('*** {name} ***'.format(name=self.name))
        player.tell(self.description or 'You see nothing here.')
        if self.exits:
            directions = self.exits.keys()
            player.tell('You can go {directions}.'.format(directions=join_strings(directions, 'or')))
        players = [p for p in self.players.values() if p != player]
        if players:
            names = [p.name for p in players]
            player.tell('{names} {are} here.'.format(names=join_strings(names, 'and'), are=len(players) > 1 and 'are' or 'is'))
        if self.contents:
            player.tell('There is {contents} here.'.format(contents=join_strings(self.contents.keys(), 'and')))

    def do_name(self, player, name=None):
        if name:
            self.name = name
        elif self.name:
            player.tell('*** {name} ***'.format(name=self.name))
        else:
            player.tell('This room has no name.')

    def do_describe(self, player, description=None):
        if description:
            self.description = description
        elif self.description:
            player.tell(self.description)
        else:
            player.tell('This room has no description.')


class Player:
    """ Represents a participant in the MOO. """

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

    def tell(self, message):
        if self.stdout:
            self.stdout.write(message + '\n')
            self.stdout.flush()

    def get_verb(self, verb):
        for key in [verb, 'do_' + verb]:
            method = getattr(self, key, None)
            if method and callable(method):
                return method
        return None

    def find_verb(self, verb):
        search_path = [self] + self.contents.values() + self.room.contents.values()
        for obj in search_path:
            method = obj.get_verb(verb)
            if method:
                return method
        return None

    def parse_command(self, line):
        args = line.split(' ', 1)
        verb = self.find_verb(args[0])
        if verb:
            arg = len(args) > 1 and args[1] or None
            verb(arg)
        else:
            self.tell('I didn\'t understand that.')

    def set_room(self, room, direction=None):
        self.room.on_exit(self, direction)
        del self.room.players[self.id]
        self.room = room
        room.players[self.id] = self
        room.on_enter(self)

    def go(self, direction=None):
        if direction not in self.room.exits:
            self.tell('You can\'t go that way.')
            return
        room = world.rooms[self.room.exits[direction]]
        self.set_room(room, direction)

    def jump(self, room_name=None):
        room = world.find_room(room_name)
        if not room:
            self.tell('I couldn\'t find {name}.'.format(name=room_name))
            return
        self.set_room(room)

    def dig(self, direction=None, back='back'):
        if direction is None:
            self.tell('You must give a direction.')
            return
        if direction in self.room.exits:
            self.tell('That direction already exists.')
            return
        room = Room(exits={back: self.room.id})
        world.rooms[room.id] = room
        self.room.exits[direction] = room.id
        self.set_room(room, direction)

    def look(self, name=None):
        if name is None or name == 'here':
            self.room.look(self)
        elif name == 'me' or name == self.name:
            self.tell(self.description or 'You see nothing special.')
            if self.contents:
                self.tell('You have {contents}.'.format(contents=join_strings(self.contents.keys(), 'and')))
        elif name in self.contents:
            obj = self.contents[name]
            self.tell(obj.description or 'You see nothing special.')
        elif name in self.room.contents:
            obj = self.room.contents[name]
            self.tell(obj.description or 'You see nothing special.')
        else:
            self.tell('There is no {name} here.'.format(name=name))

    def do_name(self, name=None):
        self.room.do_name(self, name)

    def do_describe(self, description=None):
        self.room.do_describe(self, description)

    def say(self, message=None):
        if message:
            self.room.announce(self, '{name} says, "{message}"'.format(name=self.name, message=message))

    def whisper(self, message=None):
        parts = message.split(' ', 1)
        if len(parts) < 2:
            self.tell('What do you want to tell them?')
            return
        name, message = parts
        player = world.find_player(name)
        if player and message:
            player.tell('{name} whispers, "{message}"'.format(name=self.name, message=message))

    def emote(self, message=None):
        if message:
            self.room.announce(self, '{name} {message}'.format(name=self.name, message=message))

    def find(self, name=None):
        player = world.find_player(name)
        if player and player.room:
            if player.room.name:
                self.tell('{name} is in {room}.'.format(name=player.name, room=player.room.name))
            else:
                self.tell('{name} is in a room with no name.'.format(name=player.name))
                self.tell('It looks like:\n{description}'.format(description=player.room.description or '?'))
        else:
            self.tell('I couldn\'t find {name}.'.format(name=name))

    def take(self, name=None):
        if name not in self.room.contents:
            self.tell('There is no {name} here.'.format(name=name))
            return
        self.contents[name] = self.room.contents[name]
        self.contents[name].location = self
        del self.room.contents[name]
        self.tell('You take {name}.'.format(name=name))
        self.room.announce(self, '{player} takes {name}.'.format(player=self.name, name=name), exclude_player=True)

    def drop(self, name=None):
        if name not in self.contents:
            self.tell('You are not carrying {name}.'.format(name=name))
            return
        self.room.contents[name] = self.contents[name]
        self.room.contents[name].location = self.room
        del self.contents[name]
        self.tell('You drop {name}.'.format(name=name))
        self.room.announce(self, '{player} drops {name}.'.format(player=self.name, name=name), exclude_player=True)


class Object:
    """ The root class of all MOO objects. """

    name = None
    description = None
    location = None

    def __init__(self, id=None, name=None, description=None, location_id=None):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.location = location_id and world.get_location(location_id) or None

    def json_dictionary(self):
        return {
            'type': self.__class__.__name__,
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'location_id': self.location and self.location.id or None
        }

    def get_verb(self, verb):
        for key in [verb, 'do_' + verb]:
            method = getattr(self, key, None)
            if method and callable(method):
                return method
        return None


class Ball(Object):
    """ A simple ball. """

    name = 'ball'
    description = 'A super bouncy red rubber ball.'

    def __init__(self, id=None, name=None, description=None, location_id=None):
        if name is None:
            name = Ball.name
        if description is None:
            description = Ball.description
        Object.__init__(self, id, name, description, location_id)

    def bounce(self, player):
        room = self.location
        if hasattr(self.location, 'room'):
            room = self.location.room
        room.announce(player, 'The ball bounces up and down.')

    def roll(self, player):
        room = self.location
        if hasattr(self.location, 'room'):
            room = self.location.room
        room.announce(player, 'The ball rolls away.')


class Shell(cmd.Cmd):
    """ A command shell for processing user input and executing MOO commands. """

    intro = 'Welcome to MonkaMOO!'
    prompt = ''
    file = None
    use_rawinput = 0
    player = None

    shortcuts = {
        '"': 'say',
        '@': 'whisper',
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
