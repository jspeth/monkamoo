#!/usr/bin/env python -i

import json
import uuid

## World
class World:
    path = "world.json"

    def __init__(self):
        self.rooms = {"0": Room(id="0", description="This is the beginning of the world.")}

    def load(self):
        data = open(self.path, "r").read()
        world = json.loads(data)
        rooms = {}
        for room_id, room_dict in world["rooms"].iteritems():
            rooms[room_id] = Room(**room_dict)
        self.rooms = rooms

    def save(self):
        data = json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=2, separators=(',', ': '))
        with open(self.path, "w") as f:
            f.write(data)


## Room
class Room:
    def __init__(self, id=None, name=None, description=None, exits=None):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.exits = exits or {}

    def look(self):
        if self.name:
            print "* " + self.name + " *"
        print self.description or "You see nothing here."
        if self.exits:
            directions = self.exits.keys()
            if len(directions) == 1:
                # one direction: "You can go up."
                print "You can go " + directions[0] + "."
            elif len(directions) == 2:
                # two directions: "You can go east or west."
                print "You can go " + directions[0] + " or " + directions[1] + "."
            else:
                # lots of directions: "You can go up, east, or west."
                print "You can go " + ", ".join(directions[:-1]) + ", or " + directions[-1] + "."


## Commands

def load():
    world.load()

def save():
    world.save()

def look():
    here.look()

def name(name=None):
    if name:
        here.name = name
    else:
        if here.name:
            print "* " + here.name + " *"
        else:
            print "This room has no name."

def describe(description=None):
    if description:
        here.description = description
    else:
        if here.description:
            print here.description
        else:
            print "This room has no description."

def go(direction):
    global here
    if direction in here.exits:
        here = world.rooms[here.exits[direction]]
        here.look()
    else:
        print "You can't go that way."

def dig(direction, back="back"):
    global here
    new_room = Room(exits={back: here.id})
    world.rooms[new_room.id] = new_room
    here.exits[direction] = new_room.id
    here = new_room


## Start MonkaMOO

print "Welcome to MonkaMOO!"

world = World()
world.load()
here = world.rooms["0"]
here.look()
