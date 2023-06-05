import json
import sys

from ball import Ball
from base import Base
from object import Object
from player import Player
from room import Room

class World(Base):
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
            if obj.location:
                contents = all_contents.setdefault(obj.location, {})
                contents[obj.id] = obj
            self.add(obj)
        # update objects with their contents
        for id, contents in iter(all_contents.items()):
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

    def add(self, obj):
        if not hasattr(obj, 'id'):
            raise ValueError()
        self.contents[obj.id] = obj
        obj.world = self

    def add_player(self, player):
        self.add(player)
        if not player.location:
            player.location = self.contents['0']
        player.location.contents[player.id] = player
