import json
from pathlib import Path

from .. import line_parser
from ..logging_config import get_logger
from .aiplayer import AIPlayer
from .ball import Ball
from .base import Base
from .object import Object
from .player import Player
from .room import Room

# These imports are used dynamically via globals() lookup in the load() method
__all__ = ["AIPlayer", "Ball", "Base", "Object", "Player", "Room", "World"]

# Get logger for this module
logger = get_logger("monkamoo.world")


class World(Base):
    """The root container of all MOO objects."""

    shortcuts = {'"': "say", ":": "emote", "@": "whisper", "#": "jump"}

    def __init__(self, path=None, **kwargs):
        super().__init__(**kwargs)
        self.path = path
        if not self.contents:
            self.contents = {"0": Room(id="0", description="This is the beginning of the world.")}

    def json_dictionary(self):
        return {"contents": self.contents}

    def load(self, path=None):
        path = path or self.path
        logger.info("Loading world from: %s", path)
        with Path(path).open() as f:
            data = f.read()
        if not data:
            logger.warning("No data found in world file: %s", path)
            return
        world = json.loads(data)
        all_contents = {}
        loaded_objects = 0
        for object_dict in world.get("contents", {}).values():
            # get object class
            class_name = object_dict.get("type")
            cls = globals().get(class_name)
            if not cls:
                logger.error("Class not found: %s", class_name)
                continue
            del object_dict["type"]
            # create object, building contents map
            obj = cls(**object_dict)
            if obj.location:
                contents = all_contents.setdefault(obj.location, {})
                contents[obj.id] = obj
            self.add(obj)
            loaded_objects += 1
        # update objects with their contents
        for id, contents in iter(all_contents.items()):
            if id in self.contents:
                self.contents[id].contents = contents
        # replace location id with object
        for obj in self.contents.values():
            if obj.location and obj.location in self.contents:
                obj.location = self.contents[obj.location]
        logger.info("World loaded successfully: %d objects", loaded_objects)

    def save(self, path=None):
        path = path or self.path
        logger.info("Saving world to: %s", path)
        data = json.dumps(self, default=lambda o: o.json_dictionary(), sort_keys=True, indent=2, separators=(",", ": "))
        with Path(path).open("w") as f:
            f.write(data)
        logger.info("World saved successfully")

    def add(self, obj):
        if not hasattr(obj, "id"):
            raise ValueError
        self.contents[obj.id] = obj
        obj.world = self

    def add_player(self, player):
        logger.info("Adding player to world: %s", player.name)
        self.add(player)
        if not player.location:
            player.location = self.contents["0"]
        player.location.contents[player.id] = player
        logger.info("Player %s added to room: %s", player.name, player.location.id)

    def parse_command(self, player, line):
        logger.debug("Parsing command for player %s: %s", player.name, line)
        for key in self.shortcuts:
            if line.startswith(key):
                line = self.shortcuts[key] + " " + line.strip(key + " ")
                break
        command = line_parser.Parser.parse(line)
        if not command:
            logger.debug("Command not understood: %s", line)
            player.tell("I didn't understand that.")
            return
        command.resolve(self, player)
        self.handle_command(command)

    def handle_command(self, command):
        func = self.find_function(command)
        if not func:
            logger.debug("No function found for command: %s", command.verb)
            command.player.tell("I didn't understand that.")
            return
        logger.debug("Executing command: %s for player %s", command.verb, command.player.name)
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
