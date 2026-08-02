import fs from "node:fs";
import { format } from "node:util";

const LEVELS = { DEBUG: 10, INFO: 20, WARNING: 30, ERROR: 40, CRITICAL: 50 };

let minLevel = LEVELS[(process.env.LOG_LEVEL || "INFO").toUpperCase()] ?? LEVELS.INFO;
let writeLine = (line) => process.stderr.write(`${line}\n`);

function timestamp() {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return (
    `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ` +
    `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
  );
}

/**
 * Set up logging output. Mirrors the Python logging_config module:
 * mode "console" logs to stderr, mode "file" appends to log.txt (used by the
 * interactive shell so log lines don't mix with game output).
 */
export function setupLogging({ mode = "console", logLevel = null } = {}) {
  const level = (logLevel || process.env.LOG_LEVEL || "INFO").toUpperCase();
  minLevel = LEVELS[level] ?? LEVELS.INFO;
  if (mode === "file") {
    const stream = fs.createWriteStream("log.txt", { flags: "a" });
    writeLine = (line) => stream.write(`${line}\n`);
  } else {
    writeLine = (line) => process.stderr.write(`${line}\n`);
  }
}

export function getLogger(name = "monkamoo") {
  const log = (levelName, message, ...args) => {
    if (LEVELS[levelName] < minLevel) {
      return;
    }
    writeLine(`${timestamp()} - ${name} - ${levelName} - ${format(message, ...args)}`);
  };
  return {
    debug: (message, ...args) => log("DEBUG", message, ...args),
    info: (message, ...args) => log("INFO", message, ...args),
    warning: (message, ...args) => log("WARNING", message, ...args),
    error: (message, ...args) => log("ERROR", message, ...args),
    exception: (error, message, ...args) => {
      log("ERROR", message, ...args);
      log("ERROR", "%s", error?.stack || error);
    },
  };
}
