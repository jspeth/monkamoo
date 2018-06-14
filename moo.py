#!/usr/bin/env python

import argparse
import click
import cmd
import code
import json
import sys
import uuid

import server

## World
class World:
    path = 'world.json'

    def __init__(self):
        self.rooms = {'0': Room(id='0', description='This is the beginning of the world.')}
        self.players = {}

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
        data = json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=2, separators=(',', ': '))
        with open(self.path, 'w') as f:
            f.write(data)

    def add_player(self, player):
        if player.id not in self.players:
            self.players[player.id] = player
        room_id = player.room or '0'
        player.room = room_id
        self.rooms[room_id].players[player.id] = player

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

    def look(self):
        if self.name:
            print '* ' + self.name + ' *'
        print self.description or 'You see nothing here.'
        if self.exits:
            directions = self.exits.keys()
            if len(directions) == 1:
                # one direction: 'You can go up.'
                print 'You can go ' + directions[0] + '.'
            elif len(directions) == 2:
                # two directions: 'You can go east or west.'
                print 'You can go ' + directions[0] + ' or ' + directions[1] + '.'
            else:
                # lots of directions: 'You can go up, east, or west.'
                print 'You can go ' + ', '.join(directions[:-1]) + ', or ' + directions[-1] + '.'

    def go(self, direction=None):
        if direction in self.exits:
            room = world.rooms[self.exits[direction]]
            room.look()
            return room
        else:
            print "You can't go that way."

    def dig(self, direction=None, back='back'):
        if direction is None:
            print 'You must give a direction.'
        elif direction in self.exits:
            print 'That direction already exists.'
        else:
            room = Room(exits={back: self.id})
            world.rooms[room.id] = room
            self.exits[direction] = room.id
            return room

    def set_name(self, name=None):
        if name:
            self.name = name
        elif self.name:
            print '* ' + self.name + ' *'
        else:
            print 'This room has no name.'

    def set_description(self, description=None):
        if description:
            self.description = description
        elif self.description:
            print self.description
        else:
            print 'This room has no description.'


## Player
class Player:
    def __init__(self, id=None, name=None, description=None, room=None):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.room = room

    def say(self, message):
        print self.name + ' says, \'' + message + '\''

    def emote(self, message):
        print self.name + ' ' + message


## Commands

@click.command()
def load():
    world.load()

@click.command()
def save():
    world.save()

@click.command()
def look():
    here.look()

@click.command()
@click.argument('name', required=False)
def name(name=None):
    here.set_name(name)

@click.command()
@click.argument('description', required=False)
def describe(description=None):
    here.set_description(description)

@click.command()
@click.argument('direction', required=False)
def go(direction=None):
    global here
    here = here.go(direction) or here

@click.command()
@click.argument('direction', required=False)
@click.argument('back', required=False, default='back')
def dig(direction=None, back='back'):
    global here
    here = here.dig(direction, back) or here


## Start MonkaMOO

world = World()
world.load()
here = world.rooms['0']

#print 'Welcome to MonkaMOO!'
#here.look()

charlotte = world.find_player('Charlotte')
jim = world.find_player('Jim')


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

for command in [load, save, look, name, describe, go, dig]:
    cli.add_command(command)


## Shell

class Shell(cmd.Cmd):
    intro = 'Welcome to MonkaMOO!'
    prompt = 'moo> '
    file = None

    def do_pass(self, arg):
        pass

    def precmd(self, line):
        if line == 'EOF':
            print
            sys.exit(0)
        args = line.split(' ')
        try:
            cli.main(args, standalone_mode=False)
        except:
            pass
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
