import { Preposition } from "../lineParser.js";
import { Base } from "./base.js";
import { registerClass } from "./classRegistry.js";

export class Thing extends Base {
  /**
   * Represents a thing that can be picked up and put down.
   * Named `Object` in the Python implementation and in world.json; renamed
   * here because `Object` collides with the JS built-in. The registry still
   * maps the "Object" type name to this class.
   */

  static typeName = "Object";

  take(command) {
    const player = command.player;
    this.move(player);
    player.tell(`You take ${this.name}.`);
    this.room.announce(player, `${player.name} takes ${this.name}.`, true);
  }

  drop(command) {
    const player = command.player;
    this.move(player.room);
    player.tell(`You drop ${this.name}.`);
    this.room.announce(player, `${player.name} drops ${this.name}.`, true);
  }

  give(command) {
    const player = command.player;
    const recipient = command.preposition === Preposition.AT ? command.indirectObject : null;
    if (!recipient) {
      player.tell("To whom?");
      return;
    }
    this.move(recipient);
    player.tell(`You give ${this.name} to ${recipient.name}.`);
    this.room.announce(player, `${player.name} gives ${this.name} to ${recipient.name}.`, true);
  }
}
registerClass("Object", Thing);
