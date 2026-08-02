import { registerClass } from "./classRegistry.js";
import { Thing } from "./thing.js";

export class Ball extends Thing {
  /** A simple ball. */

  static typeName = "Ball";

  bounce(command) {
    this.room.announce(command.player, "The ball bounces up and down.");
  }

  roll(command) {
    this.room.announce(command.player, "The ball rolls away.");
  }

  throw(command) {
    this.room.announce(command.player, "The ball flies in the air.");
    this.timer(5, () => {
      this.room.announce(command.player, "The ball falls to the ground, bounces a few times, then settles.");
    });
  }
}
registerClass("Ball", Ball);
