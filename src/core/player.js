import { Preposition } from "../lineParser.js";
import { getLogger } from "../logger.js";
import { joinStrings } from "../utils.js";
import { Base } from "./base.js";
import { getClass, registerClass } from "./classRegistry.js";

const logger = getLogger("monkamoo.player");

const HELP_TEXT = `
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
" -- say (example: \`"Hi there.\` becomes \`say Hi there.\`)
: -- emote (example: \`:waves.\` becomes \`emote waves.\`)
@ -- whisper (example: \`@jim Psst...\` becomes \`whisper jim Psst...\`)
# -- jump (example: \`#attic\` becomes \`jump attic\`)
`;

export class Player extends Base {
  /** Represents a participant in the MOO. */

  static typeName = "Player";

  constructor(props = {}) {
    super({ stdout: null, ...props });
  }

  get isPlayer() {
    return true;
  }

  do_load(_command) {
    this.world.load().catch((error) => logger.exception(error, "Failed to load world"));
  }

  do_save(_command) {
    this.world.save().catch((error) => logger.exception(error, "Failed to save world"));
  }

  tell(message, _type = null) {
    if (this.stdout) {
      this.stdout.write(`${message}\n`);
      this.stdout.flush?.();
    }
    logger.debug("Player %s told: %s", this.name, message);
  }

  jump(command) {
    const roomName = command.directObjectStr;
    logger.debug("Player %s attempting to jump to room: %s", this.name, roomName);
    const room = this.world.findRoom(roomName);
    if (!room) {
      logger.debug("Player %s tried to jump to non-existent room: %s", this.name, roomName);
      this.tell(`I couldn't find ${roomName}.`);
      return;
    }
    this.move(room);
    logger.debug("Player %s jumped to room: %s", this.name, roomName);
  }

  look(command) {
    let obj = command.directObject;
    // special case "look at object"
    if (command.preposition === Preposition.AT && command.indirectObject) {
      obj = command.indirectObject;
    }
    // check if the object was named but not found
    if (!obj && command.directObjectStr) {
      this.tell(`There is no ${command.directObjectStr} here.`);
      return;
    }
    // look at the object
    if (!obj || obj === this.location) {
      this.location.look(this);
    } else if (obj === this) {
      this.tell(this.description || "You see nothing special.");
      const thingNames = this.things.map((o) => o.name);
      if (thingNames.length) {
        this.tell(`You have ${joinStrings(thingNames, "and")}.`);
      }
    } else {
      this.tell(obj.description || "You see nothing special.");
    }
  }

  do_name(command) {
    if (!command.directObject || command.preposition !== Preposition.AS || !command.indirectArgs) {
      this.tell("I didn't understand that.");
      return;
    }
    command.directObject.name = command.indirectArgs;
  }

  do_describe(command) {
    if (!command.directObject || command.preposition !== Preposition.AS || !command.indirectArgs) {
      this.tell("I didn't understand that.");
      return;
    }
    command.directObject.description = command.indirectArgs;
  }

  whisper(command) {
    const argsStr = command.argsStr || "";
    const index = argsStr.indexOf(" ");
    if (index === -1) {
      this.tell("What do you want to tell them?");
      return;
    }
    const name = argsStr.slice(0, index);
    const message = argsStr.slice(index + 1);
    logger.debug("Player %s whispering to %s: %s", this.name, name, message);
    const player = this.world.findPlayer(name);
    if (player && message) {
      if (typeof player.handleWhisper === "function") {
        player.handleWhisper(message);
      } else {
        player.tell(`${this.name} whispers, "${message}"`, "whisper");
      }
    } else {
      logger.debug("Player %s tried to whisper to non-existent player: %s", this.name, name);
    }
  }

  find(command) {
    const name = command.directObjectStr;
    const player = this.world.findPlayer(name);
    if (player?.location) {
      if (player.location.name) {
        this.tell(`${player.name} is in ${player.location.name}.`);
      } else {
        this.tell(`${player.name} is in a room with no name.`);
        this.tell(`It looks like:\n${player.location.description || "?"}`);
      }
    } else {
      this.tell(`I couldn't find ${name}.`);
    }
  }

  create(command) {
    /** create flower as Object */
    const name = command.directObjectStr;
    if (!name) {
      this.tell("You must give the object a name.");
      return;
    }
    let className = "Object";
    if (command.preposition === Preposition.AS && command.indirectObjectStr) {
      className = command.indirectObjectStr;
    }
    logger.debug("Player %s creating object: %s as %s", this.name, name, className);
    const cls = getClass(className);
    if (!cls) {
      logger.debug("Player %s tried to create object with non-existent class: %s", this.name, className);
      this.tell(`I couldn't find ${className}.`);
      return;
    }
    // create object
    const obj = new cls({ name });
    obj.move(this);
    this.tell(`You created ${name}.`);
    logger.debug("Player %s successfully created object: %s", this.name, name);
  }

  bot(command) {
    const name = command.directObjectStr;
    if (!name) {
      this.tell("You must provide a player name.");
      return;
    }
    logger.debug("Player %s creating bot: %s", this.name, name);
    let player = this.world.findPlayer(name);
    if (!player) {
      const AIPlayer = getClass("AIPlayer");
      player = new AIPlayer({ name });
      player.location = this.location;
      this.world.addPlayer(player);
      logger.debug("New AI player created: %s", name);
    } else {
      player.move(this.location);
      logger.debug("Existing player moved to current location: %s", name);
    }
  }

  help(_command) {
    // TODO: help should be dynamically generated and use verb search path
    this.tell(HELP_TEXT);
  }
}
registerClass("Player", Player);
