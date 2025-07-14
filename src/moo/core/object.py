from ..line_parser import Preposition
from .base import Base


class Object(Base):
    """Represents a thing that can be picked up and put down."""

    def take(self, command):
        player = command.player
        self.move(player)
        player.tell(f"You take {self.name}.")
        self.room.announce(
            player, f"{player.name} takes {self.name}.", exclude_player=True,
        )

    def drop(self, command):
        player = command.player
        self.move(player.room)
        player.tell(f"You drop {self.name}.")
        self.room.announce(
            player, f"{player.name} drops {self.name}.", exclude_player=True,
        )

    def give(self, command):
        player = command.player
        recipient = command.preposition == Preposition.AT and command.indirect_object
        if not recipient:
            return player.tell("To whom?")
        self.move(recipient)
        player.tell(f"You give {self.name} to {recipient.name}.")
        self.room.announce(
            player,
            f"{player.name} gives {self.name} to {recipient.name}.",
            exclude_player=True,
        )
        return None
