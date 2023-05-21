import threading
import uuid

from parser import Preposition
from utils import join_strings

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

    def __nonzero__(self):
        return True

    def __len__(self):
        return len(self.contents)

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
        return [obj for obj in self if isinstance(obj, Room)]

    @property
    def players(self):
        return [obj for obj in self if isinstance(obj, Player)]

    @property
    def things(self):
        return [obj for obj in self if not isinstance(obj, Player)]

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

    def get_function(self, verb):
        for key in [verb, 'do_' + verb]:
            method = getattr(self, key, None)
            if method and callable(method):
                return method
        return None

    def tell(self, message=None):
        pass

    def timer(self, interval, function, args=[], kwargs={}):
        return threading.Timer(interval, function, args, kwargs).start()


class Room(Base):
    """ Represents a room containing players and objects, with exits to other rooms. """

    def __init__(self, **kwargs):
        self.exits = {}
        super(Room, self).__init__(**kwargs)

    def json_dictionary(self):
        return dict(super(Room, self).json_dictionary(), **{
            'exits': self.exits
        })

    def announce(self, player, message, exclude_player=False):
        for obj in self:
            if exclude_player and obj is player:
                continue
            obj.tell(message)

    def on_enter(self, player, direction=None):
        if not isinstance(player, Player):
            return
        self.announce(player, '{name} enters the room.'.format(name=player.name), exclude_player=True)
        self.look(player)

    def on_exit(self, player, direction=None):
        if not isinstance(player, Player):
            return
        if direction:
            message = '{name} exits {direction}.'.format(name=player.name, direction=direction)
        else:
            message = '{name} exits the room.'.format(name=player.name)
        self.announce(player, message, exclude_player=True)

    def say(self, command):
        player = command.player
        message = command.args_str
        if player and message:
            self.announce(player, '{name} says, "{message}"'.format(name=player.name, message=message))

    def emote(self, command):
        player = command.player
        message = command.args_str
        if message:
            self.announce(player, '{name} {message}'.format(name=player.name, message=message))

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

    def go(self, command):
        player = command.player
        direction = command.direct_object_str
        if direction not in self.exits:
            player.tell('You can\'t go that way.')
            return
        room = self.world.contents[self.exits[direction]]
        player.move(room, direction)

    def dig(self, command):
        player = command.player
        direction = command.direct_object_str
        back = command.indirect_object_str or 'back'
        if not direction:
            player.tell('You must give a direction.')
            return
        if direction in self.exits:
            player.tell('That direction already exists.')
            return
        room = Room(exits={back: self.id})
        self.world.add(room)
        self.exits[direction] = room.id
        player.move(room, direction)


class Player(Base):
    """ Represents a participant in the MOO. """

    def __init__(self, **kwargs):
        self.stdout = None
        super(Player, self).__init__(**kwargs)

    def tell(self, message):
        if self.stdout:
            self.stdout.write(message + '\n')
            self.stdout.flush()

    def jump(self, command):
        room_name = command.direct_object_str
        room = self.world.find_room(room_name)
        if not room:
            self.tell('I couldn\'t find {name}.'.format(name=room_name))
            return
        self.move(room)

    def look(self, command):
        obj = command.direct_object
        # special case "look at object"
        if command.preposition == Preposition.AT and command.indirect_object:
            obj = command.indirect_object
        # check if the object was named but not found
        if obj is None and command.direct_object_str:
            self.tell('There is no {name} here.'.format(name=command.direct_object_str))
            return
        # look at the object
        if obj is None or obj == self.location:
            self.location.look(self)
        elif obj == self:
            self.tell(self.description or 'You see nothing special.')
            thing_names = [o.name for o in self.things]
            if thing_names:
                self.tell('You have {names}.'.format(names=join_strings(thing_names, 'and')))
        else:
            self.tell(obj.description or 'You see nothing special.')

    def do_name(self, command):
        if command.direct_object is None or command.preposition != Preposition.AS or not command.indirect_object_str:
            self.tell('I didn\'t understand that.')
            return
        command.direct_object.name = command.indirect_object_str

    def do_describe(self, command):
        if command.direct_object is None or command.preposition != Preposition.AS or not command.indirect_object_str:
            self.tell('I didn\'t understand that.')
            return
        command.direct_object.description = command.indirect_object_str

    def whisper(self, command):
        parts = command.args_str.split(' ', 1)
        if len(parts) < 2:
            self.tell('What do you want to tell them?')
            return
        name, message = parts
        player = self.world.find_player(name)
        if player and message:
            player.tell('{name} whispers, "{message}"'.format(name=self.name, message=message))

    def find(self, command):
        name = command.direct_object_str
        player = self.world.find_player(name)
        if player and player.location:
            if player.location.name:
                self.tell('{name} is in {room}.'.format(name=player.name, room=player.location.name))
            else:
                self.tell('{name} is in a room with no name.'.format(name=player.name))
                self.tell('It looks like:\n{description}'.format(description=player.location.description or '?'))
        else:
            self.tell('I couldn\'t find {name}.'.format(name=name))

    def create(self, command):
        """ create Object as flower """
        class_name = command.direct_object_str
        name = 'something'
        if command.preposition == Preposition.AS and command.indirect_object_str:
            name = command.indirect_object_str
        cls = globals().get(class_name)
        if not cls:
            self.tell('I couldn\'t find {class_name}.'.format(class_name=class_name))
            return
        # create object
        obj = cls(name=name)
        obj.move(self)
        self.tell('You created {name}.'.format(name=name))


class Object(Base):
    """ Represents a thing that can be picked up and put down. """

    def take(self, command):
        player = command.player
        self.move(player)
        player.tell('You take {name}.'.format(name=self.name))
        self.room.announce(player, '{player} takes {name}.'.format(player=player.name, name=self.name), exclude_player=True)

    def drop(self, command):
        player = command.player
        self.move(player.room)
        player.tell('You drop {name}.'.format(name=self.name))
        self.room.announce(player, '{player} drops {name}.'.format(player=player.name, name=self.name), exclude_player=True)
