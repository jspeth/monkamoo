import asyncio
import uuid

class Base(object):
    """ The base class of all MOO objects. """

    def __init__(self, **kwargs):
        self.id = str(uuid.uuid4())
        self.world = None
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

    def __contains__(self, obj):
        return hasattr(obj, 'id') and obj.id in self.contents

    def __iter__(self):
        return iter(self.contents.values())

    def __iadd__(self, obj):
        self.add(obj)
        return self

    def __isub__(self, obj):
        self.remove(obj)
        return self

    def add(self, obj):
        if not hasattr(obj, 'id'):
            raise ValueError()
        self.world.add(obj)
        self.contents[obj.id] = obj

    def remove(self, obj):
        if not hasattr(obj, 'id'):
            raise ValueError()
        del self.contents[obj.id]

    def move(self, location, direction=None):
        if not location.accept(self):
            return False
        if self.location:
            self.location.on_exit(self, direction)
            self.location -= self
        self.location = location
        if self.location:
            self.location += self
            self.location.on_enter(self, direction)
        return True

    def accept(self, obj):
        return True

    def on_enter(self, obj, direction=None):
        pass

    def on_exit(self, obj, direction=None):
        pass

    @property
    def room(self):
        from .room import Room
        if isinstance(self, Room):
            return self
        if self.location:
            return self.location.room
        return None

    @property
    def player(self):
        from .player import Player
        if isinstance(self, Player):
            return self
        if self.location:
            return self.location.player
        return None

    @property
    def rooms(self):
        from .room import Room
        return [obj for obj in self if isinstance(obj, Room)]

    @property
    def players(self):
        from .player import Player
        return [obj for obj in self if isinstance(obj, Player)]

    @property
    def things(self):
        from .player import Player
        return [obj for obj in self if not isinstance(obj, Player)]

    def find_room(self, name):
        # Allow using `@Player` to find the room the player is in
        if name.startswith('@'):
            player = self.find_player(name.strip('@'))
            if player:
                return player.location
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

    def get_function(self, verb):
        for key in [verb, 'do_' + verb]:
            method = getattr(self, key, None)
            if method and callable(method):
                return method
        return None

    def tell(self, message=None):
        pass

    def timer(self, interval, function, args=[], kwargs={}):
        async def perform_after():
            await asyncio.sleep(interval)
            function(*args, **kwargs)
        asyncio.create_task(perform_after())
