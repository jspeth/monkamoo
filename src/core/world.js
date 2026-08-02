import { Parser } from "../lineParser.js";
import { getLogger } from "../logger.js";
import { getStorageWithFallback } from "../storage/factory.js";
import { stripChars } from "../utils.js";
import { Base } from "./base.js";
import { getClass } from "./registry.js";
import { Room } from "./room.js";

const logger = getLogger("monkamoo.world");

export class World extends Base {
  /** The root container of all MOO objects. */

  static typeName = "World";

  static shortcuts = { '"': "say", ":": "emote", "@": "whisper", "#": "jump" };

  constructor(props = {}) {
    const { path = null, ...rest } = props;
    super(rest);
    this.path = path;
    this.storage = null;
    if (!Object.keys(this.contents).length) {
      const room = new Room({ id: "0", description: "This is the beginning of the world." });
      room.world = this;
      this.contents = { 0: room };
    }
  }

  toJSON() {
    return { contents: this.contents };
  }

  async getStorage() {
    if (!this.storage) {
      this.storage = await getStorageWithFallback({ worldPath: this.path || "world.json" });
    }
    return this.storage;
  }

  async load() {
    logger.info("Loading world using storage abstraction");
    const storage = await this.getStorage();
    const worldData = await storage.loadWorld();
    if (!worldData) {
      logger.warning("No world data found in storage");
      return;
    }
    const allContents = {};
    let loadedObjects = 0;
    for (const objectDict of Object.values(worldData.contents || {})) {
      // get object class
      const className = objectDict.type;
      const cls = getClass(className);
      if (!cls) {
        logger.error("Class not found: %s", className);
        continue;
      }
      delete objectDict.type;
      // create object, building contents map
      const obj = new cls(objectDict);
      if (obj.location) {
        allContents[obj.location] ??= {};
        allContents[obj.location][obj.id] = obj;
      }
      this.add(obj);
      loadedObjects += 1;
    }
    // update objects with their contents
    for (const [id, contents] of Object.entries(allContents)) {
      if (this.contents[id]) {
        this.contents[id].contents = contents;
      }
    }
    // replace location id with object
    for (const obj of Object.values(this.contents)) {
      if (obj.location && this.contents[obj.location]) {
        obj.location = this.contents[obj.location];
      }
    }
    logger.info("World loaded successfully: %d objects", loadedObjects);
  }

  async save() {
    logger.info("Saving world using storage abstraction");
    const storage = await this.getStorage();
    const success = await storage.saveWorld(this);
    if (success) {
      logger.info("World saved successfully");
    } else {
      logger.error("Failed to save world");
    }
  }

  add(obj) {
    if (!obj || obj.id === undefined) {
      throw new Error("object must have an id");
    }
    this.contents[obj.id] = obj;
    obj.world = this;
  }

  addPlayer(player) {
    logger.info("Adding player to world: %s", player.name);
    this.add(player);
    if (!player.location) {
      player.location = this.contents["0"];
    }
    player.location.contents[player.id] = player;
    logger.info("Player %s added to room: %s", player.name, player.location.id);
  }

  parseCommand(player, line) {
    logger.debug("Parsing command for player %s: %s", player.name, line);
    let input = line;
    for (const key of Object.keys(World.shortcuts)) {
      if (input.startsWith(key)) {
        input = `${World.shortcuts[key]} ${stripChars(input, `${key} `)}`;
        break;
      }
    }
    const command = Parser.parse(input);
    if (!command) {
      logger.debug("Command not understood: %s", input);
      player.tell("I didn't understand that.");
      return;
    }
    command.resolve(this, player);
    this.handleCommand(command);
  }

  handleCommand(command) {
    const func = this.findFunction(command);
    if (!func) {
      logger.debug("No function found for command: %s", command.verb);
      command.player.tell("I didn't understand that.");
      return;
    }
    logger.debug("Executing command: %s for player %s", command.verb, command.player.name);
    try {
      func(command);
    } catch (error) {
      // Python let these propagate (and kill the caller's task); contain them instead.
      logger.exception(error, "Error executing command %s for player %s", command.verb, command.player.name);
      command.player.tell("Something went wrong.");
    }
  }

  findFunction(command) {
    const searchPath = [command.player, command.player.room];
    if (command.directObject) {
      searchPath.push(command.directObject);
    }
    if (command.indirectObject) {
      searchPath.push(command.indirectObject);
    }
    for (const obj of searchPath) {
      if (!obj) {
        continue;
      }
      const method = obj.getFunction(command.verb);
      if (method) {
        return method;
      }
    }
    return null;
  }
}
