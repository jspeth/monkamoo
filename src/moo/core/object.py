from .base import Base
from ..line_parser import Preposition

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

    def give(self, command):
        player = command.player
        recipient = command.preposition == Preposition.AT and command.indirect_object
        if not recipient:
            return player.tell('To whom?')
        self.move(recipient)
        player.tell('You give {name} to {recipient}.'.format(name=self.name, recipient=recipient.name))
        self.room.announce(player, '{player} gives {name} to {recipient}.'.format(player=player.name, name=self.name, recipient=recipient.name), exclude_player=True)
