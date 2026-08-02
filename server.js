#!/usr/bin/env node

import { createHmac, timingSafeEqual } from "node:crypto";
import { createServer } from "node:http";
import dotenv from "dotenv";
import express from "express";
import nunjucks from "nunjucks";
import { WebSocketServer } from "ws";
import { Broker, CLOSED } from "./src/broker.js";
import { getLogger, setupLogging } from "./src/logger.js";

// Configure logging before importing modules that use it at load time
setupLogging({ mode: "console" });
dotenv.config();

const { World } = await import("./src/core/world.js");
const { Player } = await import("./src/core/player.js");

const logger = getLogger("monkamoo.web");

const world = new World({ path: "world.json" });
await world.load();
logger.info("World loaded successfully");

const SECRET_KEY = process.env.SECRET_KEY || "JGS123#";
const SESSION_COOKIE = "monkamoo_session";

const app = express();
nunjucks.configure("templates", { autoescape: true, express: app });
app.use("/static", express.static("static"));
app.use(express.urlencoded({ extended: false }));

const broker = new Broker();

class SocketOutput {
  constructor(playerName) {
    this.playerName = playerName;
  }

  write(message) {
    broker.publish(this.playerName, message).catch((error) => logger.exception(error, "Failed to publish message"));
  }

  flush() {}
}

// --- signed session cookie helpers (replaces Quart's signed cookie session) ---

function sign(value) {
  return createHmac("sha256", SECRET_KEY).update(value).digest("base64url");
}

function makeSessionCookie(playerName) {
  const payload = Buffer.from(playerName, "utf8").toString("base64url");
  return `${payload}.${sign(payload)}`;
}

function getPlayerName(cookieHeader) {
  if (!cookieHeader) {
    return null;
  }
  for (const part of cookieHeader.split(";")) {
    const [name, ...rest] = part.trim().split("=");
    if (name !== SESSION_COOKIE) {
      continue;
    }
    const token = decodeURIComponent(rest.join("="));
    const index = token.lastIndexOf(".");
    if (index === -1) {
      return null;
    }
    const payload = token.slice(0, index);
    const signature = Buffer.from(token.slice(index + 1));
    const expected = Buffer.from(sign(payload));
    if (signature.length !== expected.length || !timingSafeEqual(signature, expected)) {
      logger.warning("Session cookie signature mismatch");
      return null;
    }
    return Buffer.from(payload, "base64url").toString("utf8") || null;
  }
  return null;
}

// --- routes ---

app.get("/", (req, res) => {
  const playerName = getPlayerName(req.headers.cookie);
  if (!playerName) {
    res.redirect("/login");
    return;
  }
  res.render("session.html", { player_name: playerName });
});

app.get("/login", (_req, res) => {
  res.render("login.html", {});
});

app.post("/login", (req, res) => {
  let playerName = req.body.player_name;
  if (playerName) {
    playerName = playerName.toLowerCase();
  }
  if (!playerName) {
    res.redirect("/login");
    return;
  }
  logger.info("Player login: %s", playerName);
  let player = world.findPlayer(playerName);
  if (!player) {
    player = new Player({ name: playerName });
    world.addPlayer(player);
    logger.info("New player created: %s", playerName);
  }
  player.stdout = new SocketOutput(playerName);
  res.cookie(SESSION_COOKIE, makeSessionCookie(playerName), { httpOnly: true, sameSite: "lax" });
  res.redirect("/");
});

app.get("/logout", (req, res) => {
  const playerName = getPlayerName(req.headers.cookie);
  res.clearCookie(SESSION_COOKIE);
  if (playerName) {
    logger.info("Player logout: %s", playerName);
  }
  res.redirect("/");
});

// --- websocket ---

const httpServer = createServer(app);
const wss = new WebSocketServer({ noServer: true });

httpServer.on("upgrade", (req, socket, head) => {
  const { pathname } = new URL(req.url, "http://localhost");
  if (pathname !== "/ws") {
    socket.destroy();
    return;
  }
  const playerName = getPlayerName(req.headers.cookie);
  if (!playerName) {
    logger.warning("WebSocket connection attempt without player_name");
    socket.write("HTTP/1.1 401 Unauthorized\r\n\r\n");
    socket.destroy();
    return;
  }
  wss.handleUpgrade(req, socket, head, (ws) => {
    wss.emit("connection", ws, req, playerName);
  });
});

wss.on("connection", (ws, _req, playerName) => {
  logger.info("WebSocket connection established for player: %s", playerName);
  let player = world.findPlayer(playerName);
  if (!player) {
    player = new Player({ name: playerName });
    world.addPlayer(player);
    logger.info("New player created: %s", playerName);
  }
  // (Re)bind output on every connection so players still receive messages
  // after a server restart, when login didn't run in this process.
  player.stdout = new SocketOutput(playerName);

  const queue = broker.subscribe(playerName);
  (async () => {
    while (true) {
      const message = await queue.get();
      if (message === CLOSED) {
        break;
      }
      ws.send(message);
    }
  })().catch((error) => logger.exception(error, "WebSocket send loop error for player %s", playerName));

  ws.on("message", (data) => {
    const message = data.toString();
    if (!message) {
      return; // keepalive ping from the client
    }
    logger.debug("WebSocket message from %s: %s", playerName, message);
    world.parseCommand(player, message);
  });

  ws.on("close", () => {
    broker.unsubscribe(playerName, queue);
    logger.info("WebSocket connection closed for player: %s", playerName);
  });

  ws.on("error", (error) => logger.exception(error, "WebSocket error for player %s", playerName));
});

const port = Number(process.env.PORT || 5432);
httpServer.listen(port, () => {
  logger.info("Server starting on port %d...", port);
});
