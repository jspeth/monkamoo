#!/usr/bin/env python

import argparse
import cmd
import json
import sys
import uuid

import interpreter
import server
from utils import join_strings

class Object(object):
    """ The root class of all MOO objects. """

    def __init__(self, **kwargs):
        self.id = str(uuid.uuid4())
        self.name = None
        self.description = None
        self.location = None
        self.contents = {}
        self.__dict__.update(kwargs)

    def __repr__(self):
        return '<%s 0x%x name="%s">' % (self.__class__.__name__, id(self), self.name)

    def json_dictionary(self):
        return {
            'type': self.__class__.__name__,
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'location': self.location and self.location.id or None
        }

    @property
    def room(self):
        if isinstance(self, Room):
            return self
        if self.location:
            return self.location.room
        return None

    @property
    def player(self):
        if isinstance(self, Player):
            return self
        if self.location:
            return self.location.player
        return None

    @property
    def rooms(self):
        return [obj for obj in self.contents.values() if isinstance(obj, Room)]

    @property
    def players(self):
        return [obj for obj in self.contents.values() if isinstance(obj, Player)]

    @property
    def things(self):
        return [obj for obj in self.contents.values() if not isinstance(obj, Player)]

    def find_room(self, name):
        for room in self.rooms:
            if room.name and room.name.lower() == name.lower():
                return room
        return None

    def find_player(self, name):
        for player in self.players:
            if player.name.lower() == name.lower():
                return player
        return None

    def find_thing(self, name):
        for obj in self.things:
            if obj.name.lower() == name.lower():
                return obj
        return None

    def get_verb(self, verb):
        for key in [verb, 'do_' + verb]:
            method = getattr(self, key, None)
            if method and callable(method):
                return method
        return None


class World(Object):
    """ The root container of all MOO objects. """

    path = 'world.json'

    def __init__(self, **kwargs):
        self.contents = {'0': Room(id='0', description='This is the beginning of the world.')}
        super(World, self).__init__(**kwargs)

    def json_dictionary(self):
        return {'contents': self.contents}

    def load(self):
        data = open(self.path, 'r').read()
        world = json.loads(data)
        all_contents = {}
        for object_dict in world.get('contents', {}).values():
            # get object class
            cls = globals().get(object_dict.get('type'))
            if not cls:
                continue
            del object_dict['type']
            # create object, building contents map
            obj = cls(**object_dict)
            if obj.location:
                contents = all_contents.setdefault(obj.location, {})
                contents[obj.id] = obj
            self.contents[obj.id] = obj
        # update objects with their contents
        for id, contents in all_contents.iteritems():
            self.contents[id].contents = contents
        # replace location id with object
        for obj in self.contents.values():
            if obj.location:
                obj.location = self.contents[obj.location]

    def save(self):
        data = json.dumps(self, default=lambda o: o.json_dictionary(), sort_keys=True, indent=2, separators=(',', ': '))
        with open(self.path, 'w') as f:
            f.write(data)

    def add_player(self, player):
        self.contents[player.id] = player
        if not player.location:
            player.location = self.contents['0']
        player.location.contents[player.id] = player


class Room(Object):
    """ Represents a room containing players and objects, with exits to other rooms. """

    def __init__(self, **kwargs):
        self.exits = {}
        super(Room, self).__init__(**kwargs)

    def json_dictionary(self):
        return dict(super(Room, self).json_dictionary(), **{
            'exits': self.exits
        })

    def announce(self, player, message, exclude_player=False):
        for other in self.players:
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
        # show name and description
        if self.name:
            player.tell('*** {name} ***'.format(name=self.name))
        player.tell(self.description or 'You see nothing here.')
        # show exits
        if self.exits:
            directions = self.exits.keys()
            player.tell('You can go {directions}.'.format(directions=join_strings(directions, 'or')))
        # show other players
        players = [p.name for p in self.players if p != player]
        if players:
            player.tell('{players} {are} here.'.format(players=join_strings(players, 'and'), are=len(players) > 1 and 'are' or 'is'))
        # show room contents
        things = [o.name for o in self.things]
        if things:
            player.tell('There is {names} here.'.format(names=join_strings(things, 'and')))

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


class Player(Object):
    """ Represents a participant in the MOO. """

    def __init__(self, **kwargs):
        self.stdout = None
        super(Player, self).__init__(**kwargs)

    def tell(self, message):
        if self.stdout:
            self.stdout.write(message + '\n')
            self.stdout.flush()

    def find_verb(self, verb):
        search_path = [self] + self.contents.values() + self.location.contents.values()
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
        self.location.on_exit(self, direction)
        del self.location.contents[self.id]
        self.location = room
        room.contents[self.id] = self
        room.on_enter(self)

    def go(self, direction=None):
        if direction not in self.location.exits:
            self.tell('You can\'t go that way.')
            return
        room = world.contents[self.location.exits[direction]]
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
        if direction in self.location.exits:
            self.tell('That direction already exists.')
            return
        room = Room(exits={back: self.location.id})
        world.contents[room.id] = room
        self.location.exits[direction] = room.id
        self.set_room(room, direction)

    def look(self, name=None):
        # look at room
        if name is None or name == 'here':
            self.location.look(self)
            return
        # look at self
        if name == 'me' or name.lower() == self.name.lower():
            self.tell(self.description or 'You see nothing special.')
            thing_names = [o.name for o in self.things]
            if thing_names:
                self.tell('You have {names}.'.format(names=join_strings(thing_names, 'and')))
            return
        # look at an object
        obj = self.find_thing(name) or self.location.find_thing(name)
        if obj:
            self.tell(obj.description or 'You see nothing special.')
        else:
            self.tell('There is no {name} here.'.format(name=name))

    def do_name(self, name=None):
        self.location.do_name(self, name)

    def do_describe(self, description=None):
        self.location.do_describe(self, description)

    def say(self, message=None):
        if message:
            self.location.announce(self, '{name} says, "{message}"'.format(name=self.name, message=message))

    def emote(self, message=None):
        if message:
            self.location.announce(self, '{name} {message}'.format(name=self.name, message=message))

    def whisper(self, message=None):
        parts = message.split(' ', 1)
        if len(parts) < 2:
            self.tell('What do you want to tell them?')
            return
        name, message = parts
        player = world.find_player(name)
        if player and message:
            player.tell('{name} whispers, "{message}"'.format(name=self.name, message=message))

    def find(self, name=None):
        player = world.find_player(name)
        if player and player.location:
            if player.location.name:
                self.tell('{name} is in {room}.'.format(name=player.name, room=player.location.name))
            else:
                self.tell('{name} is in a room with no name.'.format(name=player.name))
                self.tell('It looks like:\n{description}'.format(description=player.location.description or '?'))
        else:
            self.tell('I couldn\'t find {name}.'.format(name=name))

    def take(self, name=None):
        obj = self.location.find_thing(name)
        if not obj:
            self.tell('There is no {name} here.'.format(name=name))
            return
        self.contents[obj.id] = obj
        obj.location = self
        del self.location.contents[obj.id]
        self.tell('You take {name}.'.format(name=name))
        self.location.announce(self, '{player} takes {name}.'.format(player=self.name, name=name), exclude_player=True)

    def drop(self, name=None):
        obj = self.find_thing(name)
        if not obj:
            self.tell('You are not carrying {name}.'.format(name=name))
            return
        self.location.contents[obj.id] = obj
        obj.location = self.location
        del self.contents[obj.id]
        self.tell('You drop {name}.'.format(name=name))
        self.location.announce(self, '{player} drops {name}.'.format(player=self.name, name=name), exclude_player=True)


class Ball(Object):
    """ A simple ball. """

    def bounce(self, player):
        if self.room:
            self.room.announce(player, 'The ball bounces up and down.')

    def roll(self, player):
        if self.room:
            self.room.announce(player, 'The ball rolls away.')


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
