from ..utils import join_strings
from .base import Base
from .player import Player


class Room(Base):
    """Represents a room containing players and objects, with exits to other rooms."""

    def __init__(self, **kwargs):
        self.exits = {}
        super().__init__(**kwargs)

    def json_dictionary(self):
        return dict(super().json_dictionary(), exits=self.exits)

    def find_exit(self, direction):
        for exit in self.exits:
            if exit.lower() == direction.lower():
                return self.exits[exit]
        return None

    def announce(self, player, message, exclude_player=False):
        for obj in self:
            if exclude_player and obj is player:
                continue
            obj.tell(message)

    def on_enter(self, player, _direction=None):
        if not isinstance(player, Player):
            return
        self.announce(player, f"{player.name} enters the room.", exclude_player=True)
        self.look(player)

    def on_exit(self, player, direction=None):
        if not isinstance(player, Player):
            return
        message = f"{player.name} exits {direction}." if direction else f"{player.name} exits the room."
        self.announce(player, message, exclude_player=True)

    def say(self, command):
        player = command.player
        message = command.args_str
        if player and message:
            self.announce(player, f'{player.name} says, "{message}"')

    def emote(self, command):
        player = command.player
        message = command.args_str
        if message:
            self.announce(player, f"{player.name} {message}")

    def look(self, player):
        lines = []
        # show name and description
        if self.name:
            lines.append(f"*** {self.name} ***")
        lines.append(self.description or "You see nothing here.")
        # show exits
        if self.exits:
            directions = self.exits.keys()
            lines.append("You can go {directions}.".format(directions=join_strings(directions, "or")))
        # show other players
        players = [p.name for p in self.players if p != player]
        if players:
            lines.append(
                "{players} {are} here.".format(
                    players=join_strings(players, "and"),
                    are=len(players) > 1 and "are" or "is",
                ),
            )
        # show room contents
        things = [o.name for o in self.things]
        if things:
            lines.append("There is {names} here.".format(names=join_strings(things, "and")))
        player.tell("\n".join(lines))

    def go(self, command):
        player = command.player
        direction = command.direct_object_str
        room_id = self.find_exit(direction)
        if room_id is None:
            player.tell("You can't go that way.")
            return
        room = self.world.contents[room_id]
        player.move(room, direction)

    def dig(self, command):
        player = command.player
        direction = command.direct_object_str
        back = command.indirect_object_str or "back"
        if not direction:
            player.tell("You must give a direction.")
            return
        if self.find_exit(direction) is not None:
            player.tell("That direction already exists.")
            return
        room = Room(exits={back: self.id})
        self.world.add(room)
        self.exits[direction] = room.id
        self.announce(
            player,
            f"{player.name} created a room to the {direction}.",
            exclude_player=False,
        )
