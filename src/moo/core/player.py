from .base import Base

from .ball import Ball
from .object import Object

from ..line_parser import Preposition
from ..utils import join_strings

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
        if not obj and command.direct_object_str:
            self.tell('There is no {name} here.'.format(name=command.direct_object_str))
            return
        # look at the object
        if not obj or obj == self.location:
            self.location.look(self)
        elif obj == self:
            self.tell(self.description or 'You see nothing special.')
            thing_names = [o.name for o in self.things]
            if thing_names:
                self.tell('You have {names}.'.format(names=join_strings(thing_names, 'and')))
        else:
            self.tell(obj.description or 'You see nothing special.')

    def do_name(self, command):
        if not command.direct_object or command.preposition != Preposition.AS or not command.indirect_args:
            self.tell('I didn\'t understand that.')
            return
        command.direct_object.name = command.indirect_args

    def do_describe(self, command):
        if not command.direct_object or command.preposition != Preposition.AS or not command.indirect_args:
            self.tell('I didn\'t understand that.')
            return
        command.direct_object.description = command.indirect_args

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
        """ create flower as Object """
        name = command.direct_object_str
        if not name:
            self.tell('You must give the object a name.')
            return
        class_name = 'Object'
        if command.preposition == Preposition.AS and command.indirect_object_str:
            class_name = command.indirect_object_str
        cls = globals().get(class_name)
        if not cls:
            self.tell('I couldn\'t find {class_name}.'.format(class_name=class_name))
            return
        # create object
        obj = cls(name=name)
        obj.move(self)
        self.tell('You created {name}.'.format(name=name))
