import repl from "node:repl";
import { getLogger } from "./logger.js";

const logger = getLogger("monkamoo.interpreter");

/**
 * Start a live JavaScript REPL with the world and players in scope
 * (the port of the Python interactive console). Resolves when the
 * REPL exits (.exit or Ctrl-D).
 */
export function interact({ input, output, context = {}, terminal = false } = {}) {
  logger.info("Starting interactive console");
  return new Promise((resolve) => {
    const server = repl.start({ prompt: ">>> ", input, output, terminal, useColors: terminal });
    Object.assign(server.context, context);
    server.on("exit", () => {
      logger.info("Interactive console exited");
      resolve();
    });
  });
}
