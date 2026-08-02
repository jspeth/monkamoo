import { randomUUID } from "node:crypto";
import { registerClass } from "./classRegistry.js";

export class Base {
  /** The base class of all MOO objects. */

  static typeName = "Base";

  constructor(props = {}) {
    this.id = randomUUID();
    this.world = null;
    this.name = null;
    this.description = null;
    this.location = null;
    this.contents = {};
    Object.assign(this, props);
  }

  // Type flags instead of instanceof checks so base.js never has to import
  // its own subclasses (Python used function-local imports for this).
  get isRoom() {
    return false;
  }

  get isPlayer() {
    return false;
  }

  toJSON() {
    return {
      type: this.constructor.typeName,
      id: this.id,
      name: this.name,
      description: this.description,
      location: this.location?.id || null,
    };
  }

  [Symbol.iterator]() {
    return Object.values(this.contents)[Symbol.iterator]();
  }

  add(obj) {
    if (!obj || obj.id === undefined) {
      throw new Error("object must have an id");
    }
    this.world.add(obj);
    this.contents[obj.id] = obj;
  }

  remove(obj) {
    if (!obj || obj.id === undefined) {
      throw new Error("object must have an id");
    }
    delete this.contents[obj.id];
  }

  move(location, direction = null) {
    if (!location.accept(this)) {
      return false;
    }
    if (this.location) {
      this.location.onExit(this, direction);
      this.location.remove(this);
    }
    this.location = location;
    if (this.location) {
      this.location.add(this);
      this.location.onEnter(this, direction);
    }
    return true;
  }

  accept(_obj) {
    return true;
  }

  onEnter(_obj, _direction = null) {}

  onExit(_obj, _direction = null) {}

  get room() {
    if (this.isRoom) {
      return this;
    }
    if (this.location) {
      return this.location.room;
    }
    return null;
  }

  get player() {
    if (this.isPlayer) {
      return this;
    }
    if (this.location) {
      return this.location.player;
    }
    return null;
  }

  get rooms() {
    return [...this].filter((obj) => obj.isRoom);
  }

  get players() {
    return [...this].filter((obj) => obj.isPlayer);
  }

  get things() {
    return [...this].filter((obj) => !obj.isPlayer);
  }

  findRoom(name) {
    // Allow using `@Player` to find the room the player is in
    if (name.startsWith("@")) {
      const player = this.findPlayer(name.replace(/^@+/, ""));
      if (player) {
        return player.location;
      }
    }
    for (const room of this.rooms) {
      if (room.name && room.name.toLowerCase() === name.toLowerCase()) {
        return room;
      }
    }
    return null;
  }

  findPlayer(name) {
    for (const player of this.players) {
      if (player.name && player.name.toLowerCase() === name.toLowerCase()) {
        return player;
      }
    }
    return null;
  }

  findThing(name) {
    for (const obj of this.things) {
      if (obj.name && obj.name.toLowerCase() === name.toLowerCase()) {
        return obj;
      }
    }
    return null;
  }

  getFunction(verb) {
    for (const key of [verb, `do_${verb}`]) {
      // Never dispatch to JS object plumbing (constructor, toString, __proto__, ...).
      if (key in Object.prototype) {
        continue;
      }
      const method = this[key];
      if (typeof method === "function") {
        return method.bind(this);
      }
    }
    return null;
  }

  tell(_message = null, _type = null) {}

  timer(interval, fn, args = []) {
    setTimeout(() => fn(...args), interval * 1000);
  }
}
registerClass("Base", Base);
