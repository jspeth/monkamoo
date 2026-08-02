import { joinStrings } from "../utils.js";
import { Base } from "./base.js";
import { registerClass } from "./classRegistry.js";

export class Room extends Base {
  /** Represents a room containing players and objects, with exits to other rooms. */

  static typeName = "Room";

  constructor(props = {}) {
    super({ exits: {}, ...props });
  }

  get isRoom() {
    return true;
  }

  toJSON() {
    return { ...super.toJSON(), exits: this.exits };
  }

  findExit(direction) {
    for (const exit of Object.keys(this.exits)) {
      if (exit.toLowerCase() === direction.toLowerCase()) {
        return this.exits[exit];
      }
    }
    return null;
  }

  announce(player, message, excludePlayer = false) {
    for (const obj of this) {
      if (excludePlayer && obj === player) {
        continue;
      }
      obj.tell(message);
    }
  }

  onEnter(player, _direction = null) {
    if (!player.isPlayer) {
      return;
    }
    this.announce(player, `${player.name} enters the room.`, true);
    this.look(player);
  }

  onExit(player, direction = null) {
    if (!player.isPlayer) {
      return;
    }
    const message = direction ? `${player.name} exits ${direction}.` : `${player.name} exits the room.`;
    this.announce(player, message, true);
  }

  say(command) {
    const player = command.player;
    const message = command.argsStr;
    if (player && message) {
      this.announce(player, `${player.name} says, "${message}"`);
    }
  }

  emote(command) {
    const player = command.player;
    const message = command.argsStr;
    if (message) {
      this.announce(player, `${player.name} ${message}`);
    }
  }

  look(player) {
    const lines = [];
    // show name and description
    if (this.name) {
      lines.push(`*** ${this.name} ***`);
    }
    lines.push(this.description || "You see nothing here.");
    // show exits
    const directions = Object.keys(this.exits);
    if (directions.length) {
      lines.push(`You can go ${joinStrings(directions, "or")}.`);
    }
    // show other players
    const players = this.players.filter((p) => p !== player).map((p) => p.name);
    if (players.length) {
      lines.push(`${joinStrings(players, "and")} ${players.length > 1 ? "are" : "is"} here.`);
    }
    // show room contents
    const things = this.things.map((o) => o.name);
    if (things.length) {
      lines.push(`There is ${joinStrings(things, "and")} here.`);
    }
    player.tell(lines.join("\n"));
  }

  go(command) {
    const player = command.player;
    const direction = command.directObjectStr;
    const roomId = this.findExit(direction);
    const room = roomId === null ? null : this.world.contents[roomId];
    if (!room) {
      player.tell("You can't go that way.");
      return;
    }
    player.move(room, direction);
  }

  dig(command) {
    const player = command.player;
    const direction = command.directObjectStr;
    const back = command.indirectObjectStr || "back";
    if (!direction) {
      player.tell("You must give a direction.");
      return;
    }
    if (this.findExit(direction) !== null) {
      player.tell("That direction already exists.");
      return;
    }
    const room = new Room({ exits: { [back]: this.id } });
    this.world.add(room);
    this.exits[direction] = room.id;
    this.announce(player, `${player.name} created a room to the ${direction}.`, false);
  }
}
registerClass("Room", Room);
