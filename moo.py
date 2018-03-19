#!/usr/bin/env python -i

import json
import uuid

WORLD = {}
CURRENT = WORLD

def load(path="world.json"):
    global WORLD
    global CURRENT
    data = open(path, "r").read()
    WORLD = json.loads(data)
    CURRENT = WORLD["rooms"][WORLD["start"]]

def save(path="world.json", world=None):
    if world is None:
        world = WORLD
    data = json.dumps(world, sort_keys=True, indent=4, separators=(',', ': '))
    f = open(path, "w")
    f.write(data)
    f.close()

def look(room=None):
    if room is None:
        room = CURRENT
    name = room.get("name")
    if name:
        print "* " + name + " *"
    description = room.get("description", "You see nothing here.")
    if description:
        print description
    exits = room.get("exits")
    if exits:
        print "You can go " + ", ".join(exits.keys()) + "."

def name(name=None, room=None):
    if room is None:
        room = CURRENT
    if name is None:
        name = room.get("name")
        if name:
            print "* " + name + " *"
        else:
            print "This room has no name."
    else:
        room["name"] = name

def describe(description=None, room=None):
    if room is None:
        room = CURRENT
    if description is None:
        description = room.get("description")
        if description:
            print description
        else:
            print "This room has no description."
    else:
        room["description"] = description

def go(direction, room=None):
    global CURRENT
    if room is None:
        room = CURRENT
    exits = room.setdefault("exits", {})
    if direction in exits:
        CURRENT = WORLD["rooms"][exits[direction]]
        look()
    else:
        print "You can't go that way."

def dig(direction, back="back", room=None):
    global CURRENT
    if room is None:
        room = CURRENT
    new_room = {"id": str(uuid.uuid4()), "exits": {back: room["id"]}}
    WORLD["rooms"][new_room["id"]] = new_room
    exits = room.setdefault("exits", {})
    exits[direction] = new_room["id"]
    CURRENT = new_room

print "Welcome!"
