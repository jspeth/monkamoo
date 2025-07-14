from ..line_parser import Preposition
from ..logging_config import get_logger
from ..utils import join_strings
from .base import Base

# Get logger for this module
logger = get_logger("monkamoo.player")


class Player(Base):
    """Represents a participant in the MOO."""

    def __init__(self, **kwargs):
        self.stdout = None
        super().__init__(**kwargs)

    def do_load(self, command):
        self.world.load()

    def do_save(self, command):
        self.world.save()

    def tell(self, message):
        if self.stdout:
            self.stdout.write(message + "\n")
            self.stdout.flush()
        logger.debug("Player %s told: %s", self.name, message)

    def jump(self, command):
        room_name = command.direct_object_str
        logger.info("Player %s attempting to jump to room: %s", self.name, room_name)
        room = self.world.find_room(room_name)
        if not room:
            logger.debug("Player %s tried to jump to non-existent room: %s", self.name, room_name)
            self.tell(f"I couldn't find {room_name}.")
            return
        self.move(room)
        logger.info("Player %s jumped to room: %s", self.name, room_name)

    def look(self, command):
        obj = command.direct_object
        # special case "look at object"
        if command.preposition == Preposition.AT and command.indirect_object:
            obj = command.indirect_object
        # check if the object was named but not found
        if not obj and command.direct_object_str:
            self.tell(f"There is no {command.direct_object_str} here.")
            return
        # look at the object
        if not obj or obj == self.location:
            self.location.look(self)
        elif obj == self:
            self.tell(self.description or "You see nothing special.")
            thing_names = [o.name for o in self.things]
            if thing_names:
                self.tell("You have {names}.".format(names=join_strings(thing_names, "and")))
        else:
            self.tell(obj.description or "You see nothing special.")

    def do_name(self, command):
        if not command.direct_object or command.preposition != Preposition.AS or not command.indirect_args:
            self.tell("I didn't understand that.")
            return
        command.direct_object.name = command.indirect_args

    def do_describe(self, command):
        if not command.direct_object or command.preposition != Preposition.AS or not command.indirect_args:
            self.tell("I didn't understand that.")
            return
        command.direct_object.description = command.indirect_args

    def whisper(self, command):
        parts = command.args_str.split(" ", 1)
        if len(parts) < 2:
            self.tell("What do you want to tell them?")
            return
        name, message = parts
        logger.info("Player %s whispering to %s: %s", self.name, name, message)
        player = self.world.find_player(name)
        if player and message:
            if hasattr(player, "handle_whisper"):
                player.handle_whisper(message)
            else:
                player.tell(f'{self.name} whispers, "{message}"', "whisper")
        else:
            logger.debug("Player %s tried to whisper to non-existent player: %s", self.name, name)

    def find(self, command):
        name = command.direct_object_str
        player = self.world.find_player(name)
        if player and player.location:
            if player.location.name:
                self.tell(f"{player.name} is in {player.location.name}.")
            else:
                self.tell(f"{player.name} is in a room with no name.")
                self.tell("It looks like:\n{description}".format(description=player.location.description or "?"))
        else:
            self.tell(f"I couldn't find {name}.")

    def create(self, command):
        """create flower as Object"""
        name = command.direct_object_str
        if not name:
            self.tell("You must give the object a name.")
            return
        class_name = "Object"
        if command.preposition == Preposition.AS and command.indirect_object_str:
            class_name = command.indirect_object_str
        logger.info("Player %s creating object: %s as %s", self.name, name, class_name)
        cls = globals().get(class_name)
        if not cls:
            logger.debug("Player %s tried to create object with non-existent class: %s", self.name, class_name)
            self.tell(f"I couldn't find {class_name}.")
            return
        # create object
        obj = cls(name=name)
        obj.move(self)
        self.tell(f"You created {name}.")
        logger.info("Player %s successfully created object: %s", self.name, name)

    def bot(self, command):
        name = command.direct_object_str
        if not name:
            self.tell("You must provide a player name.")
            return
        logger.info("Player %s creating bot: %s", self.name, name)
        player = self.world.find_player(name)
        if not player:
            from .aiplayer import AIPlayer

            player = AIPlayer(name=name)
            player.location = self.location
            self.world.add_player(player)
            logger.info("New AI player created: %s", name)
        else:
            player.move(self.location)
            logger.info("Existing player moved to current location: %s", name)

    def help(self, command):
        # TODO: help should be dynamically generated and use verb search path
        help = """
Commands:
player [name]: select an existing player or create a new one
look [object]: show a description of the object or the current room
go [direction]: change rooms by moving player in direction
jump [room name]: go directly to a named room
dig [direction]: create a new room, adding direction to the current room
name [object] as [name]: set an object's name
describe [object] as [description]: set an object's description
say [message]: say a message to all players in the current room
emote [expression]: express an action, feeling, or just about anything
whisper [player] [message]: send a private message directly to another player
find [player]: find player by name, gives their room name or description
take [object]: pick up an object by name
drop [object]: drop an object you are carrying
give [object] to [player]: give an object to another player
create [name] as [class]: create a new object

Shortcuts:
" -- say (example: `"Hi there.` becomes `say Hi there.`)
: -- emote (example: `:waves.` becomes `emote waves.`)
@ -- whisper (example: `@jim Psst...` becomes `whisper jim Psst...`)
# -- jump (example: `#attic` becomes `jump attic`)
"""
        self.tell(help)
