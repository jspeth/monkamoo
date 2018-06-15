#!/usr/bin/env python

import argparse
import click
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
        room_id = player.room_id or '0'
        player.room_id = room_id
        self.rooms[room_id].players[player.id] = player

    def move_player(self, player, new_room):
        old_room = self.rooms[player.room_id]
        del old_room.players[player.id]
        new_room.players[player.id] = player

    def find_player(self, name):
        for player in self.players.values():
            if player.name == name:
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

    def print_line(self, player, message):
        for other in self.players.values():
            other.print_line(message)

    def look(self, player):
        if self.name:
            player.print_line('* ' + self.name + ' *')
        player.print_line(self.description or 'You see nothing here.')
        if self.exits:
            directions = self.exits.keys()
            player.print_line('You can go ' + join_strings(directions, 'or') + '.')
        if self.players:
            names = [other.name for other in self.players.values()]
            isAre = len(self.players) > 1 and 'are' or 'is'
            player.print_line(join_strings(names, 'and') + ' ' + isAre + ' here.')

    def go(self, player, direction=None):
        if direction in self.exits:
            room = world.rooms[self.exits[direction]]
            world.move_player(player, room)
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

    def set_name(self, player, name=None):
        if name:
            self.name = name
        elif self.name:
            player.print_line('* ' + self.name + ' *')
        else:
            player.print_line('This room has no name.')

    def set_description(self, player, description=None):
        if description:
            self.description = description
        elif self.description:
            player.print_line(self.description)
        else:
            player.print_line('This room has no description.')


## Player
class Player:
    def __init__(self, id=None, name=None, description=None, room_id=None):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.room_id = room_id

    def json_dictionary(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'room_id': self.room_id
        }

    def print_line(self, message):
        if hasattr(self, 'stdout'):
            self.stdout.write(message + '\n')
        else:
            print message

    def get_room(self):
        return world.rooms[self.room_id]

    def look(self):
        self.get_room().look(self)

    def say(self, message):
        self.get_room().print_line(self, self.name + ' says, "' + message + '".')

    def emote(self, message):
        self.get_room().print_line(self, self.name + ' ' + message)

    def set_name(self, name=None):
        self.get_room().set_name(self, name)

    def set_description(self, description=None):
        self.get_room().set_description(self, description)

    def go(self, direction=None):
        room = self.get_room()
        room = room.go(self, direction) or room
        self.room_id = room.id

    def dig(self, direction=None, back='back'):
        room = self.get_room()
        room = room.dig(self, direction, back) or room
        self.room_id = room.id


## Commands

@click.command()
def load():
    world.load()

@click.command()
def save():
    world.save()

@click.command()
def look():
    me.look()

@click.command()
@click.argument('message', required=False)
def say(message=None):
    me.say(message)

@click.command()
@click.argument('message', required=False)
def emote(message=None):
    me.emote(message)

@click.command()
@click.argument('name', required=False)
def name(name=None):
    me.set_name(name)

@click.command()
@click.argument('description', required=False)
def describe(description=None):
    me.set_description(description)

@click.command()
@click.argument('direction', required=False)
def go(direction=None):
    me.go(direction)

@click.command()
@click.argument('direction', required=False)
@click.argument('back', required=False, default='back')
def dig(direction=None, back='back'):
    me.dig(direction, back)

@click.command()
@click.argument('name', required=False)
def player(name=None):
    global me
    if name is None:
        return
    player = world.find_player(name)
    if player:
        me = player
    else:
        me = Player(name=name)
        world.add_player(me)


## Start MonkaMOO

world = World()
world.load()

charlotte = world.find_player('Charlotte')
jim = world.find_player('Jim')
me = jim


## Command Parsing

@click.group()
def cli():
    pass

@click.command()
def interact():
    # see https://docs.python.org/2/library/code.html?highlight=interpreter
    code.interact(local=globals())

@click.command()
def help():
    print 'help'

@click.command()
def quit():
    sys.exit(0)

for command in [interact, help, quit]:
    cli.add_command(command)

for command in [load, save, look, say, emote, name, describe, go, dig, player]:
    cli.add_command(command)


## Shell

class Shell(cmd.Cmd):
    intro = 'Welcome to MonkaMOO!'
    prompt = 'moo> '
    file = None
    use_rawinput = 0

    def do_pass(self, arg):
        pass

    def precmd(self, line):
        if line == 'EOF':
            print
            sys.exit(0)
        args = line.split(' ')
        try:
            me.stdout = self.stdout
            cli.main(args, standalone_mode=False)
        except click.UsageError as ex:
            me.print_line('I didn\'t understand that.')
        except Exception as ex:
            me.print_line('Error: ' + `ex`)
        return 'pass'


## Launch

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
        Shell().cmdloop()

if __name__ == '__main__':
    main()
