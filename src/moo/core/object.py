from .base import Base

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
