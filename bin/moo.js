#!/usr/bin/env node

import { parseArgs } from "node:util";
import dotenv from "dotenv";
import { getLogger, setupLogging } from "../src/logger.js";

const { values: args } = parseArgs({
  options: {
    interact: { type: "boolean", short: "i", default: false },
    server: { type: "boolean", short: "s", default: false },
  },
  strict: false,
});

// Console logging for the REPL and telnet server; file logging for the
// interactive shell so log lines don't mix with game output.
setupLogging({ mode: args.interact || args.server ? "console" : "file" });
dotenv.config();

const { World } = await import("../src/core/world.js");
const { MonkaMOOServer } = await import("../src/telnetServer.js");
const { Shell } = await import("../src/shell.js");
const { interact } = await import("../src/interact.js");

const logger = getLogger("monkamoo.main");

async function main() {
  const world = new World({ path: "world.json" });
  await world.load();
  logger.info("World loaded successfully");

  if (args.interact) {
    logger.info("Starting interactive JavaScript REPL");
    const context = { world };
    for (const player of world.players) {
      context[player.name.toLowerCase()] = player;
    }
    await interact({
      input: process.stdin,
      output: process.stdout,
      context,
      terminal: Boolean(process.stdin.isTTY),
    });
    process.exit(0);
  } else if (args.server) {
    logger.info("Starting telnet server");
    const mooServer = new MonkaMOOServer(world);
    await mooServer.run();
  } else {
    logger.info("Starting interactive shell");
    const me = world.findPlayer("Jim");
    const shell = new Shell(world, { player: me, input: process.stdin, output: process.stdout });
    await shell.cmdloop();
    process.exit(0);
  }
}

main().catch((error) => {
  logger.exception(error, "Fatal error");
  process.exit(1);
});
