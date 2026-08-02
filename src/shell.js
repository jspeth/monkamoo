import { Player } from "./core/player.js";
import { interact } from "./interact.js";
import { getLogger } from "./logger.js";

const logger = getLogger("monkamoo.shell");

/**
 * Buffers a readable stream into lines that can be awaited one at a time.
 * Can be paused so another consumer (the interact REPL) can take over the
 * stream, then resumed.
 */
export class LineReader {
  constructor(stream) {
    this.stream = stream;
    this.buffer = "";
    this.lines = [];
    this.resolvers = [];
    this.ended = false;
    this.onData = (chunk) => {
      this.buffer += chunk.toString();
      let index = this.buffer.indexOf("\n");
      while (index !== -1) {
        const line = this.buffer.slice(0, index).replace(/\r$/, "");
        this.buffer = this.buffer.slice(index + 1);
        this.pushLine(line);
        index = this.buffer.indexOf("\n");
      }
    };
    this.onEnd = () => {
      this.ended = true;
      while (this.resolvers.length) {
        this.resolvers.shift()(null);
      }
    };
    stream.on("data", this.onData);
    stream.on("end", this.onEnd);
    stream.on("error", this.onEnd);
  }

  pushLine(line) {
    const resolve = this.resolvers.shift();
    if (resolve) {
      resolve(line);
    } else {
      this.lines.push(line);
    }
  }

  /** Resolves with the next line, or null on end of input. */
  readLine() {
    if (this.lines.length) {
      return Promise.resolve(this.lines.shift());
    }
    if (this.ended) {
      return Promise.resolve(null);
    }
    return new Promise((resolve) => this.resolvers.push(resolve));
  }

  pause() {
    this.stream.removeListener("data", this.onData);
  }

  resume() {
    this.stream.on("data", this.onData);
    this.stream.resume?.();
  }
}

export class Shell {
  /** A command shell for processing user input and executing MOO commands. */

  static intro = "Welcome to MonkaMOO!";

  constructor(world, { player = null, input, output }) {
    this.world = world;
    this.input = input;
    this.output = output;
    this.reader = new LineReader(input);
    this.player = null;
    this.setPlayer(player);
    this.output.write(`${Shell.intro}\n`);
    logger.info("Shell initialized for world: %s", world.path);
  }

  setPlayer(player) {
    if (this.player) {
      this.player.stdout = null;
    }
    this.player = player;
    if (this.player) {
      this.player.stdout = this.output;
      logger.info("Shell player set to: %s", player.name);
    }
  }

  async cmdloop() {
    logger.info("Shell command loop started");
    while (true) {
      const line = await this.reader.readLine();
      if (line === null) {
        logger.info("Shell received EOF, exiting");
        break;
      }
      const trimmed = line.trim();
      if (trimmed === "quit" || trimmed === "exit") {
        logger.info("Shell received quit command");
        break;
      }
      await this.execCmd(trimmed);
    }
    logger.info("Shell command loop ended");
  }

  async execCmd(line) {
    const arg = line.split(" ").slice(1).join(" ");
    if (line.startsWith("interact")) {
      logger.debug("Shell executing interact command: %s", arg);
      return this.doInteract(arg);
    }
    if (line.startsWith("player")) {
      logger.debug("Shell executing player command: %s", arg);
      return this.doPlayer(arg);
    }
    logger.debug("Shell executing default command: %s", line);
    return this.default(line);
  }

  async default(line) {
    if (!this.player) {
      return this.doPlayer(null);
    }
    if (line) {
      logger.debug("Shell parsing command for player %s: %s", this.player.name, line);
      this.world.parseCommand(this.player, line);
    }
    return null;
  }

  async doInteract(_arg) {
    const context = { world: this.world };
    for (const player of this.world.players) {
      context[player.name.toLowerCase()] = player;
    }
    this.reader.pause();
    try {
      await interact({ input: this.input, output: this.output, context });
    } finally {
      this.reader.resume();
    }
  }

  async doPlayer(arg) {
    if (!arg) {
      this.output.write('Type "player [name]" to choose a player.\n');
      return;
    }
    let player = this.world.findPlayer(arg);
    if (!player) {
      player = new Player({ name: arg });
      this.world.addPlayer(player);
    }
    this.setPlayer(player);
    this.player.location.look(this.player);
  }
}
